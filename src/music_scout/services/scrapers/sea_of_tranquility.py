"""
Sea of Tranquility scraper for album reviews.
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
from .base import BaseScraper
import logging

logger = logging.getLogger(__name__)


class SeaOfTranquilityScraper(BaseScraper):
    """Scraper for Sea of Tranquility reviews."""

    def __init__(self):
        super().__init__(base_url='https://www.seaoftranquility.org')

    def get_review_list(self, limit: int = 50) -> List[str]:
        """
        Get list of review URLs from the reviews page.

        Args:
            limit: Maximum number of review URLs to return (default: 50)

        Returns:
            List of full review URLs
        """
        reviews_url = f"{self.base_url}/reviews.php"
        soup = self.fetch_page(reviews_url)

        if not soup:
            return []

        review_urls = []

        # Find all links that match the review pattern
        for link in soup.find_all('a', href=re.compile(r'reviews\.php\?op=showcontent&id=\d+')):
            href = link.get('href')
            if href:
                # Make absolute URL
                if not href.startswith('http'):
                    href = f"{self.base_url}/{href}"
                review_urls.append(href)

                if len(review_urls) >= limit:
                    break

        logger.info(f"Found {len(review_urls)} review URLs from Sea of Tranquility")
        return review_urls

    def parse_review(self, url: str) -> Optional[Dict]:
        """
        Parse a single Sea of Tranquility review page.

        Args:
            url: Review page URL

        Returns:
            Dictionary with review data or None if parsing fails
        """
        soup = self.fetch_page(url)

        if not soup:
            return None

        try:
            # Extract review data from the page structure
            # Look for bold text containing artist:album pattern
            title = "Unknown Title"
            artist = "Unknown Artist"
            album = "Unknown Album"

            # Find all bold elements and look for one with colon pattern
            for bold in soup.find_all(['b', 'strong']):
                text = bold.get_text(strip=True)
                if ':' in text and len(text) > 5:  # Has colon and is long enough
                    title = text
                    parts = text.split(':', 1)
                    artist = parts[0].strip()
                    album = parts[1].strip()
                    break

            # Fallback to h1/h2 if not found in bold
            if title == "Unknown Title":
                title_elem = soup.find('h1') or soup.find('h2')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if ':' in title:
                        parts = title.split(':', 1)
                        artist = parts[0].strip()
                        album = parts[1].strip()
                    elif ' - ' in title:
                        parts = title.split(' - ', 1)
                        artist = parts[0].strip()
                        album = parts[1].strip()

            # Extract review score (star rating)
            review_score = None
            review_score_raw = None

            # Look for star images
            star_imgs = soup.find_all('img', src=re.compile(r'star_whole\.gif'))
            if star_imgs:
                star_count = len(star_imgs)
                review_score = float(star_count * 2)  # Convert to 10-point scale
                review_score_raw = f"{star_count}/5"

            # Extract author
            author = None
            # Look for author in various possible locations
            author_patterns = [
                re.compile(r'by\s+([A-Za-z\s]+)', re.IGNORECASE),
                re.compile(r'written\s+by\s+([A-Za-z\s]+)', re.IGNORECASE),
                re.compile(r'reviewed\s+by\s+([A-Za-z\s]+)', re.IGNORECASE)
            ]

            for pattern in author_patterns:
                for text in soup.stripped_strings:
                    match = pattern.search(text)
                    if match:
                        author = match.group(1).strip()
                        break
                if author:
                    break

            # Extract publication date
            published_date = None
            # Look for date patterns in the page text
            date_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?\s+\d{4}')

            for text in soup.stripped_strings:
                match = date_pattern.search(text)
                if match:
                    date_str = match.group(0)
                    # Clean up ordinal suffixes
                    date_str = re.sub(r'(\d)(st|nd|rd|th)', r'\1', date_str)
                    try:
                        published_date = datetime.strptime(date_str, '%B %d %Y')
                    except ValueError:
                        pass
                    break

            # Default to current date if not found
            if not published_date:
                published_date = datetime.now()

            # Extract review content (first few paragraphs)
            content_paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 50:  # Skip short paragraphs
                    content_paragraphs.append(text)
                if len(content_paragraphs) >= 3:
                    break

            content = '\n\n'.join(content_paragraphs) if content_paragraphs else ""

            return {
                'title': title,
                'url': url,
                'artist': artist,
                'album': album,
                'review_score': review_score,
                'review_score_raw': review_score_raw,
                'author': author,
                'published_date': published_date,
                'content': content
            }

        except Exception as e:
            logger.error(f"Error parsing Sea of Tranquility review {url}: {e}")
            return None
