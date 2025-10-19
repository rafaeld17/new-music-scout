"""
Simple script to run review aggregation.
"""
import sys
sys.path.insert(0, 'src')

from sqlmodel import create_engine, Session, SQLModel
from music_scout.services.review_aggregator import ReviewAggregator
from music_scout.core.config import settings

# Create engine
engine = create_engine(settings.database_url, echo=False)

# Create session
with Session(engine) as session:
    print("Running review aggregation...")
    aggregator = ReviewAggregator(session)

    try:
        aggregates = aggregator.aggregate_all_reviews()
        print(f"\n✅ Successfully aggregated reviews for {len(aggregates)} albums")

        for agg in aggregates[:5]:  # Show first 5
            print(f"\n  Album ID {agg.album_id}:")
            print(f"    - Reviews: {agg.review_count}")
            print(f"    - Weighted Average: {agg.weighted_average:.2f}")
            print(f"    - Consensus: {agg.consensus_strength:.2f}")

    except Exception as e:
        print(f"\n❌ Error during aggregation: {e}")
        import traceback
        traceback.print_exc()
