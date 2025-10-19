"""
Tests for SourceManager service.
"""
import pytest
from src.music_scout.models import Source, SourceType


def test_create_default_sources(source_manager):
    """Test creating default sources."""
    sources = source_manager.create_default_sources()

    assert len(sources) >= 2  # At least Prog Report and Sonic Perspectives

    # Check that specific sources were created
    source_names = [s.name for s in sources]
    assert "The Prog Report" in source_names
    assert "Sonic Perspectives" in source_names


def test_create_default_sources_idempotent(source_manager):
    """Test that creating default sources twice doesn't create duplicates."""
    sources1 = source_manager.create_default_sources()
    sources2 = source_manager.create_default_sources()

    assert len(sources2) == 0  # No new sources created on second call


def test_get_source_by_name(source_manager):
    """Test getting source by name."""
    # Create default sources first
    source_manager.create_default_sources()

    source = source_manager.get_source_by_name("The Prog Report")
    assert source is not None
    assert source.name == "The Prog Report"
    assert source.source_type == SourceType.RSS

    # Test non-existent source
    non_existent = source_manager.get_source_by_name("Non-existent Source")
    assert non_existent is None


def test_get_enabled_sources(source_manager, test_session):
    """Test getting enabled sources."""
    # Create a disabled source
    disabled_source = Source(
        name="Disabled Source",
        url="https://disabled.com/feed/",
        source_type=SourceType.RSS,
        enabled=False
    )
    test_session.add(disabled_source)

    # Create an enabled source
    enabled_source = Source(
        name="Enabled Source",
        url="https://enabled.com/feed/",
        source_type=SourceType.RSS,
        enabled=True
    )
    test_session.add(enabled_source)
    test_session.commit()

    enabled_sources = source_manager.get_enabled_sources()
    source_names = [s.name for s in enabled_sources]

    assert "Enabled Source" in source_names
    assert "Disabled Source" not in source_names


def test_get_rss_sources(source_manager, test_session):
    """Test getting RSS sources."""
    # Create RSS source
    rss_source = Source(
        name="RSS Source",
        url="https://rss.com/feed/",
        source_type=SourceType.RSS,
        enabled=True
    )
    test_session.add(rss_source)

    # Create HTML source
    html_source = Source(
        name="HTML Source",
        url="https://html.com/",
        source_type=SourceType.HTML,
        enabled=True
    )
    test_session.add(html_source)
    test_session.commit()

    rss_sources = source_manager.get_rss_sources()
    source_names = [s.name for s in rss_sources]

    assert "RSS Source" in source_names
    assert "HTML Source" not in source_names


def test_update_source_health(source_manager, sample_source):
    """Test updating source health score."""
    original_health = sample_source.health_score

    # Update health score
    source_manager.update_source_health(sample_source.id, 0.8)

    # Refresh the source from database
    source_manager.session.refresh(sample_source)
    assert sample_source.health_score == 0.8

    # Test clamping to valid range
    source_manager.update_source_health(sample_source.id, 1.5)  # > 1.0
    source_manager.session.refresh(sample_source)
    assert sample_source.health_score == 1.0

    source_manager.update_source_health(sample_source.id, -0.5)  # < 0.0
    source_manager.session.refresh(sample_source)
    assert sample_source.health_score == 0.0