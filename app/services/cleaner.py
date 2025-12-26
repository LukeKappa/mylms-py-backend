import re
import logging
from bs4 import BeautifulSoup, Comment
from typing import Optional, List

logger = logging.getLogger(__name__)

# Kortext phrases - containers with these phrases are removed
KORTEXT_PHRASES = [
    "Sign in to Kortext",
    "Open book in new window",
    "You will only be able to access the book on Kortext",
    "kortext.com",
    "launchReader",
    "emailKortextSupport",
]

# Prescribed Reading phrases
PRESCRIBED_READING_PHRASES = [
    "Prescribed Reading",
]

# Container classes to remove when they contain unwanted text
CONTAINER_CLASSES = [
    "no-overflow",
    "box",
    "generalbox",
    "prescribed-reading",
]

# Unwanted elements selectors
UNWANTED_SELECTORS = [
    "script",
    "style",
    "link[rel='stylesheet']",
    "iframe",
    "nav",
    ".navigation",
    ".breadcrumb",
    "#page-header",
    ".modified",
    ".activity-navigation",
]

def clean_html_content(html: str) -> str:
    return clean_html_with_token(html, None)

def clean_html_with_token(html: str, token: Optional[str] = None) -> str:
    if not html:
        return ""
    
    original_len = len(html)
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Remove unwanted elements
    for selector in UNWANTED_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()
            
    # 2. Remove unwanted containers (Kortext, etc)
    remove_unwanted_containers(soup)
    
    # 3. Remove duplicate headings
    remove_duplicate_headings(soup)
    
    # 4. Clean images
    clean_images(soup)
    
    # 5. Remove empty paragraphs
    remove_empty_paragraphs(soup)
    
    # 6. Fix image URLs
    if token:
        fix_image_urls(soup, token)
        
    # Get string
    output = str(soup)
    
    # 7. Fix entity encoding issues (string level replacement)
    output = output.replace("&amp;nbsp;", " ")
    output = output.replace("&nbsp;", " ")
    output = output.replace("&amp;amp;", "&")
    
    logger.debug(f"Cleaned HTML: {original_len} -> {len(output)} bytes")
    
    return output

def remove_unwanted_containers(soup: BeautifulSoup):
    all_phrases = [p.lower() for p in KORTEXT_PHRASES + PRESCRIBED_READING_PHRASES]
    
    for class_name in CONTAINER_CLASSES:
        for tag in soup.find_all(class_=class_name):
            # Check text and stringified HTML for phrases
            tag_html_lower = str(tag).lower()
            
            if any(phrase in tag_html_lower for phrase in all_phrases):
                logger.debug(f"Removed container .{class_name} with unwanted content")
                tag.decompose()

def remove_duplicate_headings(soup: BeautifulSoup):
    seen_headings = set()
    
    for tag_name in ["h2", "h3"]:
        for tag in soup.find_all(tag_name):
            text = tag.get_text().strip()
            if not text:
                continue
                
            key = f"{tag_name}:{text}"
            if key in seen_headings:
                logger.debug(f"Removed duplicate heading: {text}")
                tag.decompose()
            else:
                seen_headings.add(key)

def clean_images(soup: BeautifulSoup):
    for img in soup.find_all("img"):
        src = img.get("src", "")
        
        # Remove spacer images
        if not src or src.startswith("data:image/gif;base64") or "spacer" in src:
            img.decompose()

def remove_empty_paragraphs(soup: BeautifulSoup):
    # Regex approach is often cleaner for this than soup traversal because of nested whitespace
    # But let's try soup first to be safe, or just do regex on the string at the end?
    # The rust implem used regex on the string: r"<p[^>]*>\s*(&nbsp;|\s)*\s*</p>"
    # Let's do the same string replacement at the end or apply to soup?
    # Applying regex to soup string is dangerous if we serialize/deserialize.
    # Let's do it on the soup elements.
    for p in soup.find_all("p"):
        # Check if text is only whitespace/nbsp using regex
        text = p.get_text()
        if not text.strip():
            # Check if it contains images or other meaningful tags (like input, etc - though we clean most)
            if not p.find_all(["img", "video", "audio", "iframe"]):
                p.decompose()

def fix_image_urls(soup: BeautifulSoup, token: str):
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
            
        if "token=" in src:
            continue
            
        if src.startswith("data:"):
            continue
            
        if src.startswith("http") and "mylms.vossie.net" not in src:
            continue
            
        # Add token
        separator = "&" if "?" in src else "?"
        new_src = f"{src}{separator}token={token}"
        img["src"] = new_src
