from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Any
from app.services.libgen import LibGenClient
from app.dependencies import get_libgen_client

router = APIRouter()

class SearchResponse(BaseModel):
    success: bool
    results: Optional[Any] = None
    error: Optional[str] = None

class DownloadResponse(BaseModel):
    success: bool
    download_url: Optional[str] = None
    error: Optional[str] = None

class DetectRequest(BaseModel):
    html: str

class DetectResponse(BaseModel):
    success: bool
    books: List[Any]

@router.get("/search", response_model=SearchResponse)
async def search_books(
    q: str,
    client: LibGenClient = Depends(get_libgen_client)
):
    try:
        results = await client.search(q)
        return SearchResponse(
            success=True,
            results=results
        )
    except Exception as e:
        return SearchResponse(
            success=False,
            error=str(e)
        )

@router.get("/download/{md5}", response_model=DownloadResponse)
async def get_download_url(
    md5: str,
    client: LibGenClient = Depends(get_libgen_client)
):
    try:
        url = await client.get_download_url(md5)
        return DownloadResponse(
            success=True,
            download_url=url
        )
    except Exception as e:
        return DownloadResponse(
            success=False,
            error=str(e)
        )

@router.post("/detect", response_model=DetectResponse)
async def detect_books(
    request: DetectRequest,
    client: LibGenClient = Depends(get_libgen_client)
):
    books = await client.detect_books_from_html(request.html)
    return DetectResponse(
        success=True,
        books=books
    )
