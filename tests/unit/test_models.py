"""
Tests for database models.
"""
import pytest
from datetime import datetime, date
from src.music_scout.models import Source, MusicItem, Artist, Album, SourceType, ContentType


def test_source_model_creation():
    """Test Source model creation and validation."""
    source = Source(
        name="Test Source",
        url="https://example.com/feed/",
        source_type=SourceType.RSS,
        weight=1.5,
        enabled=True
    )

    assert source.name == "Test Source"
    assert source.url == "https://example.com/feed/"
    assert source.source_type == SourceType.RSS
    assert source.weight == 1.5
    assert source.enabled is True
    assert source.health_score == 1.0  # default value


def test_music_item_model_creation():
    """Test MusicItem model creation and validation."""
    published_date = datetime(2023, 1, 15, 10, 30, 0)

    music_item = MusicItem(
        source_id=1,
        url="https://example.com/review/test",
        title="Test Album - Review",
        published_date=published_date,
        content_type=ContentType.REVIEW,
        raw_content="This is a great album review.",
        artists=["Test Artist"],
        album="Test Album",
        review_score=8.5
    )

    assert music_item.source_id == 1
    assert music_item.url == "https://example.com/review/test"
    assert music_item.title == "Test Album - Review"
    assert music_item.published_date == published_date
    assert music_item.content_type == ContentType.REVIEW
    assert music_item.artists == ["Test Artist"]
    assert music_item.album == "Test Album"
    assert music_item.review_score == 8.5
    assert music_item.is_processed is False  # default value


def test_artist_model_creation():
    """Test Artist model creation and validation."""
    artist = Artist(
        name="Porcupine Tree",
        normalized_name="porcupine tree",
        genres=["progressive rock", "progressive metal"],
        country="United Kingdom",
        formed_year=1987
    )

    assert artist.name == "Porcupine Tree"
    assert artist.normalized_name == "porcupine tree"
    assert artist.genres == ["progressive rock", "progressive metal"]
    assert artist.country == "United Kingdom"
    assert artist.formed_year == 1987


def test_album_model_creation():
    """Test Album model creation and validation."""
    release_date = date(2022, 6, 24)

    album = Album(
        title="Closure/Continuation",
        normalized_title="closure continuation",
        artist_id=1,
        release_date=release_date,
        release_year=2022,
        album_type="album"
    )

    assert album.title == "Closure/Continuation"
    assert album.normalized_title == "closure continuation"
    assert album.artist_id == 1
    assert album.release_date == release_date
    assert album.release_year == 2022
    assert album.album_type == "album"


def test_content_type_enum():
    """Test ContentType enum values."""
    assert ContentType.REVIEW == "review"
    assert ContentType.NEWS == "news"
    assert ContentType.PREMIERE == "premiere"
    assert ContentType.INTERVIEW == "interview"
    assert ContentType.BEST_OF == "best_of"
    assert ContentType.ALBUM_OF_DAY == "album_of_day"


def test_source_type_enum():
    """Test SourceType enum values."""
    assert SourceType.RSS == "rss"
    assert SourceType.HTML == "html"
    assert SourceType.API == "api"