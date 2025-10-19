"""
Web scrapers for music review sites without RSS feeds.
"""
from .base import BaseScraper
from .sea_of_tranquility import SeaOfTranquilityScraper
from .metal_temple import MetalTempleScraper
from .ultimate_classic_rock import UltimateClassicRockScraper

__all__ = [
    'BaseScraper',
    'SeaOfTranquilityScraper',
    'MetalTempleScraper',
    'UltimateClassicRockScraper',
]
