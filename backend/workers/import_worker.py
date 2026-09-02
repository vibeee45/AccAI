from workers.celery_app import celery_app


@celery_app.task(name="accai.test_task")
def test_task(message: str) -> dict:
    """
    Temporary Celery test task.

    This verifies that:
    FastAPI/application code -> Redis -> Celery Worker
    is functioning correctly.
    """

    return {
        "status": "success",
        "message": message,
        "worker": "accai-celery",
    }