from sqlalchemy import String, Text
import time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    private: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[int] = mapped_column(default=lambda: int(time.time()))  # Unix timestamp
    post_to_rss: Mapped[bool] = mapped_column(default=False)