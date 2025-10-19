"""
Content API endpoints for retrieving music items with filtering.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, desc

from ..core.database import get_session
from ..models import MusicItem, ContentType, Source

router = APIRouter()


@router.get("/items", response_model=List[dict])
async def get_items(
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    session: Session = Depends(get_session)
):
    """Get music items with optional filtering."""
    query = select(MusicItem, Source).join(Source)

    # Apply filters
    if content_type:
        query = query.where(MusicItem.content_type == content_type)

    if source_id:
        query = query.where(MusicItem.source_id == source_id)

    # Order by date (newest first) and apply pagination
    query = query.order_by(desc(MusicItem.published_date)).offset(offset).limit(limit)

    results = session.exec(query).all()

    # Format response
    items = []
    for music_item, source in results:
        items.append({
            "id": music_item.id,
            "title": music_item.title,
            "url": music_item.url,
            "content_type": music_item.content_type.value,
            "artists": music_item.artists,
            "album": music_item.album,
            "review_score": music_item.review_score,
            "review_score_raw": music_item.review_score_raw,
            "published_date": music_item.published_date.isoformat() if music_item.published_date else None,
            "author": music_item.author,
            "source": {
                "id": source.id,
                "name": source.name,
                "weight": source.weight
            }
        })

    return items


@router.get("/reviews", response_model=List[dict])
async def get_reviews(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    min_score: Optional[float] = Query(None, ge=0, le=10, description="Minimum review score"),
    max_score: Optional[float] = Query(None, ge=0, le=10, description="Maximum review score"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    offset: int = Query(0, ge=0, description="Number of reviews to skip"),
    session: Session = Depends(get_session)
):
    """Get reviews with optional score and source filtering."""
    query = select(MusicItem, Source).join(Source).where(MusicItem.content_type == ContentType.REVIEW)

    # Apply filters
    if source_id:
        query = query.where(MusicItem.source_id == source_id)

    if min_score is not None:
        query = query.where(MusicItem.review_score >= min_score)

    if max_score is not None:
        query = query.where(MusicItem.review_score <= max_score)

    # Order by score (highest first), then by date
    query = query.order_by(desc(MusicItem.review_score), desc(MusicItem.published_date))
    query = query.offset(offset).limit(limit)

    results = session.exec(query).all()

    # Format response
    reviews = []
    for music_item, source in results:
        reviews.append({
            "id": music_item.id,
            "title": music_item.title,
            "url": music_item.url,
            "artists": music_item.artists,
            "album": music_item.album,
            "review_score": music_item.review_score,
            "review_score_raw": music_item.review_score_raw,
            "published_date": music_item.published_date.isoformat() if music_item.published_date else None,
            "author": music_item.author,
            "source": {
                "id": source.id,
                "name": source.name,
                "weight": source.weight
            }
        })

    return reviews


@router.get("/news", response_model=List[dict])
async def get_news(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of news items to return"),
    offset: int = Query(0, ge=0, description="Number of news items to skip"),
    session: Session = Depends(get_session)
):
    """Get news items with optional source filtering."""
    query = select(MusicItem, Source).join(Source).where(MusicItem.content_type == ContentType.NEWS)

    # Apply filters
    if source_id:
        query = query.where(MusicItem.source_id == source_id)

    # Order by date (newest first)
    query = query.order_by(desc(MusicItem.published_date)).offset(offset).limit(limit)

    results = session.exec(query).all()

    # Format response
    news_items = []
    for music_item, source in results:
        news_items.append({
            "id": music_item.id,
            "title": music_item.title,
            "url": music_item.url,
            "artists": music_item.artists,
            "album": music_item.album,
            "published_date": music_item.published_date.isoformat() if music_item.published_date else None,
            "author": music_item.author,
            "source": {
                "id": source.id,
                "name": source.name,
                "weight": source.weight
            }
        })

    return news_items


@router.get("/albums")
async def get_albums(
    limit: int = Query(50, ge=1, le=200, description="Number of albums to return"),
    offset: int = Query(0, ge=0, description="Number of albums to skip"),
    fetch_metadata: bool = Query(False, description="Fetch cover art and genres from MusicBrainz"),
    session: Session = Depends(get_session)
):
    """Get unique albums with their reviews grouped by album (simple grouping by artist+album)."""
    from collections import defaultdict
    from ..services.metadata_fetcher import get_metadata_fetcher

    # Get all reviews with album information
    query = select(MusicItem, Source).join(Source).where(
        MusicItem.content_type == ContentType.REVIEW,
        MusicItem.album.isnot(None),
        MusicItem.artists != []
    ).order_by(desc(MusicItem.published_date))

    reviews = session.exec(query).all()

    # Group reviews by album + artist combination
    albums_dict = defaultdict(lambda: {
        "reviews": [],
        "first_seen": None,
        "latest_review": None
    })

    for music_item, source in reviews:
        if not music_item.album or not music_item.artists:
            continue

        # Filter out concert reviews and weekly roundups (check title and album name)
        title_lower = music_item.title.lower()
        album_lower = music_item.album.lower() if music_item.album else ""

        concert_keywords = [
            'concert review', 'live review', 'show review', 'gig review',
            'tour review', 'performance review', 'live at', 'live in',
            'concert report', 'live report', 'setlist'
        ]

        # Filter out weekly roundup posts (Heavy Music HQ, etc.)
        roundup_keywords = [
            'week of', 'weekly review', 'roundup', 'reviews:', 'this week',
            'weekly roundup', 'album reviews:', 'monthly review', 'month of',
            'hq reviews'
        ]

        is_concert = any(keyword in title_lower or keyword in album_lower for keyword in concert_keywords)
        is_roundup = any(keyword in title_lower or keyword in album_lower for keyword in roundup_keywords)

        if is_concert or is_roundup:
            continue

        # Create a simple key from artist + album
        artist_key = music_item.artists[0].lower().strip() if music_item.artists else ""
        album_key = music_item.album.lower().strip()
        key = f"{artist_key}|||{album_key}"

        review_data = {
            "id": music_item.id,
            "title": music_item.title,
            "url": music_item.url,
            "review_score": music_item.review_score,
            "review_score_raw": music_item.review_score_raw,
            "published_date": music_item.published_date.isoformat() if music_item.published_date else None,
            "author": music_item.author,
            "content": music_item.processed_content or music_item.raw_content or "",
            "source": {
                "id": source.id,
                "name": source.name
            }
        }

        albums_dict[key]["reviews"].append(review_data)
        albums_dict[key]["artist"] = music_item.artists[0] if music_item.artists else "Unknown"
        albums_dict[key]["album"] = music_item.album

        # Track dates
        if not albums_dict[key]["first_seen"] or music_item.published_date < albums_dict[key]["first_seen"]:
            albums_dict[key]["first_seen"] = music_item.published_date
        if not albums_dict[key]["latest_review"] or music_item.published_date > albums_dict[key]["latest_review"]:
            albums_dict[key]["latest_review"] = music_item.published_date

    # Convert to list and collect cached metadata
    albums_list = []

    for key, data in albums_dict.items():
        # Get cached metadata and tracks from all reviews of this album
        genres = []
        cover_art_url = None
        album_tracks = []  # Collect tracks at album level

        for review_data in data["reviews"]:
            # Find the music_item that matches this review
            for music_item, source in reviews:
                if music_item.id == review_data["id"]:
                    if music_item.album_genres:
                        # Parse JSON string to list
                        import json
                        try:
                            genres = json.loads(music_item.album_genres) if isinstance(music_item.album_genres, str) else music_item.album_genres
                        except (json.JSONDecodeError, TypeError):
                            genres = []
                    if music_item.album_cover_url:
                        cover_art_url = music_item.album_cover_url
                    # Collect tracks from this review
                    if music_item.tracks and len(music_item.tracks) > 0:
                        # Merge tracks, preferring longer tracklist
                        if len(music_item.tracks) > len(album_tracks):
                            album_tracks = music_item.tracks
                    break
            if genres or cover_art_url:
                break

        albums_list.append({
            "artist": data["artist"],
            "album": data["album"],
            "review_count": len(data["reviews"]),
            "reviews": data["reviews"],
            "first_seen": data["first_seen"].isoformat() if data["first_seen"] else None,
            "latest_review": data["latest_review"].isoformat() if data["latest_review"] else None,
            "genres": genres,
            "cover_art_url": cover_art_url,
            "tracks": album_tracks  # Add tracks at album level
        })

    # Sort by latest review (most recent first)
    albums_list.sort(key=lambda x: x["latest_review"] or "", reverse=True)

    # Apply pagination
    total = len(albums_list)
    paginated = albums_list[offset:offset + limit]

    # Optionally fetch and cache metadata for paginated results
    if fetch_metadata:
        metadata_fetcher = get_metadata_fetcher()
        for album in paginated:
            # Skip if already has metadata
            if album["genres"] or album["cover_art_url"]:
                continue

            # Fetch from MusicBrainz
            metadata = metadata_fetcher.search_album(album["artist"], album["album"])
            if metadata:
                genres = metadata.get("genres", [])
                cover_url = metadata.get("cover_art_url")

                album["genres"] = genres
                album["cover_art_url"] = cover_url

                # Cache in database - update all reviews for this album
                for music_item, source in reviews:
                    if (music_item.artists and music_item.artists[0] == album["artist"] and
                        music_item.album == album["album"]):
                        music_item.album_genres = genres
                        music_item.album_cover_url = cover_url
                        music_item.musicbrainz_id = metadata.get("musicbrainz_id")
                        session.add(music_item)

                session.commit()

    return {
        "total": total,
        "items": paginated,
        "limit": limit,
        "offset": offset
    }


@router.get("/singles")
async def get_singles(
    limit: int = Query(50, ge=1, le=100, description="Number of singles to return"),
    offset: int = Query(0, ge=0, description="Number of singles to skip"),
    session: Session = Depends(get_session)
):
    """Get recent singles/tracks from news and premieres."""
    # Get items with tracks (news, premieres)
    query = select(MusicItem, Source).join(Source).where(
        MusicItem.tracks.op('!=')('[]')
    ).order_by(desc(MusicItem.published_date))

    results = session.exec(query).all()

    # Format response
    singles = []
    for music_item, source in results:
        if music_item.tracks and len(music_item.tracks) > 0:
            artist = music_item.artists[0] if music_item.artists else "Unknown Artist"

            singles.append({
                "id": music_item.id,
                "title": music_item.title,
                "url": music_item.url,
                "artist": artist,
                "album": music_item.album,
                "tracks": music_item.tracks,
                "content_type": music_item.content_type.value,
                "published_date": music_item.published_date.isoformat() if music_item.published_date else None,
                "source": {
                    "id": source.id,
                    "name": source.name
                },
                "cover_art_url": music_item.album_cover_url,
                "genres": music_item.album_genres if music_item.album_genres else []
            })

    # Apply pagination
    total = len(singles)
    paginated = singles[offset:offset + limit]

    return {
        "total": total,
        "items": paginated,
        "limit": limit,
        "offset": offset
    }


@router.get("/sources")
async def get_sources(session: Session = Depends(get_session)):
    """Get all available sources with item counts."""
    sources_query = select(Source).where(Source.enabled == True)
    sources = session.exec(sources_query).all()

    sources_data = []
    for source in sources:
        # Count items by type for this source
        from sqlmodel import func

        total_count = session.exec(
            select(func.count(MusicItem.id)).where(MusicItem.source_id == source.id)
        ).one()

        review_count = session.exec(
            select(func.count(MusicItem.id)).where(
                MusicItem.source_id == source.id,
                MusicItem.content_type == ContentType.REVIEW
            )
        ).one()

        news_count = session.exec(
            select(func.count(MusicItem.id)).where(
                MusicItem.source_id == source.id,
                MusicItem.content_type == ContentType.NEWS
            )
        ).one()

        sources_data.append({
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "weight": source.weight,
            "health_score": source.health_score,
            "item_counts": {
                "total": total_count,
                "reviews": review_count,
                "news": news_count
            }
        })

    return sources_data
