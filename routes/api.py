import os
import re
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app

from utils.content_extractor import extract_pdf_text, extract_web_content
from utils.script_generator import ScriptGenerator
from utils.audio_utils import AudioGenerator

api_bp = Blueprint('api', __name__)

# Initialize generators
script_gen = None
audio_gen = None

def init_generators(openai_api_key):
    """Initialize the generators with API keys."""
    global script_gen, audio_gen
    try:
        script_gen = ScriptGenerator(openai_api_key)
        audio_gen = AudioGenerator()
        print("Generators initialized successfully")
    except Exception as e:
        print(f"Error initializing generators: {e}")
        script_gen = None
        audio_gen = None

def generate_audio(script):
    """Generate audio file from script."""
    try:
        audio_data = audio_gen.create_audio(script)
        if not audio_data:
            return None, "Audio generation failed"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"podcast_{timestamp}.mp3"
        filepath = os.path.join(current_app.config['AUDIO_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        return f"/static/audio/{filename}", None
    except Exception as e:
        return None, str(e)

@api_bp.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve audio files."""
    return send_from_directory(current_app.config['AUDIO_FOLDER'], filename)

@api_bp.route('/test-api')
def test_api():
    """Test OpenAI API connection."""
    try:
        response = script_gen.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        return jsonify({'status': 'success', 'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@api_bp.route('/generate', methods=['POST'])
def generate_podcast():
    """Main endpoint for generating podcasts from content."""
    print("=== GENERATE PODCAST ROUTE CALLED ===")
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    print(f"Request files: {list(request.files.keys())}")
    print(f"Request is_json: {request.is_json}")
    
    try:
        content = None
        
        # Handle PDF file upload
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'Please upload a PDF file'}), 400
            
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.pdf")
            file.save(temp_path)
            content = extract_pdf_text(temp_path)
            os.remove(temp_path)
            source_type = 'PDF Upload'
            
        # Handle URL input
        elif request.is_json:
            data = request.get_json()
            url = data.get('source')
            
            if not url or not re.match(r'^https?://', url):
                return jsonify({'error': 'Please provide a valid URL'}), 400
            
            content = extract_web_content(url)
            source_type = 'URL'
        
        # Validate extracted content
        if not content or len(content.strip()) < 100:
            return jsonify({'error': 'Could not extract enough content from this source'}), 400
        
        print(f"Extracted {len(content)} characters of content")
        print(f"About to call create_podcast_script...")
        
        # Check if generators are initialized
        if not script_gen:
            return jsonify({'error': 'OpenAI client not initialized. Check API key configuration.'}), 500
        
        # Generate podcast script
        script = script_gen.create_podcast_script(content)
        print(f"Script result: {script is not None}")
        if not script:
            print("Script generation returned None")
            return jsonify({'error': 'Failed to generate podcast script. Check console for details.'}), 500
        
        print(f"Generated script with {len(script)} characters")
        
        # Save script to file
        script_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.txt")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        # Generate audio
        audio_url, audio_error = generate_audio(script)
        
        response = {
            'success': True,
            'script': script,
            'source_type': source_type,
            'content_length': len(content),
            'script_length': len(script)
        }
        
        if audio_url:
            response['audio_url'] = audio_url
        else:
            response['audio_error'] = audio_error or "Audio generation failed"
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in generate_podcast: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500