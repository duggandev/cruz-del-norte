from fastapi import APIRouter, HTTPException
from hmac import compare_digest
import os, json
from app.sc00_auth.schemas import LoginRequest, LoginResponse
from app.shared.security import create_access_token

router = APIRouter(prefix="/api/v1", tags=["Autenticacion"])

def _users() -> dict:
    raw = os.getenv("AUTH_USERS_JSON", "")
    if raw:
        try: return json.loads(raw)
        except json.JSONDecodeError: pass
    return {"admin": {"password": "admin-demo", "roles": ["ADMIN"]}, "caja": {"password": "caja-demo", "roles": ["CAJA"]}, "emision": {"password": "emision-demo", "roles": ["EMISION"]}, "mantenimiento": {"password": "mantenimiento-demo", "roles": ["MANTENIMIENTO"]}}

@router.post("/auth/login", response_model=LoginResponse, operation_id="iniciarSesion")
def login(data: LoginRequest):
    user = _users().get(data.usuario)
    if not user or not compare_digest(str(user.get("password", "")), data.password):
        raise HTTPException(status_code=401, detail="Usuario o password invalidos.")
    token = create_access_token(data.usuario, list(user.get("roles", [])), minutes=120)
    return {"access_token": token, "token_type": "bearer", "expires_in": 7200, "usuario": data.usuario, "roles": list(user.get("roles", []))}

@router.get("/auth/roles", operation_id="listarRoles")
def roles():
    return {"roles": ["ADMIN", "CAJA", "EMISION", "MANTENIMIENTO"], "descripcion": "Roles disponibles en Cruz del Norte"}
