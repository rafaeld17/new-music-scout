"""Initial schema - create all tables

Revision ID: initial_schema
Revises:
Create Date: 2025-10-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create source table
    op.create_table(
        'source',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_crawled', sa.DateTime(), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create artist table
    op.create_table(
        'artist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('spotify_id', sa.String(length=100), nullable=True),
        sa.Column('musicbrainz_id', sa.String(length=100), nullable=True),
        sa.Column('genres', sa.JSON(), nullable=True),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create album table
    op.create_table(
        'album',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('artist_id', sa.Integer(), nullable=False),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('spotify_id', sa.String(length=100), nullable=True),
        sa.Column('musicbrainz_id', sa.String(length=100), nullable=True),
        sa.Column('cover_art_url', sa.String(length=500), nullable=True),
        sa.Column('genres', sa.JSON(), nullable=True),
        sa.Column('album_type', sa.String(), nullable=True),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['artist_id'], ['artist.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create musicitem table
    op.create_table(
        'musicitem',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('published_date', sa.DateTime(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('artists', sa.JSON(), nullable=True),
        sa.Column('album', sa.String(), nullable=True),
        sa.Column('review_score', sa.Float(), nullable=True),
        sa.Column('review_score_raw', sa.String(), nullable=True),
        sa.Column('genres', sa.JSON(), nullable=True),
        sa.Column('tracks', sa.JSON(), nullable=True),
        sa.Column('spotify_album_id', sa.String(length=100), nullable=True),
        sa.Column('spotify_artist_id', sa.String(length=100), nullable=True),
        sa.Column('artist_popularity', sa.Integer(), nullable=True),
        sa.Column('album_popularity', sa.Integer(), nullable=True),
        sa.Column('musicbrainz_id', sa.String(length=100), nullable=True),
        sa.Column('album_genres', sa.JSON(), nullable=True),
        sa.Column('album_cover_url', sa.String(length=500), nullable=True),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('album_type', sa.String(), nullable=True),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('metadata_source', sa.String(), nullable=True),
        sa.Column('metadata_fetched_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['source.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )

    # Create album_review_aggregate table
    op.create_table(
        'albumreviewaggregate',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('artist_name', sa.String(), nullable=False),
        sa.Column('album_title', sa.String(), nullable=False),
        sa.Column('review_count', sa.Integer(), nullable=False),
        sa.Column('avg_score', sa.Float(), nullable=True),
        sa.Column('weighted_score', sa.Float(), nullable=True),
        sa.Column('consensus_strength', sa.Float(), nullable=True),
        sa.Column('first_review_date', sa.DateTime(), nullable=True),
        sa.Column('latest_review_date', sa.DateTime(), nullable=True),
        sa.Column('spotify_album_id', sa.String(length=100), nullable=True),
        sa.Column('album_cover_url', sa.String(length=500), nullable=True),
        sa.Column('genres', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_musicitem_content_type', 'musicitem', ['content_type'])
    op.create_index('ix_musicitem_published_date', 'musicitem', ['published_date'])
    op.create_index('ix_albumreviewaggregate_latest_review', 'albumreviewaggregate', ['latest_review_date'])


def downgrade() -> None:
    op.drop_index('ix_albumreviewaggregate_latest_review', table_name='albumreviewaggregate')
    op.drop_index('ix_musicitem_published_date', table_name='musicitem')
    op.drop_index('ix_musicitem_content_type', table_name='musicitem')
    op.drop_table('albumreviewaggregate')
    op.drop_table('musicitem')
    op.drop_table('album')
    op.drop_table('artist')
    op.drop_table('source')
