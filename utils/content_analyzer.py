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
    """Calculate optimal podcast length based on content size."""
    if content_length < 5000:
        return "short"
    elif content_length < 20000:
        return "medium"
    elif content_length < 50000:
        return "long"
    elif content_length < 100000:
        return "extended"
    else:
        return "comprehensive"

def chunk_large_document(text, max_chunk_size=600000):
    """Advanced chunking for very large documents (600k+ characters - Claude Opus 4 can handle 200k tokens)."""
    if len(text) < 600000:  # ~200k tokens worth of characters
        return [text]  # No chunking needed for Claude Opus 4
    
    # For extremely large docs, create chunks with overlap
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Add small overlap for context
            current_chunk = current_chunk[-1000:] + "\n\n" + paragraph
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def chunk_content(text, max_chunk_size=600000):
    """Split large content into manageable chunks for processing."""
    # Claude Opus 4 can handle up to 200k tokens (~600k characters)
    if len(text) <= max_chunk_size:
        return [text]  # No chunking needed
    
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