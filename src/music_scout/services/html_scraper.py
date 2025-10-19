"""
HTML scraping service for extracting track listings and detailed content from review pages.
"""
import re
from typing import Optional, List, Dict
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from ..core.logging import logger


class HTMLScraper:
    """Scrape HTML content from music review pages to extract track listings."""

    def __init__(self, timeout: int = 10):
        """
        Initialize the HTML scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_page(self, url: str) -> Optional[Dict[str, any]]:
        """
        Scrape a review page and extract content.

        Args:
            url: URL of the review page

        Returns:
            Dictionary with extracted content or None if scraping fails
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Determine source based on URL
            domain = urlparse(url).netloc

            if 'progreport' in domain:
                return self._scrape_prog_report(soup, url)
            elif 'sonicperspectives' in domain:
                return self._scrape_sonic_perspectives(soup, url)
            else:
                logger.warning(f"Unknown source for URL: {url}")
                return None

        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None

    def _scrape_prog_report(self, soup: BeautifulSoup, url: str) -> Dict[str, any]:
        """Extract content from The Prog Report reviews."""
        result = {
            'url': url,
            'full_text': None,
            'tracks': []
        }

        # Get main content
        content_div = soup.find('div', class_='entry-content')
        if content_div:
            result['full_text'] = content_div.get_text(separator='\n', strip=True)

            # Try to extract from HTML lists first
            tracks = self._extract_tracklist_from_html(content_div)

            # Fall back to text-based extraction if no HTML list found
            if not tracks:
                tracks = self._extract_tracklist_from_text(result['full_text'])

            result['tracks'] = tracks

        return result

    def _scrape_sonic_perspectives(self, soup: BeautifulSoup, url: str) -> Dict[str, any]:
        """Extract content from Sonic Perspectives reviews."""
        result = {
            'url': url,
            'full_text': None,
            'tracks': []
        }

        # Get main content
        content_div = soup.find('div', class_='entry-content') or soup.find('article')
        if content_div:
            result['full_text'] = content_div.get_text(separator='\n', strip=True)

            # Try to extract from HTML lists first (Sonic Perspectives uses <ol> for tracklists)
            tracks = self._extract_tracklist_from_html(content_div)

            # Fall back to text-based extraction if no HTML list found
            if not tracks:
                tracks = self._extract_tracklist_from_text(result['full_text'])

            result['tracks'] = tracks

        return result

    def _extract_tracklist_from_html(self, content_div: BeautifulSoup) -> List[str]:
        """
        Extract track listings from HTML lists (ol/ul elements).

        Args:
            content_div: BeautifulSoup object containing the review content

        Returns:
            List of track names
        """
        tracks = []

        # Look for headings that might indicate a tracklist
        # Common patterns: "Track-list:", "Tracklist:", "Track Listing:", etc.
        headings = content_div.find_all(['h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', 'p'])

        for heading in headings:
            heading_text = heading.get_text().lower()

            # Check if this heading mentions tracklist/track listing
            if any(keyword in heading_text for keyword in ['track-list', 'tracklist', 'track listing']):
                # Look for the next ol or ul element (could be sibling or within next few elements)
                next_list = None

                # Check immediate next sibling
                next_sibling = heading.find_next_sibling(['ol', 'ul'])
                if next_sibling:
                    next_list = next_sibling
                else:
                    # Check within the next few elements
                    parent = heading.parent
                    if parent:
                        next_list = parent.find_next(['ol', 'ul'])

                if next_list:
                    # Extract track names from list items
                    list_items = next_list.find_all('li', recursive=False)
                    for li in list_items:
                        track_text = li.get_text(strip=True)
                        if track_text and len(track_text) > 1:
                            # Filter out common false positives (ads, links, etc.)
                            # Skip if it contains currency symbols or "ebook" (ads)
                            if any(x in track_text.lower() for x in ['$', '€', '£', 'ebook', 'buy now', 'purchase', 'available at']):
                                continue

                            # Skip if it looks like a URL or email
                            if 'http' in track_text.lower() or '@' in track_text or 'www.' in track_text.lower():
                                continue

                            # Skip if it's too long (likely a description or paragraph, not a track name)
                            if len(track_text) > 100:
                                continue

                            # Clean up track name (remove timestamps, etc.)
                            track_text = re.sub(r'\s*\([\d:]+\)\s*$', '', track_text)
                            track_text = re.sub(r'\s*-\s*[\d:]+\s*$', '', track_text)
                            track_text = re.sub(r'\s+[\d:]+\s*$', '', track_text)
                            tracks.append(track_text)

                    # If we found tracks, stop looking
                    if tracks:
                        break

        return tracks

    def _extract_tracklist_from_text(self, text: str) -> List[str]:
        """
        Extract track listings from review text.

        Args:
            text: Full review text

        Returns:
            List of track names
        """
        tracks = []

        # Look for tracklist section in text
        # More flexible pattern that allows whitespace and handles different formats
        tracklist_section_pattern = r'(?:Tracklist|Track\s*Listing|TRACKLIST)[:\s]*(.{5,500}?)(?:\n\n|\Z)'

        match = re.search(tracklist_section_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            tracklist_text = match.group(1)

            # Extract individual tracks
            # Pattern matches: "1. Track Name" or "1 Track Name" or "1) Track Name"
            track_lines = re.findall(
                r'^\s*\d+[.)\s]+(.+?)$',
                tracklist_text,
                re.MULTILINE
            )

            for track in track_lines:
                track = track.strip()
                if track and len(track) > 1:  # Filter out empty or single-char matches
                    # Remove common suffixes like duration times
                    track = re.sub(r'\s*\([\d:]+\)\s*$', '', track)  # (4:32)
                    track = re.sub(r'\s*-\s*[\d:]+\s*$', '', track)   # - 4:32
                    track = re.sub(r'\s+[\d:]+\s*$', '', track)        # 4:32 at end
                    tracks.append(track)

        return tracks


# Global scraper instance
_scraper_instance: Optional[HTMLScraper] = None


def get_html_scraper() -> HTMLScraper:
    """Get or create the global HTML scraper instance."""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = HTMLScraper()
    return _scraper_instance
