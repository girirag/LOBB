from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class URLItem(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    original_url = Column(Text, nullable=False, index=True)
    short_code = Column(String(32), unique=True, index=True, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<URLItem(id={self.id}, short_code='{self.short_code}', clicks={self.clicks})>"
