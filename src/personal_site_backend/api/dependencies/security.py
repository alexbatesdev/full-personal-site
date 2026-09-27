import hmac
import os

from fastapi import Depends, Header, HTTPException, status

INTERNAL_TOKEN_HEADER = "poster-certification-id"

def has_internal_token(
    token: str = Header(default="", alias=INTERNAL_TOKEN_HEADER),
) -> bool:
    expected = os.environ.get("ADMIN_TOKEN")

    if not token:
        return False
    if not expected or not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )
    return True

def require_internal_token(
    is_internal: bool = Depends(has_internal_token),
) -> None:
    if not is_internal:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No! No! That's completely wrong!\nNow scram, non-pirate!",
        )
