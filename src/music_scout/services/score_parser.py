"""
Review score parsing and normalization service.
"""
import re
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ParsedScore:
    """Represents a parsed review score."""
    raw_score: str
    normalized_score: float  # 0-10 scale
    confidence: float       # 0-1 confidence in extraction
    format_type: str        # "decimal", "fraction", "stars", "letter", "text"
    sub_scores: Dict[str, float] = None


class ScoreParser:
    """Service for parsing and normalizing review scores from different sources."""

    def __init__(self):
        # Sonic Perspectives patterns
        self.sonic_patterns = [
            # Overall score pattern: "8.8 out of 10" or "Overall: 8.8"
            (r'(?:overall|score):\s*(\d+\.?\d*)\s*(?:out of|/)?\s*(?:10)?', 'decimal'),
            # Sub-category patterns: "Songwriting: 8/10"
            (r'(?:songwriting|musicianship|originality|production):\s*(\d+)(?:/10)?', 'subcategory'),
            # Direct decimal score
            (r'(\d+\.\d+)\s*out of 10', 'decimal'),
        ]

        # The Prog Report patterns (to be implemented)
        self.prog_report_patterns = [
            # Common review score patterns
            (r'(\d+)/10', 'fraction'),
            (r'(\d+)/5', 'fraction'),
            (r'Rating:\s*(\d+\.?\d*)', 'decimal'),
        ]

        # Universal patterns
        self.universal_patterns = [
            # Star ratings: ★★★★☆ or 4/5 stars
            (r'([1-5])/5\s*stars?', 'fraction'),
            (r'★{1,5}', 'stars'),
            # Letter grades: Must be preceded by "grade:", "rating:", or similar context
            (r'(?:grade|rating|score):\s*([A-F][+-]?)\b', 'letter'),
            # Text ratings - must be preceded by rating context
            (r'(?:rating|score):\s*(excellent|great|good|average|poor|terrible)\b', 'text'),
            # Percentage - must be explicitly a score/rating
            (r'(?:score|rating):\s*(\d+)%', 'percentage'),
        ]

    def parse_score(self, content: str, source_name: str) -> Optional[ParsedScore]:
        """Parse review score from content based on source."""
        if not content:
            return None

        content_lower = content.lower()

        # Try source-specific patterns first
        if 'sonic perspectives' in source_name.lower():
            result = self._parse_sonic_perspectives(content_lower)
            if result:
                return result
        elif 'prog report' in source_name.lower():
            result = self._parse_prog_report(content_lower)
            if result:
                return result

        # Fall back to universal patterns
        return self._parse_universal(content_lower)

    def _parse_sonic_perspectives(self, content: str) -> Optional[ParsedScore]:
        """Parse Sonic Perspectives specific scoring format."""
        # Look for overall score with more specific patterns
        patterns = [
            # Overall score: X.X out of 10 (most specific)
            (r'(?:overall\s*score|score).*?(\d+\.\d+)\s*out\s*of\s*10', 'decimal', 0.95),
            # Just X.X out of 10 in context
            (r'(\d+\.\d+)\s*out\s*of\s*10', 'decimal', 0.9),
            # Score followed by rating text
            (r'score.*?(\d+\.\d+).*?(?:excellent|good|average)', 'decimal', 0.85),
        ]

        for pattern, format_type, confidence in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                if 0 <= score <= 10:  # Valid score range
                    return ParsedScore(
                        raw_score=match.group(0),
                        normalized_score=score,
                        confidence=confidence,
                        format_type=format_type
                    )

        # Look for sub-category scores and calculate average
        sub_scores = {}
        patterns = [
            (r'songwriting:\s*(\d+)(?:/10)?', 'songwriting'),
            (r'musicianship:\s*(\d+)(?:/10)?', 'musicianship'),
            (r'originality:\s*(\d+)(?:/10)?', 'originality'),
            (r'production:\s*(\d+)(?:/10)?', 'production'),
        ]

        for pattern, category in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                sub_scores[category] = float(match.group(1))

        if sub_scores and len(sub_scores) >= 2:
            # Calculate average of available sub-scores
            avg_score = sum(sub_scores.values()) / len(sub_scores)
            return ParsedScore(
                raw_score=f"Average of {len(sub_scores)} categories",
                normalized_score=avg_score,
                confidence=0.8,
                format_type="subcategory",
                sub_scores=sub_scores
            )

        return None

    def _parse_prog_report(self, content: str) -> Optional[ParsedScore]:
        """Parse The Prog Report specific scoring format."""
        # The Prog Report patterns (to be refined based on actual content)
        for pattern, format_type in self.prog_report_patterns:
            match = re.search(pattern, content)
            if match:
                score = self._normalize_score(match.group(1), format_type)
                if score is not None:
                    return ParsedScore(
                        raw_score=match.group(0),
                        normalized_score=score,
                        confidence=0.8,
                        format_type=format_type
                    )
        return None

    def _parse_universal(self, content: str) -> Optional[ParsedScore]:
        """Parse common scoring patterns."""
        for pattern, format_type in self.universal_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                score = self._normalize_score(match.group(1), format_type)
                if score is not None:
                    return ParsedScore(
                        raw_score=match.group(0),
                        normalized_score=score,
                        confidence=0.6,
                        format_type=format_type
                    )
        return None

    def _normalize_score(self, raw_value: str, format_type: str) -> Optional[float]:
        """Normalize different score formats to 0-10 scale."""
        try:
            if format_type == "decimal":
                return float(raw_value)

            elif format_type == "fraction":
                # Handle X/Y format
                if '/' in raw_value:
                    num, denom = raw_value.split('/')
                    score = (float(num) / float(denom)) * 10
                    return min(score, 10.0)
                else:
                    return float(raw_value)

            elif format_type == "stars":
                # Count star characters
                star_count = raw_value.count('★')
                return (star_count / 5.0) * 10

            elif format_type == "letter":
                # Convert letter grades to numeric
                grade_map = {
                    'A+': 10.0, 'A': 9.0, 'A-': 8.5,
                    'B+': 8.0, 'B': 7.0, 'B-': 6.5,
                    'C+': 6.0, 'C': 5.0, 'C-': 4.5,
                    'D+': 4.0, 'D': 3.0, 'D-': 2.5,
                    'F': 1.0
                }
                return grade_map.get(raw_value.upper())

            elif format_type == "text":
                # Convert text ratings to numeric
                text_map = {
                    'excellent': 9.0, 'great': 8.0, 'good': 7.0,
                    'average': 5.0, 'poor': 3.0, 'terrible': 1.0
                }
                return text_map.get(raw_value.lower())

            elif format_type == "percentage":
                # Convert percentage to 10-point scale
                return (float(raw_value) / 100.0) * 10

        except (ValueError, ZeroDivisionError):
            return None

        return None

    def get_confidence_reason(self, parsed_score: ParsedScore) -> str:
        """Get human-readable explanation of confidence level."""
        if parsed_score.confidence >= 0.9:
            return "High confidence - exact score format match"
        elif parsed_score.confidence >= 0.8:
            return "Good confidence - recognized format"
        elif parsed_score.confidence >= 0.6:
            return "Medium confidence - generic pattern match"
        else:
            return "Low confidence - weak pattern match"