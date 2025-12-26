from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.services.moodle import MoodleClient
from app.services.libgen import LibGenClient

async def get_moodle_client():
    client = MoodleClient()
    try:
        yield client
    finally:
        await client.close()

async def get_libgen_client():
    client = LibGenClient()
    try:
        yield client
    finally:
        await client.close()

async def get_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    
    return authorization
