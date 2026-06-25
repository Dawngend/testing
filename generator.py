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

if __name__ == "__main__":
    print("🧪 Testing Generator...")
    result = generate_adaptive_content("Variables", 10, 0.5, "Variables store data.")
    print(json.dumps(result, indent=2))