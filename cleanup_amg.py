"""
Quick script to delete Angry Metal Guy source and all its content
"""
from sqlmodel import Session, select, create_engine, delete
from src.music_scout.models import Source, MusicItem

engine = create_engine('sqlite:///src/music_scout.db')

with Session(engine) as session:
    # Find AMG source
    amg = session.exec(select(Source).where(Source.name == "Angry Metal Guy")).first()

    if amg:
        print(f"Found Angry Metal Guy source (ID: {amg.id})")

        # Count items
        items = session.exec(select(MusicItem).where(MusicItem.source_id == amg.id)).all()
        print(f"Found {len(items)} items from Angry Metal Guy")

        # Delete all items
        session.exec(delete(MusicItem).where(MusicItem.source_id == amg.id))
        print(f"Deleted {len(items)} items")

        # Delete source
        session.delete(amg)
        print("Deleted Angry Metal Guy source")

        session.commit()
        print("✓ Cleanup complete!")
    else:
        print("Angry Metal Guy source not found")
