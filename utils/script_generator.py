from openai import OpenAI
from .content_analyzer import detect_content_type, calculate_podcast_length, chunk_content


class ScriptGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
    
    def create_podcast_script(self, text):
        """Generate podcast script from text content."""
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
            "short": "Create a comprehensive podcast covering all important aspects.",
            "medium": "Create a detailed podcast with thorough analysis and context.",
            "long": "Create an in-depth podcast covering all major aspects comprehensively.",
            "extended": "Create a comprehensive, detailed podcast with thorough exploration of all aspects."
        }
        
        content_instructions = {
            'research': "Explain the research methodology, findings, and implications in accessible terms.",
            'news': "Present facts, provide context, and analyze broader implications.",
            'tutorial': "Walk through concepts step-by-step with clear explanations.",
            'general': "Extract key insights and explain their significance."
        }
        
        chunks = chunk_content(text)
        
        if len(chunks) == 1:
            return self._generate_single_script(
                chunks[0], system_prompt, structure_prompt, 
                length_instructions[podcast_length],
                content_instructions.get(content_type, content_instructions['general']),
                max_tokens
            )
        else:
            return self._generate_multi_chunk_script(
                chunks, system_prompt, structure_prompt,
                length_instructions[podcast_length],
                content_instructions.get(content_type, content_instructions['general']),
                max_tokens
            )
    
    def _generate_single_script(self, content, system_prompt, structure_prompt, length_instruction, content_instruction, max_tokens):
        """Generate script for single chunk of content."""
        full_prompt = (
            f"{length_instruction} "
            f"{content_instruction}\n\n"
            f"{structure_prompt}\n\n"
            f"Content: {content}"
        )
        
        try:
            print(f"Making API call with {len(full_prompt)} character prompt...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
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
    
    def _generate_multi_chunk_script(self, chunks, system_prompt, structure_prompt, length_instruction, content_instruction, max_tokens):
        """Generate script for multiple chunks of content."""
        scripts = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = (
                f"Part {i+1} of {len(chunks)}. {length_instruction} "
                f"{content_instruction}\n\n"
                f"{structure_prompt}\n\n"
                f"Content: {chunk}"
            )
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
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
            return self._combine_scripts(scripts, max_tokens)
        
        return None
    
    def _combine_scripts(self, scripts, max_tokens):
        """Combine multiple script segments into one cohesive script."""
        final_prompt = (
            f"Combine these podcast segments into one cohesive script. "
            f"Ensure smooth transitions and natural flow:\n\n" +
            "\n\n--- SEGMENT BREAK ---\n\n".join(scripts)
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
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