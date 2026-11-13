from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import BaseModel

from app.shared.config import settings
from app.shared.errors import ApiError


bearer = HTTPBearer(auto_error=False)


class Principal(BaseModel):
    subject: str
    roles: set[str]


def create_access_token(subject: str, roles: list[str], minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "roles": roles, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def current_principal(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(401, "Se requiere un token Bearer válido.")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        roles = payload.get("roles", [])
        if not subject or not isinstance(roles, list):
            raise InvalidTokenError("claims inválidos")
        return Principal(subject=subject, roles=set(roles))
    except InvalidTokenError as exc:
        raise ApiError(401, "El token es inválido o ha expirado.") from exc


def require_roles(*allowed: str):
    def dependency(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
        if "ADMIN" not in principal.roles and principal.roles.isdisjoint(allowed):
            raise ApiError(403, "El usuario no tiene permisos para esta operación.")
        return principal
    return dependency
