# coding: utf-8

"""
 SWB -- SkillCorner Batch
 Whoscored scraper reference module
"""

__version__ = "1.0"
__author__ = "Yannis Rachid"
__maintainer__ = "Yannis Rachid"
__email__ = "yannis.rachid6@gmail.com"
__date__ = "Feb 22th, 2025"
__status__ = "Development"  # Prototype, Development, Production

__all__ = ["WhoScored", "process_match_data", "get_matches_data", "preprocess_events_df"]

from .whoscored import WhoScored
from .scraper import process_match_data, get_matches_data, preprocess_events_df