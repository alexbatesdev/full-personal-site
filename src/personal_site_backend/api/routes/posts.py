from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_site_backend.api.dependencies.database import get_db
from personal_site_backend.api.dependencies.security import (
    has_internal_token,
    require_internal_token,
)
from personal_site_backend.api.tables.posts import Post
from personal_site_backend.main import WEBSITE_DIRECTORY

# ^^ Imports ^^


class PostFields(BaseModel):
    title: str
    body: str
    private: bool = False


class PostCreate(PostFields):
    post_to_rss: bool = False


class PostRead(PostFields):
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
):
    query = select(Post).order_by(Post.id)
    print(f"Admin header present: {admin_header_present}")
    if not admin_header_present:
        query = query.where(Post.private.is_(False))
    return list(session.scalars(query).all())


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

