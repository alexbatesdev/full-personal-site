from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from personal_site_backend.api.dependencies.database import get_db
from personal_site_backend.api.dependencies.security import (
    has_internal_token,
    require_internal_token,
)
from personal_site_backend.api.tables.posts import Post
from personal_site_backend.env import WEBSITE_DIRECTORY

# ^^ Imports ^^


class PostCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = []


class PostRead(PostCreate):
    id: int
    created_at: str
    model_config = ConfigDict(from_attributes=True)


# ^^ Types ^^

post_html_router = APIRouter(tags=["posts html"], prefix="/posts")
post_api_router = APIRouter(tags=["posts"], prefix="/posts")


@post_html_router.get("/{post_id}", response_model=list[PostRead])
def post_page(post_id: int):
    return FileResponse(WEBSITE_DIRECTORY / "posts" / "post_details.html")  


@post_api_router.get("/", response_model=list[PostRead])
def index(
    session: Session = Depends(get_db),
    admin_header_present: bool = Depends(has_internal_token),
    tags: Annotated[list[str] | None, Query()] = None,
    match_all_tags: bool = False,
    created_after: int | None = None,
    created_before: int | None = None,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    query = select(Post).order_by(Post.created_at.desc(), Post.id.desc())
    print(f"Admin header present: {admin_header_present}")
    if not admin_header_present:
        query = query.where(Post.private.is_(False))

    if created_after is not None:
        query = query.where(Post.created_at >= created_after)
    if created_before is not None:
        query = query.where(Post.created_at < created_before)

    if tags:
        if match_all_tags:
            for tag in tags:
                query = query.where(_has_tag([tag]))
        else:
            query = query.where(_has_tag(tags))

    if q:
        escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        query = query.where(
            or_(
                func.lower(Post.title).like(like, escape="\\"),
                func.lower(Post.body).like(like, escape="\\"),
            )
        )

    return list(session.scalars(query.limit(limit).offset(offset)).all())


def _has_tag(tags: list[str]):
    """True when the post's JSON tags list contains any of `tags`."""
    je = func.json_each(Post.tags).table_valued("value")
    return exists().where(je.c.value.in_(tags)).select_from(je)


@post_api_router.get("/{post_id}", response_model=PostRead)
def get_post(
    post_id: int,
    session: Session = Depends(get_db),
    admin_header_present: bool = Depends(has_internal_token),
):
    print(f"Fetching post with ID: {post_id}")
    post = session.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=404,
            detail="IDK what ur lookin for. Nothing here but forest spirits",
        )
    if not admin_header_present and post.private:
        raise HTTPException(
            status_code=404,
            detail="IDK what ur lookin for. Nothing here but forest spirits",
        )
    return post


# vv Secured routes (require secret password) vv


@post_api_router.post(
    "/", response_model=PostRead, dependencies=[Depends(require_internal_token)]
)
def create_post(payload: PostCreate, session: Session = Depends(get_db)):
    post = Post(**payload.model_dump())
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@post_api_router.put(
    "/{post_id}",
    response_model=PostRead,
    dependencies=[Depends(require_internal_token)],
)
def update_post(post_id: int, payload: PostCreate, session: Session = Depends(get_db)):
    post = session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    for field, value in payload.model_dump().items():
        setattr(post, field, value)
    session.commit()
    session.refresh(post)
    return post


@post_api_router.delete(
    "/{post_id}", status_code=204, dependencies=[Depends(require_internal_token)]
)
def delete_post(post_id: int, session: Session = Depends(get_db)):
    post = session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    session.delete(post)
    session.commit()

