---
title: AI Narrator
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# AI Narrator

A Flask web application that converts research papers, articles, and web content into AI-generated podcast audio. Built to help researchers and students consume academic content more efficiently.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude--Opus--4-purple.svg)](https://anthropic.com)


## Features

### Content Processing
- **Multi-format Support**: Handles PDF uploads and web URLs
- **Content Type Detection**: Automatically identifies research papers, news articles, tutorials, and general content
- **Text Extraction**: Uses PyMuPDF for PDFs and BeautifulSoup for web scraping with content filtering
- **Large Document Handling**: Processes content up to 600K+ characters leveraging Claude Opus 4's 200K token context

### Podcast Generation
- **Adaptive Length**: Determines podcast duration based on content size
  - Short content (< 5K chars): Comprehensive coverage
  - Medium content (5K-20K chars): Detailed analysis
  - Long content (20K-50K chars): In-depth exploration
  - Extended content (50K-100K chars): Comprehensive coverage
  - Comprehensive content (100K+ chars): Extensive detailed analysis
- **Content-Specific Scripts**: Tailored explanations for research, news, tutorials, and general content
- **Structured Format**: Includes compelling hooks, digestible insights, real-world implications, and memorable conclusions
- **Maximum Output**: Generates up to 32,000 tokens of comprehensive podcast content

### Audio Generation
- **OpenAI TTS Integration**: Uses OpenAI's tts-1-hd model with natural 'alloy' voice
- **High-Quality Audio**: Generates MP3 files with conversational tone optimized for learning
- **Intelligent Chunking**: Processes long scripts in 4K character chunks for optimal audio quality
- **Fallback Options**: Windows SAPI and tone generation as backup audio methods
- **File Management**: Automatic timestamped file naming and storage

## Technical Implementation

### Backend Architecture
- **Flask Application**: Main web server with modular route handling
- **Anthropic Integration**: Uses Claude Opus 4 (200K token context, 32K output) for comprehensive script generation
- **Audio Pipeline**: OpenAI TTS integration with AudioGenerator class for high-quality speech synthesis
- **File Processing**: Temporary file handling for uploads and audio generation

### Content Processing Pipeline
1. **Input Validation**: Checks file types and URL formats
2. **Text Extraction**: Extracts clean text from PDFs or web pages
3. **Content Analysis**: Determines content type and optimal podcast length
4. **Script Generation**: Creates structured podcast scripts using Anthropic Claude Opus 4
5. **Audio Conversion**: Generates high-quality MP3 files using OpenAI TTS
6. **File Delivery**: Serves audio files through Flask static routes

### Key Components
- `extract_pdf_text()`: PDF text extraction using PyMuPDF with content filtering
- `extract_web_content()`: Web scraping with BeautifulSoup and intelligent content selection
- `detect_content_type()`: Content classification for research, news, tutorials, and general content
- `calculate_podcast_length()`: Dynamic length calculation based on content size
- `chunk_large_document()`: Advanced chunking for documents over 600K characters
- `chunk_content()`: Content splitting optimized for Claude Opus 4's context window
- `create_podcast_script()`: AI-powered script generation using Claude Opus 4 (32K token output)
- `_openai_tts()`: High-quality audio generation using OpenAI's TTS API
- `_windows_sapi()`: Fallback Windows Speech API integration
- `_combine_audio_parts()`: Audio chunk combination with ffmpeg support
- `generate_audio()`: Main audio file creation and management function

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

