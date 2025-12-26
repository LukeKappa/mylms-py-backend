from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Any
from pydantic import BaseModel
from app.services.moodle import MoodleClient
from app.dependencies import get_moodle_client, get_token

router = APIRouter()

class CoursesResponse(BaseModel):
    courses: List[Any]
    userid: int
    fullname: str

class Activity(BaseModel):
    id: str
    name: str
    activity_type: str
    url: str
    modname: str
    completed: Optional[bool] = None

class SectionWithActivities(BaseModel):
    id: int
    name: str
    summary: str
    activities: List[Activity]

class CourseContentsResponse(BaseModel):
    sections: List[SectionWithActivities]

@router.get("/", response_model=CoursesResponse)
async def get_courses(
    token: str = Depends(get_token),
    client: MoodleClient = Depends(get_moodle_client)
):
    # 1. Get site info to get userid
    site_info = await client.get_site_info(token)
    userid = site_info.get("userid")
    fullname = site_info.get("fullname")
    
    # 2. Get courses
    courses = await client.get_user_courses(token, userid)
    
    return CoursesResponse(
        courses=courses,
        userid=userid,
        fullname=fullname
    )

@router.get("/{id}", response_model=CourseContentsResponse)
async def get_course_contents(
    id: int,
    token: str = Depends(get_token),
    client: MoodleClient = Depends(get_moodle_client)
):
    sections = await client.get_course_contents(token, id)
    
    processed_sections = []
    
    for section in sections:
        activities = []
        modules = section.get("modules", [])
        
        for module in modules:
            # Filter invisible modules
            if module.get("uservisible", True) is False:
                continue
                
            activities.append(Activity(
                id=str(module.get("id")),
                name=module.get("name"),
                activity_type=module.get("modname"),
                url=module.get("url", ""),
                modname=module.get("modname"),
                completed=None, # TODO: Check completion status if available
            ))
            
        processed_sections.append(SectionWithActivities(
            id=section.get("id"),
            name=section.get("name", ""),
            summary=section.get("summary", ""),
            activities=activities
        ))
        
    return CourseContentsResponse(sections=processed_sections)
