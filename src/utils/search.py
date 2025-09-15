"""
QuranBot - Surah Search Utility
================================

Fuzzy search functionality for finding Surahs by name or number.
Handles typos and partial matches for both Arabic and English names.

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from difflib import SequenceMatcher

from src.core.logger import logger


class SurahSearch:
    """
    Fuzzy search for Quran Surahs.
    
    Supports searching by:
    - Surah number (1-114)
    - Arabic name with typo tolerance
    - English name with typo tolerance
    - Partial name matching
    """
    
    def __init__(self) -> None:
        """
        Initialize the Surah search system by loading the mapper data.
        
        This method loads the comprehensive surah mapping data from the JSON file,
        which contains all 114 surahs with their Arabic names, English names,
        and translations. If the file is missing or corrupted, it gracefully
        falls back to empty data to prevent the bot from crashing.
        """
        try:
            # Construct path to the surah mapper JSON file
            # Navigate from src/utils/ to src/data/surah_mapper.json
            mapper_path: Path = Path(__file__).parent.parent / "data" / "surah_mapper.json"
            
            if not mapper_path.exists():
                # Log the missing file error with helpful debugging information
                logger.error_tree("Surah mapper file not found", FileNotFoundError("Missing surah_mapper.json"), [
                    ("Expected Path", str(mapper_path)),
                    ("Current Directory", str(Path.cwd()))
                ])
                # Create empty default data to prevent crashes
                # This allows the bot to continue operating without search functionality
                self.data = {"surahs": {}}
                self.surahs = {}
                return
            
            # Load the JSON data with UTF-8 encoding to support Arabic characters
            with open(mapper_path, 'r', encoding='utf-8') as f:
                self.data: Dict[str, Any] = json.load(f)
            
            # Extract the surahs dictionary from the loaded data
            # This contains all 114 surahs with their metadata
            self.surahs: Dict[str, Dict[str, str]] = self.data.get("surahs", {})
            
            logger.success(f"Loaded {len(self.surahs)} Surahs for search")
            
        except json.JSONDecodeError as e:
            logger.error_tree("Failed to parse surah mapper JSON", e, [
                ("File", str(mapper_path)),
                ("Error Position", f"Line {e.lineno}, Column {e.colno}" if hasattr(e, 'lineno') else "Unknown")
            ])
            self.data = {"surahs": {}}
            self.surahs = {}
            
        except Exception as e:
            logger.error_tree("Failed to initialize SurahSearch", e, [
                ("Type", type(e).__name__)
            ])
            self.data = {"surahs": {}}
            self.surahs = {}
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for Surahs matching the query.
        
        Args:
            query: Search query (number, Arabic name, or English name)
            limit: Maximum number of results to return
            
        Returns:
            List of matching Surahs with similarity scores
        """
        try:
            if not query:
                logger.tree("⚠️ Empty Search Query", [
                    ("Query", "Empty string"),
                    ("Action", "Returning empty results")
                ])
                return []
            
            query: str = query.strip()
            
            # Check if query is a numeric surah number (1-114)
            # This provides the fastest and most accurate search for numeric queries
            if query.isdigit():
                num: int = int(query)
                if 1 <= num <= 114:
                    if str(num) in self.surahs:
                        # Create a copy of the surah data and add search metadata
                        surah: Dict[str, Any] = self.surahs[str(num)].copy()
                        surah['number'] = num
                        surah['score'] = 1.0  # Perfect match for numeric queries
                        
                        logger.tree(f"🔍 Surah Found by Number", [
                            ("Query", query),
                            ("Surah", f"{num}. {surah.get('english', 'Unknown')}")
                        ])
                        
                        return [surah]
                    else:
                        logger.tree("⚠️ Surah Not in Database", [
                            ("Requested Number", str(num)),
                            ("Valid Range", "1-114"),
                            ("Action", "Returning empty results")
                        ])
                        return []
            
            # FUZZY SEARCH BY NAME
            # ====================
            # Perform intelligent fuzzy search across Arabic, English, and translation names
            # This handles typos, partial matches, and different naming conventions
            results: List[Dict[str, Any]] = []
            query_lower: str = query.lower()
            
            for num_str, surah_data in self.surahs.items():
                try:
                    num: int = int(num_str)
                    
                    # Calculate similarity scores using SequenceMatcher for each name type
                    # Arabic names are searched with original case to preserve authenticity
                    arabic_score: float = self._calculate_similarity(query, surah_data.get('arabic', ''))
                    # English and translation names are searched case-insensitively
                    english_score: float = self._calculate_similarity(query_lower, surah_data.get('english', '').lower())
                    translation_score: float = self._calculate_similarity(query_lower, surah_data.get('translation', '').lower())
                    
                    # Take the best similarity score from all three name types
                    # This ensures we catch matches regardless of which name field contains the query
                    best_score: float = max(arabic_score, english_score, translation_score)
                    
                    # PARTIAL MATCH BOOSTING
                    # ======================
                    # Boost scores for partial matches (query contained within names)
                    # This helps with incomplete searches and partial typing
                    if query in surah_data.get('arabic', ''):
                        best_score = max(best_score, 0.8)  # High boost for Arabic partial matches
                    if query_lower in surah_data.get('english', '').lower():
                        best_score = max(best_score, 0.8)  # High boost for English partial matches
                    if query_lower in surah_data.get('translation', '').lower():
                        best_score = max(best_score, 0.7)  # Medium boost for translation partial matches
                    
                    # Only include results above the minimum similarity threshold
                    # 0.3 threshold balances accuracy with recall
                    if best_score > 0.3:
                        result: Dict[str, Any] = surah_data.copy()
                        result['number'] = num
                        result['score'] = best_score
                        results.append(result)
                        
                except (ValueError, KeyError) as e:
                    logger.error_tree(f"Error processing surah {num_str}", e, [
                        ("Surah Number", num_str),
                        ("Query", query)
                    ])
                    continue
            
            # Sort results by similarity score (highest first) and return top matches
            # This ensures the most relevant results appear first in the search results
            results.sort(key=lambda x: x['score'], reverse=True)
            
            if results:
                logger.tree(f"🔍 Search Results", [
                    ("Query", query),
                    ("Results Found", str(len(results))),
                    ("Top Match", f"{results[0]['number']}. {results[0].get('english', 'Unknown')}")
                ])
            else:
                logger.tree("ℹ️ No Search Results", [
                    ("Query", query),
                    ("Results", "0 matches"),
                    ("Action", "Returning empty list")
                ])
            
            return results[:limit]
            
        except Exception as e:
            logger.error_tree("Search failed", e, [
                ("Query", query),
                ("Limit", str(limit))
            ])
            return []
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using SequenceMatcher.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            if not str1 or not str2:
                return 0.0
            return SequenceMatcher(None, str1, str2).ratio()
        except Exception as e:
            logger.error_tree("Similarity calculation failed", e, [
                ("String 1 Length", str(len(str1)) if str1 else "0"),
                ("String 2 Length", str(len(str2)) if str2 else "0")
            ])
            return 0.0
    
    def get_surah(self, number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific Surah by number.
        
        Args:
            number: Surah number (1-114)
            
        Returns:
            Surah data or None if not found
        """
        try:
            if not isinstance(number, int):
                logger.tree("⚠️ Invalid Number Type", [
                    ("Provided Type", type(number).__name__),
                    ("Expected Type", "int"),
                    ("Value", str(number))
                ])
                return None
                
            if 1 <= number <= 114:
                if str(number) in self.surahs:
                    surah: Dict[str, Any] = self.surahs[str(number)].copy()
                    surah['number'] = number
                    
                    logger.tree(f"📖 Retrieved Surah", [
                        ("Number", str(number)),
                        ("Name", surah.get('english', 'Unknown'))
                    ])
                    
                    return surah
                else:
                    logger.tree("⚠️ Surah Not Found", [
                        ("Number", str(number)),
                        ("Database", "Missing entry"),
                        ("Action", "Returning None")
                    ])
                    return None
            else:
                logger.tree("⚠️ Number Out of Range", [
                    ("Provided", str(number)),
                    ("Valid Range", "1-114"),
                    ("Action", "Returning None")
                ])
                return None
                
        except Exception as e:
            logger.error_tree("Failed to get surah", e, [
                ("Requested Number", str(number))
            ])
            return None
    
    def format_result(self, surah: Dict[str, Any]) -> str:
        """
        Format a Surah result for display.
        
        Args:
            surah: Surah data dictionary
            
        Returns:
            Formatted string for display
        """
        try:
            if not surah:
                return "❌ Invalid surah data"
            
            # Get values with defaults
            emoji: str = surah.get('emoji', '📖')
            number: int = surah.get('number', 0)
            english: str = surah.get('english', 'Unknown')
            arabic: str = surah.get('arabic', 'غير معروف')
            
            return f"{emoji} **{number}. {english}** - {arabic}"
            
        except Exception as e:
            logger.error_tree("Failed to format surah result", e, [
                ("Surah Number", str(surah.get('number', 'Unknown')))
            ])
            return "❌ Error formatting result"