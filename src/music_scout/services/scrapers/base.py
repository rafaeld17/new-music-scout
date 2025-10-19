"""
Base scraper class for web scraping music review sites.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for web scrapers."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    @abstractmethod
    def get_review_list(self, limit: int = 50) -> List[str]:
        """
        Get list of review URLs.

        Args:
            limit: Maximum number of review URLs to return

        Returns:
            List of review URLs
        """
        pass

    @abstractmethod
    def parse_review(self, url: str) -> Optional[Dict]:
        """
        Parse a single review page.

        Args:
            url: Review page URL

        Returns:
            Dictionary with review data:
            {
                'title': str,
                'url': str,
                'artist': str,
                'album': str,
                'review_score': float,
                'review_score_raw': str,
                'author': str,
                'published_date': datetime,
                'content': str
            }
        """
        pass

    def scrape_reviews(self, limit: int = 50) -> List[Dict]:
        """
        Scrape multiple reviews.

        Args:
            limit: Maximum number of reviews to scrape

        Returns:
            List of parsed review dictionaries
        """
        review_urls = self.get_review_list(limit=limit)
        reviews = []

        for url in review_urls:
            try:
                review_data = self.parse_review(url)
                if review_data:
                    reviews.append(review_data)
            except Exception as e:
                logger.error(f"Error parsing review {url}: {e}")
                continue

        return reviews

    def close(self):
        """Close the session."""
        self.session.close()
