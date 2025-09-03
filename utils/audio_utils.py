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
    
    def _google_tts(self, text):
        try:
            if len(text) > 5000:
                text = text[:5000]
            
            tts = gTTS(text=text, lang='en', slow=False)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            return buffer.read()
        except:
            return None
    
    def _windows_sapi(self, text):
        try:
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                temp_path = tmp.name
            
            file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
            file_stream.Open(temp_path, 3)
            voice.AudioOutputStream = file_stream
            voice.Speak(text[:1000])
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