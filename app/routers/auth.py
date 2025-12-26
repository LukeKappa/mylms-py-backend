from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.moodle import MoodleClient
from app.dependencies import get_moodle_client

router = APIRouter()

class LoginRequest(BaseModel):
    token: str

class UserInfo(BaseModel):
    userid: int
    username: str
    fullname: str
    userpictureurl: Optional[str] = None

class LoginResponse(BaseModel):
    success: bool
    user: Optional[UserInfo] = None
    error: Optional[str] = None

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    client: MoodleClient = Depends(get_moodle_client)
):
    try:
        site_info = await client.get_site_info(request.token)
        
        return LoginResponse(
            success=True,
            user=UserInfo(
                userid=site_info.get("userid"),
                username=site_info.get("username"),
                fullname=site_info.get("fullname"),
                userpictureurl=site_info.get("userpictureurl"),
            )
        )
    except Exception as e:
        return LoginResponse(
            success=False,
            error=str(e)
        )

@router.post("/validate")
async def validate_token(
    request: LoginRequest,
    client: MoodleClient = Depends(get_moodle_client)
):
    try:
        await client.get_site_info(request.token)
        return {"valid": True}
    except:
        return {"valid": False}
