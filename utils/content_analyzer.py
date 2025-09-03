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
    if content_length < 2000:
        return "short", 3000
    elif content_length < 10000:
        return "medium", 6000
    elif content_length < 30000:
        return "long", 12000
    else:
        return "extended", 20000


def chunk_content(text, max_chunk_size=50000):
    """Split large content into manageable chunks for processing."""
    if len(text) <= max_chunk_size:
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