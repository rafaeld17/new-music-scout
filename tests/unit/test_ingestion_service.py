"""
Tests for IngestionService.
"""
import pytest
from datetime import datetime
from src.music_scout.models import ContentType
from src.music_scout.services import IngestionService


def test_clean_html(ingestion_service):
    """Test HTML cleaning functionality."""
    html_content = """
    <div>
        <h1>Album Review</h1>
        <p>This is a <strong>great</strong> album with <em>amazing</em> tracks.</p>
        <script>alert('test');</script>
        <style>body { color: red; }</style>
    </div>
    """

    clean_text = ingestion_service._clean_html(html_content)

    assert "Album Review" in clean_text
    assert "great" in clean_text
    assert "amazing" in clean_text
    assert "<h1>" not in clean_text
    assert "<strong>" not in clean_text
    assert "alert('test')" not in clean_text
    assert "body { color: red; }" not in clean_text


def test_classify_content_type(ingestion_service):
    """Test content type classification."""
    # Test review classification
    review_title = "Porcupine Tree - Closure/Continuation Review"
    assert ingestion_service._classify_content_type(review_title, "") == ContentType.REVIEW

    rating_title = "Album Rating: 8.5/10"
    assert ingestion_service._classify_content_type(rating_title, "") == ContentType.REVIEW

    # Test interview classification
    interview_title = "Steven Wilson Talks About New Album"
    assert ingestion_service._classify_content_type(interview_title, "") == ContentType.INTERVIEW

    # Test premiere classification
    premiere_title = "Band Releases New Single"
    assert ingestion_service._classify_content_type(premiere_title, "") == ContentType.PREMIERE

    debut_title = "New Song Debuts on Radio"
    assert ingestion_service._classify_content_type(debut_title, "") == ContentType.PREMIERE

    # Test album of the day classification
    aotd_title = "Album of the Day: Tool - Fear Inoculum"
    assert ingestion_service._classify_content_type(aotd_title, "") == ContentType.ALBUM_OF_DAY

    # Test best of classification
    best_of_title = "Best Albums of 2023"
    assert ingestion_service._classify_content_type(best_of_title, "") == ContentType.BEST_OF

    # Test default (news) classification
    news_title = "Band Announces Tour Dates"
    assert ingestion_service._classify_content_type(news_title, "") == ContentType.NEWS


def test_extract_music_metadata(ingestion_service):
    """Test extraction of artist and album metadata from titles."""
    # Test "Artist - Album Review" format
    title1 = "Porcupine Tree - Closure/Continuation Review"
    artists1, album1 = ingestion_service._extract_music_metadata(title1, "")
    assert "Porcupine Tree" in artists1
    assert album1 == "Closure/Continuation"

    # Test "Album by Artist" format
    title2 = "Fear Inoculum by Tool - Album Review"
    artists2, album2 = ingestion_service._extract_music_metadata(title2, "")
    assert "Tool" in artists2
    assert album2 == "Fear Inoculum"

    # Test title with quotes
    title3 = '"The Dark Side of the Moon" by Pink Floyd Review'
    artists3, album3 = ingestion_service._extract_music_metadata(title3, "")
    assert "Pink Floyd" in artists3
    assert album3 == "The Dark Side of the Moon"

    # Test title without clear pattern
    title4 = "New Progressive Rock Album Announcement"
    artists4, album4 = ingestion_service._extract_music_metadata(title4, "")
    assert len(artists4) == 0 or not artists4[0]  # Should not extract false positives
    assert album4 is None


def test_create_music_item_from_rss(ingestion_service, sample_source, sample_rss_entry):
    """Test creating MusicItem from RSS entry."""
    music_item = ingestion_service._create_music_item_from_rss(sample_source, sample_rss_entry)

    assert music_item is not None
    assert music_item.source_id == sample_source.id
    assert music_item.url == sample_rss_entry.link
    assert music_item.title == sample_rss_entry.title
    assert music_item.author == sample_rss_entry.author
    assert music_item.content_type == ContentType.REVIEW  # Based on title
    assert "Porcupine Tree" in music_item.artists
    assert music_item.album == "Closure/Continuation"
    assert music_item.is_processed is False


def test_get_existing_item(ingestion_service, test_session, sample_source):
    """Test checking for existing items."""
    from src.music_scout.models import MusicItem

    # Create an existing item
    existing_item = MusicItem(
        source_id=sample_source.id,
        url="https://example.com/existing",
        title="Existing Item",
        published_date=datetime.utcnow(),
        content_type=ContentType.NEWS,
        raw_content="Test content"
    )
    test_session.add(existing_item)
    test_session.commit()

    # Test finding existing item
    found_item = ingestion_service._get_existing_item("https://example.com/existing")
    assert found_item is not None
    assert found_item.title == "Existing Item"

    # Test not finding non-existent item
    not_found = ingestion_service._get_existing_item("https://example.com/not-existing")
    assert not_found is None


@pytest.mark.parametrize("title,expected_artists,expected_album", [
    ("Tool - Fear Inoculum Review", ["Tool"], "Fear Inoculum"),
    ("Steven Wilson - The Raven That Refused to Sing Rating", ["Steven Wilson"], "The Raven That Refused to Sing"),
    ("Interview: Mikael Akerfeldt discusses Opeth", [], None),  # Interview, no album
    ("Best Progressive Albums of 2023", [], None),  # List article
    ("Haken – Vector Album Review", ["Haken"], "Vector"),  # Different dash character
    ("'Lateralus' by Tool - 20th Anniversary Review", ["Tool"], "Lateralus"),  # Quotes
])
def test_extract_music_metadata_parametrized(ingestion_service, title, expected_artists, expected_album):
    """Parametrized test for music metadata extraction."""
    artists, album = ingestion_service._extract_music_metadata(title, "")

    if expected_artists:
        assert len(artists) > 0
        assert expected_artists[0] in artists
    else:
        assert len(artists) == 0 or not artists[0]

    assert album == expected_album