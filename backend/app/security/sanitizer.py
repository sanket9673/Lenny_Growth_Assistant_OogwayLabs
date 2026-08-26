import re
from typing import Dict

def sanitize_html_content(html: str) -> str:
    """
    Sanitizes HTML content by stripping script tags, inline event handlers,
    and javascript: links to prevent XSS.
    """
    if not html:
        return ""
        
    # Remove script tags and blocks
    clean = re.sub(r'(?i)<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html)
    clean = re.sub(r'(?i)<script.*?>.*?</script>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'(?i)<\/?script.*?>', '', clean)
    
    # Remove inline handlers like onerror, onload, onclick
    clean = re.sub(r'(?i)\bon[a-z]+\s*=\s*(["\'])(.*?)\1', '', clean)
    clean = re.sub(r'(?i)\bon[a-z]+\s*=\s*[^>\s]+', '', clean)
    
    # Remove javascript: scheme
    clean = re.sub(r'(?i)href\s*=\s*(["\'])\s*javascript:.*?\1', 'href="#"', clean)
    clean = re.sub(r'(?i)src\s*=\s*(["\'])\s*javascript:.*?\1', 'src=""', clean)
    
    return clean

def generate_sandbox_headers() -> Dict[str, str]:
    """
    Generates security sandbox headers for rendering iframe preview.
    Excludes allow-same-origin to prevent local cookie access.
    """
    return {
        "Content-Security-Policy": "sandbox allow-scripts"
    }
