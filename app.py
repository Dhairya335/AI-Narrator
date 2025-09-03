import os
import re
import uuid
import tempfile
from datetime import datetime

import fitz
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv

from utils.audio_utils import AudioGenerator

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AUDIO_FOLDER'] = 'static/audio'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
audio_gen = AudioGenerator()

def extract_pdf_text(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            return ''.join(page.get_text() for page in doc)
    except:
        return None

def extract_web_content(url):
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
    soup = BeautifulSoup(html, 'html.parser')
    
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu', 'form']):
        tag.decompose()
    
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
    
    text_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'div'])
    text_parts = []
    
    for elem in text_elements:
        text = elem.get_text(strip=True)
        if text and len(text) > 15 and not text.lower().startswith(('cookie', 'subscribe', 'follow', 'share')):
            text_parts.append(text)
    
    if len(' '.join(text_parts)) < 300:
        for tag in main_content.find_all(['img', 'video', 'audio', 'iframe', 'button']):
            tag.decompose()
        full_text = main_content.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', full_text)
    
    final_text = '\n\n'.join(text_parts)
    return re.sub(r'\s+', ' ', final_text).strip()

def detect_content_type(text):
    text = text.lower()
    
    if any(word in text for word in ['abstract', 'methodology', 'results', 'conclusion', 'references', 'doi:', 'arxiv']):
        return 'research'
    elif any(word in text for word in ['news', 'breaking', 'reported', 'according to']):
        return 'news'
    elif any(word in text for word in ['tutorial', 'how to', 'step by step', 'guide']):
        return 'tutorial'
    return 'general'

def calculate_podcast_length(content_length):
    if content_length < 2000:
        return "short", 3000
    elif content_length < 10000:
        return "medium", 6000
    elif content_length < 30000:
        return "long", 12000
    else:
        return "extended", 20000

def chunk_content(text, max_chunk_size=50000):
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

def create_podcast_script(text):
    print(f"create_podcast_script called with {len(text) if text else 0} characters")
    
    if not text or len(text.strip()) < 50:
        print("Text too short, returning None")
        return None
    
    content_type = detect_content_type(text)
    podcast_length, max_tokens = calculate_podcast_length(len(text))
    print(f"Content type: {content_type}, Length: {podcast_length}, Tokens: {max_tokens}")
    
    system_prompt = (
        "You are an expert podcast host with deep knowledge across all fields. Your specialty is "
        "taking complex information and making it fascinating and accessible. You speak naturally, "
        "like you're having an engaging conversation with a curious friend. No robotic language, "
        "no filler words, just clear expert insights that keep listeners hooked."
    )
    
    structure_prompt = (
        "Structure your podcast script with:\n"
        "1. A compelling hook that immediately shows why this topic matters\n"
        "2. The core content broken down into digestible, fascinating insights\n"
        "3. Real-world implications and why listeners should care\n"
        "4. A memorable conclusion that ties it all together\n\n"
        "Write like you're speaking, not reading. Use natural transitions. Make every sentence count."
    )
    
    length_instructions = {
        "short": "Create a focused 3-4 minute podcast covering the main points clearly.",
        "medium": "Create a 6-8 minute podcast with detailed analysis and context.",
        "long": "Create a 12-15 minute comprehensive podcast covering all major aspects.",
        "extended": "Create a 20-25 minute in-depth podcast with thorough exploration of the topic."
    }
    
    content_instructions = {
        'research': "Explain the research methodology, findings, and implications in accessible terms.",
        'news': "Present facts, provide context, and analyze broader implications.",
        'tutorial': "Walk through concepts step-by-step with clear explanations.",
        'general': "Extract key insights and explain their significance."
    }
    
    chunks = chunk_content(text)
    
    if len(chunks) == 1:
        full_prompt = (
            f"{length_instructions[podcast_length]} "
            f"{content_instructions.get(content_type, content_instructions['general'])}\n\n"
            f"{structure_prompt}\n\n"
            f"Content: {chunks[0]}"
        )
        
        try:
            print(f"Making API call with {len(full_prompt)} character prompt...")
            response = openai_client.chat.completions.create(
                model="o3-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            print("API call successful")
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    else:
        scripts = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = (
                f"Part {i+1} of {len(chunks)}. {length_instructions[podcast_length]} "
                f"{content_instructions.get(content_type, content_instructions['general'])}\n\n"
                f"{structure_prompt}\n\n"
                f"Content: {chunk}"
            )
            
            try:
                response = openai_client.chat.completions.create(
                    model="o3-pro",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": chunk_prompt}
                    ],
                    max_tokens=max_tokens // len(chunks),
                    temperature=0.7
                )
                scripts.append(response.choices[0].message.content.strip())
            except Exception as e:
                print(f"OpenAI API Error for chunk {i+1}: {e}")
                continue
        
        if scripts:
            final_prompt = (
                f"Combine these podcast segments into one cohesive script. "
                f"Ensure smooth transitions and natural flow:\n\n" +
                "\n\n--- SEGMENT BREAK ---\n\n".join(scripts)
            )
            
            try:
                response = openai_client.chat.completions.create(
                    model="o3-pro",
                    messages=[
                        {"role": "system", "content": "You are an expert podcast editor. Create seamless, engaging scripts."},
                        {"role": "user", "content": final_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.6
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI API Error for final script: {e}")
                return "\n\n".join(scripts)
        
        return None

def generate_audio(script):
    try:
        audio_data = audio_gen.create_audio(script)
        if not audio_data:
            return None, "Audio generation failed"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"podcast_{timestamp}.mp3"
        filepath = os.path.join(app.config['AUDIO_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        return f"/static/audio/{filename}", None
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

@app.route('/test-api')
def test_api():
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        return jsonify({'status': 'success', 'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate_podcast():
    print("=== GENERATE PODCAST ROUTE CALLED ===")
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    print(f"Request files: {list(request.files.keys())}")
    print(f"Request is_json: {request.is_json}")
    
    try:
        content = None
        
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'Please upload a PDF file'}), 400
            
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.pdf")
            file.save(temp_path)
            content = extract_pdf_text(temp_path)
            os.remove(temp_path)
            source_type = 'PDF Upload'
            
        elif request.is_json:
            data = request.get_json()
            url = data.get('source')
            
            if not url or not re.match(r'^https?://', url):
                return jsonify({'error': 'Please provide a valid URL'}), 400
            
            content = extract_web_content(url)
            source_type = 'URL'
        
        if not content or len(content.strip()) < 100:
            return jsonify({'error': 'Could not extract enough content from this source'}), 400
        
        print(f"Extracted {len(content)} characters of content")
        print(f"About to call create_podcast_script...")
        
        script = create_podcast_script(content)
        print(f"Script result: {script is not None}")
        if not script:
            print("Script generation returned None")
            return jsonify({'error': 'Failed to generate podcast script. Check console for details.'}), 500
        
        estimated_duration = max(3, len(script) // 150)
        print(f"Generated script with {len(script)} characters, estimated {estimated_duration} minutes")
        
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.txt")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        audio_url, audio_error = generate_audio(script)
        
        response = {
            'status': 'success',
            'script': script,
            'audio_url': audio_url,
            'content_preview': content[:300] + "..." if len(content) > 300 else content,
            'content_length': len(content),
            'script_length': len(script),
            'estimated_duration': f"{estimated_duration} minutes",
            'source_type': source_type
        }
        
        if audio_error:
            response['warning'] = audio_error
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in generate_podcast: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)