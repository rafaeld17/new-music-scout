"""
Metal Temple scraper for album reviews.
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
from .base import BaseScraper
import logging

logger = logging.getLogger(__name__)


class MetalTempleScraper(BaseScraper):
    """Scraper for Metal Temple reviews."""

    def __init__(self):
        super().__init__(base_url='https://metal-temple.com')

    def get_review_list(self, limit: int = 50) -> List[str]:
        """
        Get list of review URLs from the reviews page.

        Args:
            limit: Maximum number of review URLs to return (default: 50)

        Returns:
            List of full review URLs
        """
        reviews_url = f"{self.base_url}/reviews/"
        soup = self.fetch_page(reviews_url)

        if not soup:
            return []

        review_urls = []

        # Find all review links
        # Metal Temple uses cards/tiles for reviews
        for link in soup.find_all('a', href=re.compile(r'/reviews/')):
            href = link.get('href')
            if href and href != '/reviews/':  # Skip the main reviews page link
                # Make absolute URL
                if not href.startswith('http'):
                    href = f"{self.base_url}{href}"

                # Avoid duplicates
                if href not in review_urls:
                    review_urls.append(href)

                if len(review_urls) >= limit:
                    break

        logger.info(f"Found {len(review_urls)} review URLs from Metal Temple")
        return review_urls

    def parse_review(self, url: str) -> Optional[Dict]:
        """
        Parse a single Metal Temple review page.

        Args:
            url: Review page URL

        Returns:
            Dictionary with review data or None if parsing fails
        """
        soup = self.fetch_page(url)

        if not soup:
            return None

        try:
            # Extract title
            title_elem = soup.find('h1') or soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

            # Extract artist and album
            # Metal Temple typically has format "Artist - Album"
            artist = "Unknown Artist"
            album = "Unknown Album"

            if ' - ' in title:
                parts = title.split(' - ', 1)
                artist = parts[0].strip()
                album = parts[1].strip()

            # Extract review score
            review_score = None
            review_score_raw = None

            # Look for rating elements (typically shown as X/10 or X/100)
            rating_patterns = [
                re.compile(r'(\d+(?:\.\d+)?)\s*/\s*10', re.IGNORECASE),
                re.compile(r'(\d+)\s*/\s*100', re.IGNORECASE),
                re.compile(r'rating:\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
            ]

            for pattern in rating_patterns:
                for text in soup.stripped_strings:
                    match = pattern.search(text)
                    if match:
                        score = float(match.group(1))
                        # Normalize to 10-point scale
                        if '/100' in text or score > 10:
                            review_score = score / 10
                        else:
                            review_score = score
                        review_score_raw = match.group(0)
                        break
                if review_score:
                    break

            # Extract author
            author = None
            author_elem = soup.find(class_=re.compile(r'author|byline', re.IGNORECASE))
            if author_elem:
                author = author_elem.get_text(strip=True)

            # Extract publication date
            published_date = None
            date_elem = soup.find('time') or soup.find(class_=re.compile(r'date|published', re.IGNORECASE))

            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # Try to parse date
                for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        published_date = datetime.strptime(date_text, fmt)
                        break
                    except ValueError:
                        continue

            # Default to current date if not found
            if not published_date:
                published_date = datetime.now()

            # Extract content
            content_paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 50:
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
            logger.error(f"Error parsing Metal Temple review {url}: {e}")
            return None
