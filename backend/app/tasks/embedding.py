from app.celery_app import celery_app


@celery_app.task
def index_item(item_id: str):
    # Placeholder for embedding task
    print(f"Indexing item {item_id}")
    return {"status": "success", "item_id": item_id}
