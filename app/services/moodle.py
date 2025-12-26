import httpx
import logging
import json
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class MoodleError(Exception):
    pass

class MoodleClient:
    def __init__(self):
        self.base_url = settings.MOODLE_URL
        self.service = settings.MOODLE_SERVICE
        self.webservice_url = f"{self.base_url}/webservice/rest/server.php"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()
        
    async def call(self, token: str, wsfunction: str, **params) -> Any:
        data = {
            "wstoken": token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
            **params
        }
        
        logger.debug(f"Moodle API call: {wsfunction}")
        
        try:
            response = await self.client.post(self.webservice_url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            # Check for Moodle error format
            # { "exception": "...", "errorcode": "...", "message": "..." }
            if isinstance(result, dict) and "exception" in result:
                raise MoodleError(result.get("message", "Unknown Moodle Error"))
                
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            raise MoodleError(f"Communication error: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response")
            raise MoodleError("Invalid JSON response from Moodle")

    async def get_site_info(self, token: str) -> Dict[str, Any]:
        return await self.call(token, "core_webservice_get_site_info")

    async def get_user_courses(self, token: str, userid: int) -> List[Dict[str, Any]]:
        return await self.call(token, "core_enrol_get_users_courses", userid=userid)

    async def get_course_contents(self, token: str, courseid: int) -> List[Dict[str, Any]]:
        return await self.call(token, "core_course_get_contents", courseid=courseid)

    async def get_course_module(self, token: str, cmid: int) -> Dict[str, Any]:
        return await self.call(token, "core_course_get_course_module", cmid=cmid)
    
    async def download_file(self, token: str, file_url: str) -> Optional[str]:
        # Handle token in URL
        url = file_url
        if "token=" not in url and "wstoken=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}token={token}"
            
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Check for error in content (Moodle returns 200 OK even for some errors with JSON body)
            content = response.text
            if content.strip().startswith("{") and '"error"' in content:
                # Basic check, might be false positive if file is JSON
                try:
                    data = json.loads(content)
                    if "error" in data or "exception" in data:
                        logger.error(f"File download error: {data}")
                        return None
                except:
                    pass
                    
            return content
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return None
