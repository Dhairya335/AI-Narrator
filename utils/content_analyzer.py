def detect_content_type(text):
    """Detect the type of content based on keywords and patterns."""
    text = text.lower()
    
    if any(word in text for word in ['abstract', 'methodology', 'results', 'conclusion', 'references', 'doi:', 'arxiv']):
        return 'research'
    elif any(word in text for word in ['news', 'breaking', 'reported', 'according to']):
        return 'news'
    elif any(word in text for word in ['tutorial', 'how to', 'step by step', 'guide']):
        return 'tutorial'
    return 'general'


def calculate_podcast_length(content_length):
    """Calculate optimal podcast length and token limits based on content size."""
    if content_length < 5000:
        return "short", 8000
    elif content_length < 20000:
        return "medium", 15000
    elif content_length < 50000:
        return "long", 25000
    elif content_length < 100000:
        return "extended", 40000
    else:
        return "comprehensive", 60000

def chunk_large_document(text, max_chunk_size=80000):
    """Advanced chunking for very large documents (100k+ characters)."""
    if len(text) < 100000:
        return chunk_content(text)
    
    # For very large docs, create more chunks with overlap
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Add small overlap for context
            current_chunk = current_chunk[-500:] + "\n\n" + paragraph
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def chunk_content(text, max_chunk_size=80000):
    """Split large content into manageable chunks for processing."""
    # For very large documents, always use chunking to ensure better processing
    if len(text) <= max_chunk_size and len(text) < 50000:
        return [text]
    
    chunks = []
    sentences = text.split('. ')
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
        else:
            current_chunk += sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks