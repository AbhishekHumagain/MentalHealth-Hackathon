from __future__ import annotations

from typing import Annotated

from fastapi import Header


async def get_current_user_id(x_user_id: Annotated[str, Header(alias="X-User-Id")]) -> str:
    return x_user_id
