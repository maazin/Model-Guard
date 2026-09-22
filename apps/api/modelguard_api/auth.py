"""Demo authentication: the `X-Demo-User` header names a seeded local user.

This is deliberately trivial for a local portfolio app, but every authorization decision is
still enforced server-side against the user's stored role.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api.db import get_db
from modelguard_api.errors import Problem, forbidden
from modelguard_api.models import User


def current_user(
    x_demo_user: str | None = Header(default=None, alias="X-Demo-User"),
    db: Session = Depends(get_db),
) -> User:
    if not x_demo_user:
        raise Problem(
            401,
            "Unauthenticated",
            "Set the X-Demo-User header to a seeded demo user",
            type_="urn:modelguard:unauthenticated",
        )
    user = db.scalar(select(User).where(User.username == x_demo_user))
    if user is None:
        raise Problem(
            401, "Unauthenticated", f"unknown demo user '{x_demo_user}'", type_="urn:modelguard:unauthenticated"
        )
    return user


def require_role(*roles: str) -> Callable[..., User]:
    def _dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise forbidden(f"role '{user.role}' may not perform this action; requires one of {sorted(roles)}")
        return user

    return _dep
