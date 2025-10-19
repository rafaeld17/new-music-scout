"""
Ultimate Classic Rock scraper for album reviews.
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
from .base import BaseScraper
import logging

logger = logging.getLogger(__name__)


class UltimateClassicRockScraper(BaseScraper):
    """Scraper for Ultimate Classic Rock reviews."""

    def __init__(self):
        super().__init__(base_url='https://ultimateclassicrock.com')

    def get_review_list(self, limit: int = 50) -> List[str]:
        """
        Get list of review URLs from the album reviews category page.

        Args:
            limit: Maximum number of review URLs to return (default: 50)

        Returns:
            List of full review URLs
        """
        review_urls = []
        page = 1

        while len(review_urls) < limit:
            # Construct page URL
            if page == 1:
                page_url = f"{self.base_url}/category/album-reviews/"
            else:
                page_url = f"{self.base_url}/category/album-reviews/page/{page}/"

            logger.info(f"Fetching Ultimate Classic Rock reviews from page {page}")
            soup = self.fetch_page(page_url)

            if not soup:
                break

            # Find all review links (URLs containing "-review")
            found_on_page = 0
            for link in soup.find_all('a', href=re.compile(r'-review(?:s)?/')):
                href = link.get('href')
                if href and href.startswith('//'):
                    href = 'https:' + href
                elif href and not href.startswith('http'):
                    href = self.base_url + href

                # Skip category pages and pagination links
                if href and '/category/' not in href and '/page/' not in href and href not in review_urls:
                    review_urls.append(href)
                    found_on_page += 1

                if len(review_urls) >= limit:
                    break

            # If no new reviews found on this page, stop
            if found_on_page == 0:
                logger.info(f"No more reviews found on page {page}, stopping")
                break

            page += 1

            # Safety limit to avoid infinite loops
            if page > 50:
                logger.warning("Reached page limit of 50, stopping")
                break

        logger.info(f"Found {len(review_urls)} review URLs from Ultimate Classic Rock")
        return review_urls[:limit]

    def parse_review(self, url: str) -> Optional[Dict]:
        """
        Parse a single Ultimate Classic Rock review page.

        Args:
            url: Review page URL

        Returns:
            Dictionary with review data or None if parsing fails
        """
        soup = self.fetch_page(url)

        if not soup:
            return None

        try:
            # Extract title from h1
            title = "Unknown Title"
            artist = "Unknown Artist"
            album = "Unknown Album"

            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

                # Replace curly quotes with straight quotes for easier parsing
                title = title.replace('\u2018', "'").replace('\u2019', "'")  # Single curly quotes
                title = title.replace('\u201c', '"').replace('\u201d', '"')  # Double curly quotes

                # Parse title patterns:
                # "Artist - Album Review"
                # "Artist, 'Album': Review"
                # "Artist, 'Album': Album Review"

                # Try pattern: "Artist, 'Album': Review"
                match = re.search(r"^([^,]+),\s*['\"]([^'\"]+)['\"]:\s*(?:Album\s+)?Review", title, re.IGNORECASE)
                if match:
                    artist = match.group(1).strip()
                    album = match.group(2).strip()
                else:
                    # Try pattern: "Artist - Album Review"
                    match = re.search(r"^(.+?)\s*[-–—]\s*(.+?)\s*(?:Album\s+)?Review", title, re.IGNORECASE)
                    if match:
                        artist = match.group(1).strip()
                        album = match.group(2).strip()

            # Extract review score (if available)
            review_score = None
            review_score_raw = None

            # Ultimate Classic Rock doesn't always have numeric scores
            # Look for star ratings or score text
            score_elem = soup.find(text=re.compile(r'Rating:\s*\d+/\d+|\d+\s*out\s*of\s*\d+', re.IGNORECASE))
            if score_elem:
                match = re.search(r'(\d+)\s*(?:out\s*of|/)\s*(\d+)', score_elem, re.IGNORECASE)
                if match:
                    score_num = float(match.group(1))
                    score_denom = float(match.group(2))
                    review_score = (score_num / score_denom) * 10  # Normalize to 10-point scale
                    review_score_raw = f"{int(score_num)}/{int(score_denom)}"

            # Extract author
            author = None
            author_elem = soup.find(class_=re.compile(r'author|byline', re.IGNORECASE))
            if author_elem:
                author = author_elem.get_text(strip=True)
                # Clean up author name (remove "By" prefix, etc.)
                author = re.sub(r'^By\s+', '', author, flags=re.IGNORECASE)

            # Fallback: look for author in meta tags
            if not author:
                meta_author = soup.find('meta', attrs={'name': 'author'})
                if meta_author:
                    author = meta_author.get('content')

            # Extract publication date
            published_date = None

            # Try to find time element
            time_elem = soup.find('time')
            if time_elem:
                datetime_str = time_elem.get('datetime')
                if datetime_str:
                    try:
                        # Parse ISO format: 2025-10-14T12:00:00+00:00
                        published_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    except ValueError:
                        pass

            # Fallback: look for date in article meta
            if not published_date:
                date_elem = soup.find(class_=re.compile(r'date|publish', re.IGNORECASE))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # Try common date formats
                    for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d']:
                        try:
                            published_date = datetime.strptime(date_text, fmt)
                            break
                        except ValueError:
                            continue

            # Default to current date if not found
            if not published_date:
                published_date = datetime.now()

            # Extract review content (first few paragraphs)
            content_paragraphs = []
            article_body = soup.find(['article', 'div'], class_=re.compile(r'content|entry|body', re.IGNORECASE))

            if article_body:
                for p in article_body.find_all('p'):
                    text = p.get_text(strip=True)
                    if len(text) > 50:  # Skip short paragraphs
                        content_paragraphs.append(text)
                    if len(content_paragraphs) >= 3:
                        break

            # Fallback: get any paragraphs
            if not content_paragraphs:
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
            logger.error(f"Error parsing Ultimate Classic Rock review {url}: {e}")
            return None
