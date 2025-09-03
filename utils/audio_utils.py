import os
import io
import math
import struct
import tempfile

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import win32com.client
except ImportError:
    win32com = None

class AudioGenerator:
    def create_audio(self, text):
        if gTTS:
            return self._google_tts(text)
        elif win32com:
            return self._windows_sapi(text)
        else:
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
    
    def _google_tts(self, text):
        try:
            chunks = self._chunk_text(text)
            audio_parts = []
            
            for chunk in chunks:
                tts = gTTS(text=chunk, lang='en', slow=False)
                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)
                audio_parts.append(buffer.read())
            
            if len(audio_parts) == 1:
                return audio_parts[0]
            
            return self._combine_audio_parts(audio_parts)
        except:
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
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            chunks = self._chunk_text(text, 800)
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                temp_path = tmp.name
            
            file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
            file_stream.Open(temp_path, 3)
            voice.AudioOutputStream = file_stream
            
            for chunk in chunks:
                voice.Speak(chunk)
            
            file_stream.Close()
            
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(temp_path)
            return audio_data
        except:
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