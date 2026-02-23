"""Celery task for indexing notes into ChromaDB."""
import logging
from sqlalchemy.orm import Session

from app.models.note import Note
from app.database import SessionLocal
from app.services.knowledge_base import knowledge_base_service
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_collection_name(user_id: str) -> str:
    return f"notebook_{user_id.replace('-', '_')}"


def _get_file_id(note_id: str) -> str:
    return f"note_{note_id.replace('-', '_')}"


@celery_app.task(name="index_note")
def index_note_task(note_id: str):
    """Celery task to index a single note into ChromaDB."""
    db: Session = SessionLocal()
    try:
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            logger.warning(f"Note {note_id} not found for indexing")
            return

        user_id = str(note.user_id)
        collection_name = _get_collection_name(user_id)
        file_id = _get_file_id(note_id)

        # Build text for embedding
        tags_str = ", ".join(note.tags) if note.tags else ""
        text = f"# {note.title}\n\n{note.content}"
        if tags_str:
            text += f"\n\nTags: {tags_str}"

        # Get or create the user's notebook collection
        collection = knowledge_base_service.get_or_create_collection(collection_name)

        # Delete old chunks for this note
        try:
            all_data = collection.get()
            ids_to_delete = []
            if all_data['ids'] and all_data['metadatas']:
                for i, metadata in enumerate(all_data['metadatas']):
                    if metadata.get('file_id') == file_id:
                        ids_to_delete.append(all_data['ids'][i])
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
        except Exception as e:
            logger.warning(f"Could not delete old chunks for note {note_id}: {e}")

        # Chunk and re-index
        chunks = knowledge_base_service.chunk_text(text)
        added_count = 0
        for i, chunk in enumerate(chunks):
            embedding = knowledge_base_service.generate_embedding(chunk)
            if not embedding:
                continue
            chunk_id = f"{file_id}_chunk_{i}"
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{
                    "file_id": file_id,
                    "note_id": note_id,
                    "note_title": note.title,
                    "chunk_index": i,
                }]
            )
            added_count += 1

        # Mark note as indexed
        note.chroma_indexed = True
        db.commit()

        logger.info(f"Indexed note {note_id} into {collection_name} ({added_count} chunks)")

    except Exception as e:
        logger.error(f"Error indexing note {note_id}: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def trigger_note_indexing(note_id: str):
    """Trigger async ChromaDB indexing for a note."""
    index_note_task.delay(note_id)
    logger.debug(f"Triggered indexing for note {note_id}")
