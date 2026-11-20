import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.workflow import Notification

logger = logging.getLogger(__name__)


def send_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "academic",
    link: Optional[str] = None
) -> Notification:
    """Dispatches a persistent notification to a user's notification feed."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    logger.info(f"Notification queued for user {user_id}: {title}")
    return notif
