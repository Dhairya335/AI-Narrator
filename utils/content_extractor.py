import os
import re
import tempfile
import requests
import fitz
from bs4 import BeautifulSoup


def extract_pdf_text(pdf_path):
    """Extract text from PDF file using PyMuPDF."""
    try:
        with fitz.open(pdf_path) as doc:
            return ''.join(page.get_text() for page in doc)
    except:
        return None


def extract_web_content(url):
    """Extract content from web URL, handling both HTML and PDF content."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        if 'pdf' in response.headers.get('content-type', '') or url.endswith('.pdf'):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(response.content)
                text = extract_pdf_text(tmp.name)
                os.unlink(tmp.name)
                return text
        
        return parse_html_content(response.text)
    except Exception as e:
        print(f"Web extraction error: {e}")
        return None


def parse_html_content(html):
    """Parse HTML content and extract main text content."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted elements
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu', 'form']):
        tag.decompose()
    
    # Try to find main content area
    content_selectors = [
        'article', 'main', '[role="main"]', '.content', '.post-content', 
        '.entry-content', '.article-content', '#content', '.post-body'
    ]
    
    main_content = None
    for selector in content_selectors:
        elements = soup.select(selector)
        if elements:
            main_content = elements[0]
            break
    
    if not main_content:
        main_content = soup.find('body') or soup
    
    # Extract text from relevant elements
    text_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'div'])
    text_parts = []
    
    for elem in text_elements:
        text = elem.get_text(strip=True)
        if text and len(text) > 15 and not text.lower().startswith(('cookie', 'subscribe', 'follow', 'share')):
            text_parts.append(text)
    
    # Fallback for short content
    if len(' '.join(text_parts)) < 300:
        for tag in main_content.find_all(['img', 'video', 'audio', 'iframe', 'button']):
            tag.decompose()
        full_text = main_content.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', full_text)
    
    final_text = '\n\n'.join(text_parts)
    return re.sub(r'\s+', ' ', final_text).strip()