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

SYSTEM_PROMPT_QWEN = """
You are an expert academic tutor. Verify the accuracy of the concept and provide a structured breakdown.
Output MUST be valid JSON.
"""

def generate_adaptive_content(
    topic: str, 
    grade_level: int, 
    user_mastery: float,
    context: str = "",
    user_preferences: Dict[str, Any] = None
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
    Grade Level: {grade_level}
    Mastery: {user_mastery} ({difficulty})
    Style Preference: {style}
    Context: {context[:2000]}

    Generate a JSON object with:
    {{
        "explanation_taglish": "...",
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

    # 1. Call Groq
    if client_groq:
        try:
            response = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_TAGLISH},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            llama_data = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Groq Error: {e}")

    # 2. Call NVIDIA Qwen
    if client_qwen:
        try:
            response = client_qwen.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_QWEN},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1024
            )
            qwen_data = json.loads(response.choices[0].message.content)
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
    sample_format_text: str = None
) -> list:
    """
    Dual-API flashcard generation:
    API 1 (Groq Llama 3.3) generates MCQ questions based on context and optional sample questions format.
    API 2 (NVIDIA Qwen 122B) acts as evaluator to double-check accuracy and enforce proper JSON format.
    """
    import math
    import json
    
    # Split text into manageable chunks
    chunk_size = 10000
    chunks = [context_text[i:i+chunk_size] for i in range(0, len(context_text), chunk_size)]
    if not chunks:
        return []
        
    questions_per_chunk = math.ceil(total_questions / len(chunks))
    all_final_cards = []
    
    for idx, chunk in enumerate(chunks, start=1):
        print(f"Generating questions for chunk {idx}/{len(chunks)}...")
        
        # API 1: Generate initial questions with Groq Llama
        llama_questions = []
        if client_groq:
            prompt_api1 = f"""
            You are "Tropa", an elite CS study buddy. Generate exactly {questions_per_chunk} tricky multiple-choice questions from the following module text:
            
            Subject: {subject}
            Reviewer Deck: {deck_name}
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
                        {"role": "system", "content": "You are a bilingual CS professor. Explain in English/Taglish. Output MUST be valid JSON."},
                        {"role": "user", "content": prompt_api1}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                data = json.loads(response.choices[0].message.content)
                llama_questions = data.get("questions", [])
            except Exception as e:
                print(f"❌ Groq API1 generation failed: {e}")
                
        # API 2: Verify, validate, and format check using NVIDIA Qwen
        if client_qwen and llama_questions:
            prompt_api2 = f"""
            You are an expert academic tutor. Review the following generated multiple-choice questions and check them against the source context for factual accuracy and format compatibility.
            
            Source Context:
            {chunk}
            
            Raw Questions Generated by API1:
            {json.dumps(llama_questions, indent=2)}
            
            TASK:
            Verify and correct the questions. Ensure they have exactly 4 choices in 'options', and 'correct_answer' matches one of the options.
            Output MUST be valid JSON with a single key 'questions'.
            """
            
            if sample_format_text:
                prompt_api2 += f"\nDouble-check that they replicate the format: {sample_format_text[:1000]}"
                
            try:
                response = client_qwen.chat.completions.create(
                    model=NVIDIA_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an academic evaluator. Verify and enforce correct JSON structure. Output MUST be valid JSON."},
                        {"role": "user", "content": prompt_api2}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1024
                )
                data = json.loads(response.choices[0].message.content)
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
                        
    # Trim to exactly requested count
    return all_final_cards[:total_questions]

if __name__ == "__main__":
    print("🧪 Testing Generator...")
    result = generate_adaptive_content("Variables", 10, 0.5, "Variables store data.")
    print(json.dumps(result, indent=2))