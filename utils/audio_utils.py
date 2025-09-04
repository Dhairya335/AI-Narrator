import os
import io
import math
import struct
import tempfile

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None

try:
    import win32com.client
except ImportError:
    win32com = None

class AudioGenerator:
    def __init__(self):
        self.speech_key = os.getenv('AZURE_SPEECH_KEY')
        self.speech_region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
    
    def create_audio(self, text):
        if speechsdk and self.speech_key:
            return self._azure_speech(text)
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
    
    def _azure_speech(self, text):
        try:
            speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.speech_region)
            
            # Use Azure's most natural voice with vibevoice AI
            speech_config.speech_synthesis_voice_name = "en-US-AvaMultilingualNeural"
            speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
            
            # Enable vibevoice AI features for more natural speech
            speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_SynthEnableCompressedAudioTransmission, "true")
            
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
            
            # Use SSML for better control over speech synthesis
            ssml = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="en-US-AvaMultilingualNeural">
                    <prosody rate="0.9" pitch="+2Hz">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            else:
                print(f"Azure Speech synthesis failed: {result.reason}")
                return None
        except Exception as e:
            print(f"Azure Speech error: {e}")
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