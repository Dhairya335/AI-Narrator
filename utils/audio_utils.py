import os
import io
import math
import struct
import tempfile

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import win32com.client
except ImportError:
    win32com = None

class AudioGenerator:
    def __init__(self):
        self.openai_client = None
        self._init_openai_tts()
    
    def _init_openai_tts(self):
        """Initialize OpenAI TTS."""
        try:
            if OpenAI:
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    print("Initializing OpenAI TTS...")
                    self.openai_client = OpenAI(api_key=openai_key)
                    print("OpenAI TTS initialized successfully")
                else:
                    print("OpenAI API key not found")
            else:
                print("OpenAI client not available")
        except Exception as e:
            print(f"Failed to initialize OpenAI TTS: {e}")
            self.openai_client = None
    
    def create_audio(self, text):
        print(f"AudioGenerator.create_audio called with {len(text)} characters")
        print(f"OpenAI TTS available: {self.openai_client is not None}")
        print(f"Windows SAPI available: {win32com is not None}")
        
        if self.openai_client:
            print("Using OpenAI TTS")
            return self._openai_tts(text)
        elif win32com:
            print("Using Windows SAPI")
            return self._windows_sapi(text)
        else:
            print("Using fallback audio")
            return self._fallback_audio(text)
    
    def _chunk_text(self, text, max_length=4500):
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) > max_length and current_chunk:
                chunks.append(current_chunk.strip() + '.')
                current_chunk = sentence
            else:
                current_chunk += sentence + '. ' if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _openai_tts(self, text):
        """Generate audio using OpenAI TTS."""
        try:
            chunks = self._chunk_text(text, max_length=4000)  # OpenAI limit
            audio_parts = []
            
            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}: {len(chunk)} characters")
                
                # Simple retry for network issues
                for attempt in range(2):
                    try:
                        response = self.openai_client.audio.speech.create(
                            model="tts-1-hd",
                            voice="alloy",
                            input=chunk,
                            response_format="mp3"
                        )
                        
                        audio_bytes = response.content
                        audio_parts.append(audio_bytes)
                        print(f"Generated {len(audio_bytes)} bytes for chunk {i+1}")
                        break
                        
                    except Exception as e:
                        if attempt == 0:
                            print(f"Chunk {i+1} failed, retrying once: {e}")
                            import time
                            time.sleep(1)
                        else:
                            print(f"Chunk {i+1} failed permanently: {e}")
                            raise e
            
            if len(audio_parts) == 1:
                return audio_parts[0]
            
            return self._combine_audio_parts(audio_parts)
            
        except Exception as e:
            print(f"OpenAI TTS error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _combine_audio_parts(self, audio_parts):
        try:
            import tempfile
            import subprocess
            
            temp_files = []
            for i, part in enumerate(audio_parts):
                temp_file = tempfile.NamedTemporaryFile(suffix=f'_part_{i}.mp3', delete=False)
                temp_file.write(part)
                temp_file.close()
                temp_files.append(temp_file.name)
            
            output_file = tempfile.NamedTemporaryFile(suffix='_combined.mp3', delete=False)
            output_file.close()
            
            file_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            for temp_file in temp_files:
                file_list.write(f"file '{temp_file}'\n")
            file_list.close()
            
            try:
                subprocess.run([
                    'ffmpeg', '-f', 'concat', '-safe', '0', 
                    '-i', file_list.name, '-c', 'copy', output_file.name
                ], check=True, capture_output=True)
                
                with open(output_file.name, 'rb') as f:
                    combined_audio = f.read()
            except:
                combined_audio = b''.join(audio_parts)
            
            for temp_file in temp_files + [file_list.name, output_file.name]:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            return combined_audio
        except:
            return b''.join(audio_parts)
    
    def _windows_sapi(self, text):
        try:
            print("Initializing Windows SAPI...")
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            chunks = self._chunk_text(text, 800)
            print(f"Processing {len(chunks)} chunks with SAPI")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                temp_path = tmp.name
            
            file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
            file_stream.Open(temp_path, 3)
            voice.AudioOutputStream = file_stream
            
            for i, chunk in enumerate(chunks):
                print(f"Speaking chunk {i+1}/{len(chunks)}")
                voice.Speak(chunk)
            
            file_stream.Close()
            
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            print(f"Generated {len(audio_data)} bytes of audio data")
            os.unlink(temp_path)
            return audio_data
        except Exception as e:
            print(f"Windows SAPI error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fallback_audio(self, text):
        duration = min(30, max(5, len(text) // 100))
        sample_rate = 22050
        samples = duration * sample_rate
        
        audio_data = bytearray()
        for i in range(samples):
            sample = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
            audio_data.extend(struct.pack('<h', sample))
        
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + len(audio_data), b'WAVE', b'fmt ', 16,
            1, 1, sample_rate, sample_rate * 2, 2, 16, b'data', len(audio_data))
        
        return header + audio_data