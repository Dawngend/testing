import os
import json
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv(override=True)

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "qwen/qwen3.5-122b-a10b"

# Initialize Clients
client_groq = None
client_qwen = None

try:
    if GROQ_API_KEY:
        client_groq = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq Client Initialized")
    else:
        print("⚠️ Groq API Key missing")
except Exception as e:
    print(f"❌ Groq Client Error: {e}")

try:
    if NVIDIA_API_KEY:
        client_qwen = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
        print("✅ NVIDIA Qwen Client Initialized")
    else:
        print("⚠️ NVIDIA API Key missing")
except Exception as e:
    print(f"❌ NVIDIA Client Error: {e}")

# --- JSON Helper ---
def clean_and_parse_json(content: str) -> dict:
    if not content:
        return {}
    content = content.strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```"):
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
            
    # Try parsing directly
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Try finding the first '{' and last '}'
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx+1]
            try:
                return json.loads(json_str)
            except:
                pass
        raise e

# --- System Prompts ---
SYSTEM_PROMPT_TAGLISH = """
You are "Tropa", an AI Study Companion for Filipino students.
YOUR GOAL: Explain concepts clearly using natural "Taglish" (conversational Tagalog-English mix).
RULES:
1. Use English for technical terms.
2. Use Tagalog for explanations, analogies, and encouragement.
3. Do NOT use deep/archaic Tagalog.
4. Output MUST be valid JSON.
"""

SYSTEM_PROMPT_ENGLISH = """
You are "Tropa", an AI Study Companion for Filipino students.
YOUR GOAL: Explain concepts clearly using pure, clear English.
RULES:
1. Write everything in professional, easy-to-understand academic English.
2. Output MUST be valid JSON.
"""

SYSTEM_PROMPT_TAGALOG = """
You are "Tropa", an AI Study Companion for Filipino students.
YOUR GOAL: Explain concepts clearly using pure Tagalog (Filipino).
RULES:
1. Write everything in grammatical, clear Tagalog. Avoid English word usage unless there is no Tagalog equivalent.
2. Output MUST be valid JSON.
"""

def generate_adaptive_content(
    topic: str, 
    grade_level: int, 
    user_mastery: float,
    context: str = "",
    user_preferences: Dict[str, Any] = None,
    language: str = "Taglish"
) -> Dict[str, Any]:
    """
    Generates content using Groq (Llama) and NVIDIA (Qwen).
    """
    if user_preferences is None:
        user_preferences = {}
    
    difficulty = "Easy" if user_mastery < 0.4 else ("Medium" if user_mastery < 0.7 else "Hard")
    style = user_preferences.get('preferred_format', 'balanced')
    
    user_prompt = f"""
    Topic: {topic}
    Mastery: {user_mastery} ({difficulty})
    Style Preference: {style}
    Context: {context[:2000]}

    Generate a JSON object with:
    {{
        "explanation_taglish": "The explanation in the requested language style ({language})",
        "key_concepts": ["...", "..."],
        "practice_exercises": [
            {{ "question": "...", "answer": "...", "difficulty": "Easy" }},
            {{ "question": "...", "answer": "...", "difficulty": "Medium" }},
            {{ "question": "...", "answer": "...", "difficulty": "Hard" }}
        ],
        "analogy": "...",
        "motivation_quote": "..."
    }}
    """

    llama_data = {}
    qwen_data = {}
    
    # Determine the system prompt based on language
    if language == "English":
        sys_prompt = SYSTEM_PROMPT_ENGLISH
    elif language == "Tagalog":
        sys_prompt = SYSTEM_PROMPT_TAGALOG
    else:
        sys_prompt = SYSTEM_PROMPT_TAGLISH

    # 1. Call Groq
    if client_groq:
        try:
            response = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            llama_data = clean_and_parse_json(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Groq Error: {e}")

    # 2. Call NVIDIA Qwen
    if client_qwen:
        try:
            response = client_qwen.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert academic tutor. Verify the accuracy of the concept. Output MUST be valid JSON."},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1024
            )
            qwen_data = clean_and_parse_json(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ NVIDIA Error: {e}")

    # 3. Merge Results
    final_output = {
        "explanation_taglish": llama_data.get("explanation_taglish", "Error generating explanation."),
        "key_concepts": llama_data.get("key_concepts", []),
        "practice_exercises": llama_data.get("practice_exercises", []),
        "analogy": llama_data.get("analogy", "No analogy available."),
        "motivation_quote": llama_data.get("motivation_quote", "Kaya mo 'yan, Tropa!"),
        "ai_consensus_note": "Verified by Qwen." if qwen_data else ""
    }

    return final_output

def generate_custom_deck_cards(
    context_text: str,
    subject: str,
    deck_name: str,
    total_questions: int,
    sample_format_text: str = None,
    language: str = "Taglish"
) -> list:
    """
    Dual-API flashcard generation with batching (prevents token truncation) and language preferences.
    API 1 (Groq Llama 3.3) generates MCQ questions based on context.
    API 2 (NVIDIA Qwen 122B) acts as evaluator to double-check accuracy and enforce proper JSON format.
    """
    import math
    import json
    
    # We generate in small batches of 3 questions at a time to prevent JSON truncation
    batch_size = 3
    all_final_cards = []
    
    # Split text into manageable chunks
    chunk_size = 12000
    chunks = [context_text[i:i+chunk_size] for i in range(0, len(context_text), chunk_size)]
    if not chunks:
        return []
        
    total_chunks = len(chunks)
    questions_per_chunk = math.ceil(total_questions / total_chunks)
    
    # Setup language prompt instructions
    lang_instruction = ""
    if language == "English":
        lang_instruction = "You MUST write all questions, options, and explanations in pure, clear English."
    elif language == "Tagalog":
        lang_instruction = "You MUST write all questions, options, and explanations in pure Tagalog (Filipino)."
    else: # Taglish
        lang_instruction = "You MUST write all questions, options, and explanations in conversational Taglish (a natural mix of Tagalog and English, using English for technical terms and Tagalog for explanations/analogies)."
    
    for idx, chunk in enumerate(chunks, start=1):
        questions_needed = min(questions_per_chunk, total_questions - len(all_final_cards))
        if questions_needed <= 0:
            break
            
        # Loop to generate in batches of 3
        while questions_needed > 0:
            batch_count = min(batch_size, questions_needed)
            print(f"Generating batch of {batch_count} questions for chunk {idx}/{len(chunks)}...")
            
            # API 1: Generate initial questions with Groq Llama
            llama_questions = []
            if client_groq:
                prompt_api1 = f"""
                You are "Tropa", an elite CS study buddy. 
                Generate exactly {batch_count} tricky multiple-choice questions from the following module text.
                
                Subject: {subject}
                Reviewer Deck: {deck_name}
                {lang_instruction}
                
                Module Content:
                {chunk}
                
                CRITICAL REQUIREMENTS:
                1. Make the questions highly situational, practical, and scenario-based.
                2. Output a strictly formatted JSON object with a single key 'questions' containing an array of objects.
                3. Each object must have:
                   "question": "The scenario/question",
                   "options": ["Choice A", "Choice B", "Choice C", "Choice D"],
                   "correct_answer": "The correct option text exactly matching one of the options"
                """
                
                if sample_format_text:
                    prompt_api1 += f"\n4. You MUST mimic the formatting style, layout, and complexity of these sample questions:\n{sample_format_text[:1500]}\n"
                    
                try:
                    response = client_groq.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a bilingual CS professor. Explain in the requested language. Output MUST be valid JSON."},
                            {"role": "user", "content": prompt_api1}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7
                    )
                    data = clean_and_parse_json(response.choices[0].message.content)
                    llama_questions = data.get("questions", [])
                except Exception as e:
                    print(f"❌ Groq API1 generation failed: {e}")
                    
            # API 2: Verify, validate, and format check using NVIDIA Qwen
            if client_qwen and llama_questions:
                # Limit source context to 3000 chars to avoid token inflation & truncation
                short_context = chunk[:3000]
                prompt_api2 = f"""
                You are an expert academic tutor. Review the following generated multiple-choice questions.
                
                TASK:
                Verify and correct the questions for accuracy and formatting. Ensure they have exactly 4 choices in 'options', and 'correct_answer' matches one of the options exactly.
                {lang_instruction}
                
                CRITICAL REQUIREMENTS:
                1. The output MUST be a valid JSON object with a single key 'questions' containing an array of objects.
                2. Each question object MUST ONLY contain these three keys: "question", "options", "correct_answer".
                3. Do NOT add any extra fields, such as "explanation" or "concept".
                4. Do NOT output any conversational text or markdown code blocks. Start your response directly with '{{'.
                
                Source Context Reference:
                {short_context}
                
                Raw Questions to Review:
                {json.dumps(llama_questions, indent=2)}
                """
                
                try:
                    response = client_qwen.chat.completions.create(
                        model=NVIDIA_MODEL,
                        messages=[
                            {"role": "system", "content": "You are a strict JSON formatting and verification engine. You must output a single valid JSON object containing only the verified questions. Do NOT include any explanations, reasoning, or conversational text. Start your response with '{' and end with '}'."},
                            {"role": "user", "content": prompt_api2}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1,
                        max_tokens=2048
                    )
                    data = clean_and_parse_json(response.choices[0].message.content)
                    verified_questions = data.get("questions", [])
                    
                    # Basic validation
                    for card in verified_questions:
                        if all(k in card for k in ("question", "options", "correct_answer")) and len(card["options"]) == 4:
                            if card["correct_answer"] in card["options"]:
                                all_final_cards.append(card)
                except Exception as e:
                    print(f"❌ Qwen API2 evaluation failed: {e}")
                    # Fallback to API1 questions if validation fails
                    for card in llama_questions:
                        if all(k in card for k in ("question", "options", "correct_answer")) and len(card["options"]) == 4:
                            all_final_cards.append(card)
            else:
                # If Qwen client is missing, fallback to API1
                for card in llama_questions:
                    if all(k in card for k in ("question", "options", "correct_answer")) and len(card["options"]) == 4:
                        all_final_cards.append(card)
                        
            questions_needed -= batch_count
            
    # Trim to exactly requested count
    return all_final_cards[:total_questions]

def generate_focus_deck_cards(
    context_text: str,
    failed_info: str,
    subject: str,
    deck_name: str,
    total_questions: int,
    language: str = "Taglish"
) -> list:
    """
    Generates new multiple-choice questions focusing specifically on concepts from failed questions.
    """
    # Setup language prompt instructions
    lang_instruction = ""
    if language == "English":
        lang_instruction = "You MUST write all questions, options, and explanations in pure, clear English."
    elif language == "Tagalog":
        lang_instruction = "You MUST write all questions, options, and explanations in pure Tagalog (Filipino)."
    else: # Taglish
        lang_instruction = "You MUST write all questions, options, and explanations in conversational Taglish (a natural mix of Tagalog and English)."

    prompt = f"""
    You are "Tropa", an elite academic coach.
    The student struggled with the following questions in a previous quiz:
    
    {failed_info}
    
    TASK:
    Generate exactly {total_questions} NEW, DIFFERENT multiple-choice questions that target these exact weak spots or concepts. 
    Use the provided Source Context for background facts and concepts.
    
    Source Context:
    {context_text[:5000]}
    
    CRITICAL REQUIREMENTS:
    1. Do NOT repeat the failed questions verbatim. Generate fresh scenarios/situations.
    2. {lang_instruction}
    3. Output a strictly formatted JSON object with a single key 'questions' containing an array of objects.
    4. Each object must have:
       "question": "The new scenario/question",
       "options": ["Choice A", "Choice B", "Choice C", "Choice D"],
       "correct_answer": "The correct option text exactly matching one of the options"
    """
    
    # We call Groq Llama to generate, then Qwen to verify
    llama_questions = []
    if client_groq:
        try:
            response = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a bilingual academic professor. Output MUST be valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            data = clean_and_parse_json(response.choices[0].message.content)
            llama_questions = data.get("questions", [])
        except Exception as e:
            print(f"❌ Groq Focus Generation failed: {e}")
            
    all_final_cards = []
    if client_qwen and llama_questions:
        prompt_api2 = f"""
        You are an expert academic tutor. Review the following generated multiple-choice questions for accuracy.
        Ensure they have exactly 4 choices in 'options', and 'correct_answer' matches one of the options.
        {lang_instruction}
        Output MUST be valid JSON with a single key 'questions'.
        
        Raw Questions to Review:
        {json.dumps(llama_questions, indent=2)}
        """
        try:
            response = client_qwen.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": "You are a strict JSON verification engine. Output MUST be valid JSON."},
                    {"role": "user", "content": prompt_api2}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048
            )
            data = clean_and_parse_json(response.choices[0].message.content)
            verified_questions = data.get("questions", [])
            for card in verified_questions:
                if all(k in card for k in ("question", "options", "correct_answer")) and len(card["options"]) == 4:
                    if card["correct_answer"] in card["options"]:
                        all_final_cards.append(card)
        except Exception as e:
            print(f"❌ Qwen Focus Verification failed: {e}")
            for card in llama_questions:
                if all(k in card for k in ("question", "options", "correct_answer")) and len(card["options"]) == 4:
                    all_final_cards.append(card)
    else:
        for card in llama_questions:
            if all(k in card for k in ("question", "options", "correct_answer")) and len(card["options"]) == 4:
                all_final_cards.append(card)
                
    return all_final_cards[:total_questions]

if __name__ == "__main__":
    print("🧪 Testing Generator...")
    result = generate_adaptive_content("Variables", 10, 0.5, "Variables store data.")
    print(json.dumps(result, indent=2))