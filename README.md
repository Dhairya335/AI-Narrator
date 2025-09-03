# AI Narrator

A Flask web application that converts research papers, articles, and web content into AI-generated podcast audio. Built to help researchers and students consume academic content more efficiently.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com)

## Features

### Content Processing
- **Multi-format Support**: Handles PDF uploads and web URLs
- **Content Type Detection**: Automatically identifies research papers, news articles, tutorials, and general content
- **Text Extraction**: Uses PyMuPDF for PDFs and BeautifulSoup for web scraping with content filtering
- **Large Document Handling**: Processes content up to 50K+ characters with intelligent chunking

### Podcast Generation
- **Adaptive Length**: Determines podcast duration based on content size
  - Short content (< 2K chars): 3-4 minutes
  - Medium content (2K-10K chars): 6-8 minutes  
  - Long content (10K-30K chars): 12-15 minutes
  - Extended content (30K+ chars): 20-25 minutes
- **Content-Specific Scripts**: Tailored explanations for different content types
- **Structured Format**: Includes hooks, main content, implications, and conclusions

### Audio Generation
- **Text-to-Speech**: Converts generated scripts to MP3 audio files
- **Natural Delivery**: Conversational tone optimized for learning
- **File Management**: Automatic timestamped file naming and storage

## Technical Implementation

### Backend Architecture
- **Flask Application**: Main web server with modular route handling
- **OpenAI Integration**: Uses GPT-4 for script generation with dynamic token limits
- **Audio Pipeline**: Custom AudioGenerator class for speech synthesis
- **File Processing**: Temporary file handling for uploads and audio generation

### Content Processing Pipeline
1. **Input Validation**: Checks file types and URL formats
2. **Text Extraction**: Extracts clean text from PDFs or web pages
3. **Content Analysis**: Determines content type and optimal podcast length
4. **Script Generation**: Creates structured podcast scripts using OpenAI API
5. **Audio Conversion**: Generates MP3 files from scripts
6. **File Delivery**: Serves audio files through Flask static routes

### Key Components
- `extract_pdf_text()`: PDF text extraction using PyMuPDF
- `extract_web_content()`: Web scraping with intelligent content selection
- `detect_content_type()`: Content classification based on keywords
- `calculate_podcast_length()`: Dynamic length calculation
- `create_podcast_script()`: AI-powered script generation with chunking support
- `generate_audio()`: Audio file creation and management

## Use Cases

- **Academic Research**: Convert research papers into audio summaries
- **Student Learning**: Transform study materials into portable podcasts
- **Professional Development**: Stay updated with industry content during commutes
- **Content Accessibility**: Make written content available in audio format
- **Content Creation**: Generate podcast drafts from existing written material

## Project Structure

```
research-podcast-generator/
├── app.py                      # Main Flask application entry point
├── routes/
│   ├── __init__.py
│   └── api.py                  # API endpoints and request handling
├── utils/
│   ├── __init__.py
│   ├── audio_utils.py          # Audio generation utilities
│   ├── content_extractor.py    # PDF and web content extraction
│   ├── content_analyzer.py     # Content type detection and analysis
│   └── script_generator.py     # AI-powered script generation
├── templates/
│   └── index.html              # Web interface
├── static/
│   └── audio/                  # Generated podcast files
├── uploads/                    # Temporary file storage
└── requirements.txt            # Python dependencies
```

Built for researchers, students, and professionals who need efficient ways to consume written content.
