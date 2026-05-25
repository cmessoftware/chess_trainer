"""
Simple test router to debug login issues
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class SimpleLogin(BaseModel):
    username: str
    password: str

class SimpleResponse(BaseModel):
    message: str
    username: str

@router.post("/test-login")
async def test_login(credentials: SimpleLogin):
    """Simple test login endpoint"""
    if credentials.username == "admin" and credentials.password == "admin123":
        return SimpleResponse(
            message="Login successful", 
            username=credentials.username
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")