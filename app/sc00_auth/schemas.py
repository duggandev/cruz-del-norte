from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    usuario: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=200)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: str
    roles: list[str]
