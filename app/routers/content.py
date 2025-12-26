import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.services.moodle import MoodleClient
from app.services.cleaner import clean_html_with_token
from app.services.cache import cache
from app.dependencies import get_moodle_client, get_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ContentResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    cached: Optional[bool] = None
    error: Optional[str] = None

class BatchPrefetchItem(BaseModel):
    url: str
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None

class BatchPrefetchRequest(BaseModel):
    urls: List[str]

class BatchPrefetchResponse(BaseModel):
    success: bool
    total: int
    loaded: int
    items: List[BatchPrefetchItem]

def extract_module_id(url: str) -> Optional[int]:
    match = re.search(r"[?&]id=(\d+)", url)
    if match:
        return int(match.group(1))
    return None

async def fetch_activity_content(client: MoodleClient, token: str, url: str) -> str:
    cmid = extract_module_id(url)
    if not cmid:
        raise ValueError("Invalid URL: Could not extract module ID")
    
    # Get module info to find course ID
    mod_info = await client.get_course_module(token, cmid)
    
    cm = mod_info.get("cm", {})
    course_id = cm.get("course")
    if not course_id:
        raise ValueError("Could not extract course ID from module info")
    
    # Get course contents
    sections = await client.get_course_contents(token, course_id)
    
    html_files = []
    
    found_module = False
    for section in sections:
        for module in section.get("modules", []):
            if module.get("id") == cmid:
                contents = module.get("contents", [])
                for content in contents:
                    filename = content.get("filename", "").lower()
                    if filename.endswith(".html") or filename.endswith(".htm"):
                        fileurl = content.get("fileurl")
                        if fileurl:
                            html_files.append((fileurl, content.get("filename")))
                found_module = True
                break
        if found_module:
            break
            
    if not html_files:
        # Fallback: Try direct download
        content = await client.download_file(token, url)
        if not content:
            raise ValueError("No content found and direct download failed")
        return content
        
    combined_html = []
    for fileurl, filename in html_files:
        content = await client.download_file(token, fileurl)
        if content:
            combined_html.append(content)
        else:
            logger.warning(f"Failed to download {filename}")
            
    if not combined_html:
        raise ValueError("Failed to download any HTML content files")
        
    return "\n\n".join(combined_html)

@router.get("/activity", response_model=ContentResponse)
async def get_activity_content(
    url: str,
    token: str = Depends(get_token),
    client: MoodleClient = Depends(get_moodle_client)
):
    cache_key = f"activity:{cache.url_hash(url)}"
    
    # Check cache
    cached_content = await cache.get(cache_key)
    if cached_content:
        return ContentResponse(
            success=True,
            content=cached_content,
            cached=True
        )
    
    try:
        raw_content = await fetch_activity_content(client, token, url)
        cleaned_content = clean_html_with_token(raw_content, token)
        
        await cache.set(cache_key, cleaned_content)
        
        return ContentResponse(
            success=True,
            content=cleaned_content,
            cached=False
        )
    except Exception as e:
        logger.error(f"Error fetching content: {e}")
        return ContentResponse(
            success=False,
            error=str(e),
            cached=False
        )

@router.post("/batch", response_model=BatchPrefetchResponse)
async def batch_prefetch(
    request: BatchPrefetchRequest,
    token: str = Depends(get_token),
    client: MoodleClient = Depends(get_moodle_client)
):
    async def process_url(url: str) -> BatchPrefetchItem:
        cache_key = f"activity:{cache.url_hash(url)}"
        
        # Check cache
        cached_content = await cache.get(cache_key)
        if cached_content:
            return BatchPrefetchItem(
                url=url,
                success=True,
                content=cached_content
            )
            
        try:
            raw_content = await fetch_activity_content(client, token, url)
            cleaned_content = clean_html_with_token(raw_content, token)
            await cache.set(cache_key, cleaned_content)
            
            return BatchPrefetchItem(
                url=url,
                success=True,
                content=cleaned_content
            )
        except Exception as e:
            return BatchPrefetchItem(
                url=url,
                success=False,
                error=str(e)
            )
    
    # Limit concurrency
    semaphore = asyncio.Semaphore(10)
    
    async def sem_task(url):
        async with semaphore:
            return await process_url(url)
            
    items = await asyncio.gather(*[sem_task(url) for url in request.urls])
    loaded = sum(1 for item in items if item.success)
    
    return BatchPrefetchResponse(
        success=True,
        total=len(items),
        loaded=loaded,
        items=items
    )

@router.delete("/cache")
async def clear_cache():
    await cache.clear()
    return {"success": True, "message": "Cache cleared"}
