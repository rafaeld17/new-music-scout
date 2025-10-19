"""
Tests for HTML scraping service.
"""
import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from src.music_scout.services.html_scraper import HTMLScraper, get_html_scraper


class TestHTMLScraper:
    """Test HTML scraping functionality."""

    @pytest.fixture
    def scraper(self):
        """Create a scraper instance for testing."""
        return HTMLScraper(timeout=5)

    def test_extract_tracklist_from_text_numbered(self, scraper):
        """Test extracting numbered tracklist."""
        text = """
        This is a great album review.

        Tracklist:
        1. Opening Track
        2. Second Song (4:32)
        3. Third Track - 5:21
        4. Final Song

        Overall a solid release.
        """

        tracks = scraper._extract_tracklist_from_text(text)

        assert len(tracks) == 4
        assert tracks[0] == "Opening Track"
        assert tracks[1] == "Second Song"
        assert tracks[2] == "Third Track"
        assert tracks[3] == "Final Song"

    def test_extract_tracklist_different_formats(self, scraper):
        """Test different tracklist formats."""
        # Format with parentheses
        text1 = """
        Track Listing:
        1) First Track
        2) Second Track
        """
        tracks1 = scraper._extract_tracklist_from_text(text1)
        assert len(tracks1) == 2
        assert "First Track" in tracks1

        # All caps
        text2 = """
        TRACKLIST:
        1. Track One
        2. Track Two
        """
        tracks2 = scraper._extract_tracklist_from_text(text2)
        assert len(tracks2) == 2

        # No colon
        text3 = """
        Tracklisting
        1. Song One
        2. Song Two
        """
        tracks3 = scraper._extract_tracklist_from_text(text3)
        assert len(tracks3) == 2

    def test_extract_tracklist_no_tracks(self, scraper):
        """Test when no tracklist is found."""
        text = """
        This is just a review with no tracklist section.
        It mentions some songs but doesn't list them formally.
        """

        tracks = scraper._extract_tracklist_from_text(text)
        assert len(tracks) == 0

    def test_extract_tracklist_with_duration_times(self, scraper):
        """Test extracting tracks with various duration formats."""
        text = """
        Tracklist:
        1. Track One (4:23)
        2. Track Two - 3:45
        3. Track Three (5:12)
        4. Track Four
        """

        tracks = scraper._extract_tracklist_from_text(text)

        assert len(tracks) == 4
        # Duration times should be stripped
        assert "(4:23)" not in tracks[0]
        assert "- 3:45" not in tracks[1]
        assert tracks[3] == "Track Four"

    @patch('requests.Session.get')
    def test_scrape_page_prog_report(self, mock_get, scraper):
        """Test scraping The Prog Report page."""
        html_content = """
        <html>
            <div class="entry-content">
                <p>This is a review of the album.</p>
                Tracklist:
                1. First Song
                2. Second Song
                <p>It's a great album!</p>
            </div>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper.scrape_page('https://progreport.com/review/album')

        assert result is not None
        assert 'tracks' in result
        assert 'full_text' in result
        assert len(result['tracks']) == 2
        assert 'First Song' in result['tracks']

    @patch('requests.Session.get')
    def test_scrape_page_sonic_perspectives(self, mock_get, scraper):
        """Test scraping Sonic Perspectives page."""
        html_content = """
        <html>
            <div class="entry-content">
                <p>Album review content here.</p>
                Track Listing:
                1. Track Alpha
                2. Track Beta
                3. Track Gamma
            </div>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper.scrape_page('https://sonicperspectives.com/albums/review')

        assert result is not None
        assert len(result['tracks']) == 3
        assert 'Track Alpha' in result['tracks']

    @patch('requests.Session.get')
    def test_scrape_page_request_error(self, mock_get, scraper):
        """Test handling of request errors."""
        mock_get.side_effect = Exception("Connection error")

        result = scraper.scrape_page('https://example.com/page')

        assert result is None

    def test_get_html_scraper_singleton(self):
        """Test that get_html_scraper returns the same instance."""
        scraper1 = get_html_scraper()
        scraper2 = get_html_scraper()

        assert scraper1 is scraper2
