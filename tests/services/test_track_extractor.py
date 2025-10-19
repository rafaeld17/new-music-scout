"""Tests for track name extraction."""

import pytest
from src.music_scout.services.track_extractor import TrackExtractor


class TestTrackExtractor:
    """Test track name extraction from titles."""

    @pytest.fixture
    def extractor(self):
        """Create a track extractor instance."""
        return TrackExtractor()

    def test_extract_single_with_quotes(self, extractor):
        """Test extracting single name with standard quotes."""
        title = "MEGADETH Unveil 'Tipping Point,' First Single & Video From Their 2026 Album"
        track = extractor.extract_track_name(title)
        assert track == "Tipping Point"

    def test_extract_single_with_curly_quotes(self, extractor):
        """Test extracting single name with curly quotes."""
        title = "ROB ZOMBIE Shares Music Video For First Single �Punks And Demons�"
        track = extractor.extract_track_name(title)
        assert track == "Punks And Demons"

    def test_extract_video_release(self, extractor):
        """Test extracting track from video release."""
        title = "TESTAMENT Releases Animated Video For �High Noon�, New Album Out Now"
        track = extractor.extract_track_name(title)
        assert track == "High Noon"

    def test_extract_premiere(self, extractor):
        """Test extracting track from premiere."""
        title = "BEHEMOTH Premieres Video For �Avgvr (The Dread Vvltvre)� From Album"
        track = extractor.extract_track_name(title)
        assert track == "Avgvr (The Dread Vvltvre)"

    def test_extract_lyric_video(self, extractor):
        """Test extracting track from lyric video."""
        title = "AEROSMITH & YUNGBLUD Share Lyric Video For Single �My Only Angel�"
        track = extractor.extract_track_name(title)
        assert track == "My Only Angel"

    def test_no_track_in_review(self, extractor):
        """Test that regular reviews don't extract false positives."""
        title = "Review: Opeth - The Last Will and Testament"
        track = extractor.extract_track_name(title)
        assert track is None

    def test_no_track_without_keywords(self, extractor):
        """Test that quoted text without track keywords is ignored."""
        title = "Interview with 'John Smith' about new album"
        track = extractor.extract_track_name(title)
        assert track is None

    def test_extract_multiple_tracks(self, extractor):
        """Test extracting multiple track names."""
        title = "Band releases videos for 'Track One' and 'Track Two'"
        tracks = extractor.extract_all_tracks(title)
        assert len(tracks) == 2
        assert "Track One" in tracks
        assert "Track Two" in tracks

    def test_real_world_examples(self, extractor):
        """Test with real examples from our database."""
        examples = [
            ("KREATOR Share Music Video For New Single �Seven Serpents�", "Seven Serpents"),
            ("SOULFLY Drop Music Video For New Single �Nihilist�", "Nihilist"),
            ("FIT FOR AN AUTOPSY Releases Music Video For �It Comes For You�", "It Comes For You"),
            ("OMNIUM GATHERUM Shares New Single �Walking Ghost Phase�", "Walking Ghost Phase"),
            ("ALTER BRIDGE Shares New Single 'What Lies Within'", "What Lies Within"),
        ]

        for title, expected_track in examples:
            track = extractor.extract_track_name(title)
            assert track == expected_track, f"Failed to extract '{expected_track}' from: {title}"

    def test_track_name_validation(self, extractor):
        """Test track name validation logic."""
        # Too short
        assert not extractor._is_valid_track_name("A")

        # Too long
        assert not extractor._is_valid_track_name("A" * 101)

        # Contains false positive keywords
        assert not extractor._is_valid_track_name("Featuring Special Guest")

        # Valid track names
        assert extractor._is_valid_track_name("High Noon")
        assert extractor._is_valid_track_name("The Dread Vvltvre")
