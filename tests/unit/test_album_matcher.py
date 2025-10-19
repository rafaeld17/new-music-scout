"""
Unit tests for the album matching service.
"""
import pytest
from sqlmodel import SQLModel, create_engine, Session

from src.music_scout.models import Artist, Album, MusicItem, ContentType
from src.music_scout.services.album_matcher import AlbumMatcher


@pytest.fixture
def test_session():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_normalize_string(test_session):
    """Test string normalization."""
    matcher = AlbumMatcher(test_session)

    # Basic normalization
    assert matcher.normalize_string("The Album Title") == "album title"
    assert matcher.normalize_string("UPPERCASE") == "uppercase"

    # Punctuation removal
    assert matcher.normalize_string("Fear, Inoculum") == "fear inoculum"
    assert matcher.normalize_string("Album: The Story") == "album the story"

    # Special characters
    assert matcher.normalize_string("Album – Part 1") == "album - part 1"
    assert matcher.normalize_string("The — Story") == "- story"  # "The" removed, dash remains

    # Parentheses content removal (content inside is removed, not just parens)
    assert matcher.normalize_string("Album (Remastered)") == "album remastered"
    assert matcher.normalize_string("Album [Deluxe Edition]") == "album deluxe edition"


def test_similarity_score(test_session):
    """Test similarity scoring."""
    matcher = AlbumMatcher(test_session)

    # Exact match
    assert matcher.similarity_score("test", "test") == 1.0

    # Very similar
    score = matcher.similarity_score("closure continuation", "closure continuation")
    assert score == 1.0

    # Similar but not identical
    score = matcher.similarity_score("fear inoculum", "fear innoculum")
    assert score > 0.85

    # Different
    score = matcher.similarity_score("album one", "totally different")
    assert score < 0.5


def test_match_artist_exact(test_session):
    """Test exact artist matching."""
    # Create artist
    artist = Artist(name="Porcupine Tree", normalized_name="porcupine tree")
    test_session.add(artist)
    test_session.commit()

    # Test matching
    matcher = AlbumMatcher(test_session)
    matched = matcher.match_artist("Porcupine Tree", create_if_missing=False)

    assert matched is not None
    assert matched.name == "Porcupine Tree"


def test_match_artist_fuzzy(test_session):
    """Test fuzzy artist matching."""
    # Create artist
    artist = Artist(name="Porcupine Tree", normalized_name="porcupine tree")
    test_session.add(artist)
    test_session.commit()

    # Test fuzzy matching (with "The" prefix)
    matcher = AlbumMatcher(test_session)
    matched = matcher.match_artist("The Porcupine Tree", create_if_missing=False)

    assert matched is not None
    assert matched.name == "Porcupine Tree"


def test_match_artist_create_new(test_session):
    """Test creating a new artist when no match found."""
    matcher = AlbumMatcher(test_session)

    # Should create new artist
    artist = matcher.match_artist("Tool", create_if_missing=True)

    assert artist is not None
    assert artist.name == "Tool"
    assert artist.normalized_name == "tool"


def test_match_album_exact(test_session):
    """Test exact album matching."""
    # Create artist and album
    artist = Artist(name="Tool", normalized_name="tool")
    test_session.add(artist)
    test_session.commit()
    test_session.refresh(artist)

    album = Album(
        title="Fear Inoculum",
        normalized_title="fear inoculum",
        artist_id=artist.id,
        release_year=2019
    )
    test_session.add(album)
    test_session.commit()

    # Test matching
    matcher = AlbumMatcher(test_session)
    matched = matcher.match_album(
        "Fear Inoculum",
        "Tool",
        create_if_missing=False
    )

    assert matched is not None
    assert matched.title == "Fear Inoculum"
    assert matched.artist_id == artist.id


def test_match_album_fuzzy(test_session):
    """Test fuzzy album matching."""
    # Create artist and album
    artist = Artist(name="Porcupine Tree", normalized_name="porcupine tree")
    test_session.add(artist)
    test_session.commit()
    test_session.refresh(artist)

    album = Album(
        title="Closure/Continuation",
        normalized_title="closure continuation",
        artist_id=artist.id,
        release_year=2022
    )
    test_session.add(album)
    test_session.commit()

    # Test fuzzy matching (different punctuation)
    matcher = AlbumMatcher(test_session)
    matched = matcher.match_album(
        "Closure / Continuation",
        "Porcupine Tree",
        create_if_missing=False
    )

    assert matched is not None
    assert matched.title == "Closure/Continuation"


def test_match_album_with_year_bonus(test_session):
    """Test that matching year gives bonus score."""
    # Create artist and two albums with same name but different years
    artist = Artist(name="Opeth", normalized_name="opeth")
    test_session.add(artist)
    test_session.commit()
    test_session.refresh(artist)

    album1 = Album(
        title="Still Life",
        normalized_title="still life",
        artist_id=artist.id,
        release_year=1999
    )
    album2 = Album(
        title="Still Life Remastered",
        normalized_title="still life remastered",
        artist_id=artist.id,
        release_year=2015
    )
    test_session.add(album1)
    test_session.add(album2)
    test_session.commit()

    # Test matching with year
    matcher = AlbumMatcher(test_session)
    matched = matcher.match_album(
        "Still Life",
        "Opeth",
        create_if_missing=False,
        release_year=1999
    )

    assert matched is not None
    assert matched.release_year == 1999


def test_match_music_item_to_album(test_session):
    """Test matching MusicItem to Album."""
    from datetime import datetime
    from src.music_scout.models import Source, SourceType

    # Create source
    source = Source(
        name="Test Source",
        url="https://test.com",
        source_type=SourceType.RSS,
        credibility_weight=1.0
    )
    test_session.add(source)
    test_session.commit()
    test_session.refresh(source)

    # Create music item
    music_item = MusicItem(
        source_id=source.id,
        url="https://test.com/review",
        title="Tool - Fear Inoculum Review",
        published_date=datetime(2019, 8, 30),
        content_type=ContentType.REVIEW,
        raw_content="Great album!",
        artists=["Tool"],
        album="Fear Inoculum",
        review_score=9.0
    )
    test_session.add(music_item)
    test_session.commit()

    # Match to album
    matcher = AlbumMatcher(test_session)
    album = matcher.match_music_item_to_album(music_item, create_if_missing=True)

    assert album is not None
    assert album.title == "Fear Inoculum"
    assert album.release_year == 2019

    # Check that artist was created
    from sqlmodel import select
    statement = select(Artist).where(Artist.name == "Tool")
    artist = test_session.exec(statement).first()
    assert artist is not None
    assert album.artist_id == artist.id


def test_find_similar_albums(test_session):
    """Test finding similar albums."""
    # Create artists and albums
    artist1 = Artist(name="Tool", normalized_name="tool")
    test_session.add(artist1)
    test_session.commit()
    test_session.refresh(artist1)

    albums = [
        Album(title="Fear Inoculum", normalized_title="fear inoculum", artist_id=artist1.id),
        Album(title="Fear", normalized_title="fear", artist_id=artist1.id),
        Album(title="Inoculum", normalized_title="inoculum", artist_id=artist1.id),
    ]
    for album in albums:
        test_session.add(album)
    test_session.commit()

    # Find similar
    matcher = AlbumMatcher(test_session)
    similar = matcher.find_similar_albums("Fear Inoculum", "Tool", limit=3)

    assert len(similar) > 0
    # First result should be exact match
    assert similar[0][0].title == "Fear Inoculum"
    assert similar[0][1] >= 0.9  # High similarity score


def test_no_match_without_create(test_session):
    """Test that no match returns None when create_if_missing=False."""
    matcher = AlbumMatcher(test_session)

    # Should return None
    artist = matcher.match_artist("Nonexistent Artist", create_if_missing=False)
    assert artist is None

    album = matcher.match_album(
        "Nonexistent Album",
        "Nonexistent Artist",
        create_if_missing=False
    )
    assert album is None


def test_match_with_special_characters(test_session):
    """Test matching with various special characters."""
    # Create artist with special characters
    artist = Artist(name="Steven Wilson", normalized_name="steven wilson")
    test_session.add(artist)
    test_session.commit()
    test_session.refresh(artist)

    album = Album(
        title="Hand. Cannot. Erase.",
        normalized_title="hand cannot erase",
        artist_id=artist.id
    )
    test_session.add(album)
    test_session.commit()

    # Test matching with different punctuation
    matcher = AlbumMatcher(test_session)
    matched = matcher.match_album(
        "Hand Cannot Erase",
        "Steven Wilson",
        create_if_missing=False
    )

    assert matched is not None
    assert matched.title == "Hand. Cannot. Erase."
