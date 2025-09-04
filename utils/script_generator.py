import anthropic
from .content_analyzer import detect_content_type, calculate_podcast_length, chunk_content, chunk_large_document


class ScriptGenerator:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def create_podcast_script(self, text):
        """Generate podcast script from text content."""
        print(f"create_podcast_script called with {len(text) if text else 0} characters")
        
        if not text or len(text.strip()) < 50:
            print("Text too short, returning None")
            return None
        
        content_type = detect_content_type(text)
        print(f"Content type: {content_type}, Content length: {len(text)} characters")
        
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
            "short": "Create a comprehensive podcast covering all important aspects within 5 minutes.",
            "medium": "Create a detailed podcast with thorough analysis and context, approximately 8-10 minutes long.",
            "long": "Create an in-depth podcast covering all major aspects comprehensively, around 15-20 minutes.",
            "extended": "Create a comprehensive, detailed podcast with thorough exploration of all aspects, lasting 30 minutes or more.",
            "comprehensive": "Create an extensive, highly detailed podcast with deep analysis of all aspects, complex topics, and nuanced discussions, lasting 45+ minutes."
        }
        
        content_instructions = {
            'research': "Explain the research methodology, findings, and implications in accessible terms.",
            'news': "Present facts, provide context, and analyze broader implications.",
            'tutorial': "Walk through concepts step-by-step with clear explanations.",
            'general': "Extract key insights and explain their significance."
        }
        
        # Generate script directly without chunking - let Claude handle the full content
        return self._generate_single_script(
            text, system_prompt, structure_prompt,
            "Create an extensive, comprehensive podcast with deep analysis covering all aspects, lasting as long as needed to thoroughly explore the content.",
            content_instructions.get(content_type, content_instructions['general'])
        )
    
    def _generate_single_script(self, content, system_prompt, structure_prompt, length_instruction, content_instruction):
        """Generate script for single chunk of content."""
        full_prompt = (
            f"{length_instruction} "
            f"{content_instruction}\n\n"
            f"{structure_prompt}\n\n"
            f"Content: {content}"
        )
        
        try:
            print(f"Making API call with {len(full_prompt)} character prompt...")
            print("Using streaming to avoid timeout...")
            
            stream = self.client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=32000,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                stream=True
            )
            
            content = ""
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    content += chunk.delta.text
            print("Streaming API call successful")
            return content.strip()
        except Exception as e:
            print(f"Anthropic API Error: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return None
    
