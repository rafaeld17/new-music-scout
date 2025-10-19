"""CLI command to generate source overview report."""

import click
from sqlalchemy import create_engine, text
from datetime import datetime
from pathlib import Path


@click.command()
def report():
    """Generate source overview report with sample reviews."""

    # Database path
    db_path = Path('src/music_scout.db')
    engine = create_engine(f'sqlite:///{db_path}')

    with engine.connect() as conn:
        # Get sources with their counts
        sources_query = text(
            "SELECT s.id, s.name, s.url, "
            "COUNT(m.id) as total_items, "
            "SUM(CASE WHEN m.content_type = 'REVIEW' THEN 1 ELSE 0 END) as review_count "
            "FROM source s LEFT JOIN musicitem m ON s.id = m.source_id "
            "GROUP BY s.id, s.name, s.url ORDER BY review_count DESC"
        )

        sources = conn.execute(sources_query).fetchall()

        click.echo('='  * 100)
        click.echo('DATABASE OVERVIEW - REVIEWS BY SOURCE')
        click.echo('=' * 100)
        click.echo()

        for source_id, source_name, source_url, total_items, review_count in sources:
            click.echo(f'[{source_id}] {source_name}')
            click.echo(f'    URL: {source_url}')
            click.echo(f'    Total Items: {total_items} ({review_count} reviews)')
            click.echo()

            # Get 5 sample reviews from this source
            sample_query = text(
                "SELECT title, url, published_date, artists, album, metadata_source "
                "FROM musicitem WHERE source_id = :source_id AND content_type = 'REVIEW' "
                "ORDER BY published_date DESC LIMIT 5"
            )

            samples = conn.execute(sample_query, {'source_id': source_id}).fetchall()

            if samples:
                click.echo('    Sample Reviews:')
                for i, (title, url, pub_date, artists, album, meta_source) in enumerate(samples, 1):
                    # Parse published date
                    try:
                        if pub_date:
                            date_obj = datetime.fromisoformat(pub_date.replace(' ', 'T'))
                            date_str = date_obj.strftime('%Y-%m-%d')
                        else:
                            date_str = 'N/A'
                    except:
                        date_str = str(pub_date)[:10] if pub_date else 'N/A'

                    # Clean title for display
                    title_display = title[:70] + '...' if len(title) > 70 else title

                    # Metadata indicator
                    meta_icon = '[Y]' if meta_source else '[N]'

                    click.echo(f'    [{i}] {meta_icon} {date_str} | {title_display}')
                    click.echo(f'        {url}')

                    # Show artist/album if available
                    if artists and artists != '[]':
                        album_display = album if album else '(no album)'
                        click.echo(f'        {artists} - {album_display}')
                    click.echo()
            else:
                click.echo('    No reviews found')
                click.echo()

            click.echo('-' * 100)
            click.echo()

        # Overall stats
        click.echo('=' * 100)
        click.echo('OVERALL STATISTICS')
        click.echo('=' * 100)

        stats_query = text(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN content_type = 'REVIEW' THEN 1 ELSE 0 END) as reviews, "
            "SUM(CASE WHEN metadata_source IS NOT NULL THEN 1 ELSE 0 END) as with_metadata, "
            "SUM(CASE WHEN metadata_source = 'spotify' THEN 1 ELSE 0 END) as spotify, "
            "SUM(CASE WHEN metadata_source = 'musicbrainz' THEN 1 ELSE 0 END) as musicbrainz, "
            "MIN(published_date) as earliest, MAX(published_date) as latest "
            "FROM musicitem"
        )

        stats = conn.execute(stats_query).fetchone()
        total, reviews, with_meta, spotify, mb, earliest, latest = stats

        click.echo(f'Total Items: {total}')
        click.echo(f'Reviews: {reviews} ({reviews/total*100:.1f}%)')
        click.echo(f'With Metadata: {with_meta} ({with_meta/total*100:.1f}%)')
        click.echo(f'  - Spotify: {spotify}')
        click.echo(f'  - MusicBrainz: {mb}')
        click.echo(f'Date Range: {earliest[:10]} to {latest[:10]}')
        click.echo()


if __name__ == '__main__':
    report()
