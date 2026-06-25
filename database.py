import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
from typing import Optional, Dict, List

# Load environment variables
load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connected")
except Exception as e:
    print(f"❌ Supabase error: {e}")
    supabase = None

def sign_up(email: str, password: str, username: str, grade_level: int = 1):
    if not supabase:
        return None
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"username": username, "grade_level": grade_level}}
        })
        return response.user
    except Exception as e:
        print(f"Signup error: {e}")
        return None

def sign_in(email: str, password: str):
    if not supabase:
        return None
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response.user
    except Exception as e:
        print(f"Login error: {e}")
        return None

def get_user_profile(user_id: str) -> Optional[Dict]:
    if not supabase:
        return None
    try:
        user_data = supabase.table("users").select("*").eq("id", user_id).execute().data
        if not user_data:
            return None

        prefs = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute().data
        user_data[0]["preferences"] = prefs[0] if prefs else {}
        return user_data[0]
    except Exception as e:
        print(f"Profile error: {e}")
        return None

def update_user_mastery(user_id: str, new_score: float):
    if supabase:
        supabase.table("users").update({"mastery_score": new_score}).eq("id", user_id).execute()

def update_learning_pattern(user_id: str, topic: str, is_struggle: bool, preferred_format: Optional[str] = None):
    if not supabase:
        return

    current = get_user_profile(user_id)
    if not current:
        return

    prefs = current.get("preferences", {})
    struggles = set(prefs.get("struggle_areas", []))
    strengths = set(prefs.get("strength_areas", []))

    if is_struggle:
        struggles.add(topic)
        strengths.discard(topic)
    else:
        strengths.add(topic)
        struggles.discard(topic)

    update_data = {
        "struggle_areas": list(struggles),
        "strength_areas": list(strengths),
        "interaction_count": (prefs.get("interaction_count") or 0) + 1,
        "last_active": datetime.utcnow().isoformat()
    }

    if preferred_format:
        update_data["preferred_format"] = preferred_format

    supabase.table("user_preferences").update(update_data).eq("id", user_id).execute()

def save_document_metadata(user_id: str, filename: str, storage_path: str):
    if supabase:
        supabase.table("documents").insert({
            "user_id": user_id,
            "filename": filename,
            "file_path": storage_path
        }).execute()

def get_user_documents(user_id: str) -> List[Dict]:
    if not supabase:
        return []
    return supabase.table("documents").select("*").eq("user_id", user_id).execute().data or []

def add_flashcard(user_id: str, question: str, answer: str, difficulty: str = "Medium") -> Optional[str]:
    if not supabase:
        return None
    data = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "difficulty": difficulty,
        "next_review_date": datetime.utcnow().isoformat()
    }
    result = supabase.table("flashcards").insert(data).execute()
    return result.data[0]["id"] if result.data else None

def get_due_flashcards(user_id: str) -> List[Dict]:
    if not supabase:
        return []
    now = datetime.utcnow().isoformat()
    result = supabase.table("flashcards").select("*").eq("user_id", user_id).lte("next_review_date", now).execute()
    return result.data or []

def add_flashcard_card(user_id: str, deck_name: str, subject: str, question_text: str, options: List[str], correct_answer: str, difficulty: str = "Medium") -> bool:
    """Inserts a new flashcard stored as JSON inside the question column."""
    if not supabase:
        return False
    
    import json
    question_data = {
        "deck_name": deck_name,
        "subject": subject,
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer
    }
    
    data = {
        "user_id": user_id,
        "question": json.dumps(question_data),
        "answer": correct_answer,
        "difficulty": difficulty,
        "next_review_date": datetime.utcnow().isoformat()
    }
    try:
        response = supabase.table("flashcards").insert(data).execute()
        return response.data is not None
    except Exception as e:
        print(f"Error adding card: {e}")
        return False

def get_user_decks_and_cards(user_id: str) -> Dict[str, List[Dict]]:
    """Fetches all flashcards from Supabase and groups them by deck_name."""
    if not supabase:
        return {}
    
    import json
    try:
        response = supabase.table("flashcards").select("*").eq("user_id", user_id).execute()
        cards_by_deck = {}
        for row in (response.data or []):
            q_text = row.get("question", "")
            try:
                q_data = json.loads(q_text)
                if isinstance(q_data, dict) and "deck_name" in q_data:
                    deck = q_data["deck_name"]
                    card = {
                        "id": row["id"],
                        "deck_name": deck,
                        "subject": q_data.get("subject", "General"),
                        "question": q_data.get("question_text", ""),
                        "options": q_data.get("options", []),
                        "correct_answer": q_data.get("correct_answer", ""),
                        "difficulty": row.get("difficulty", "Medium"),
                        "next_review_date": row.get("next_review_date")
                    }
                    if deck not in cards_by_deck:
                        cards_by_deck[deck] = []
                    cards_by_deck[deck].append(card)
            except json.JSONDecodeError:
                # Fallback to standard card
                deck = "General Flashcards"
                card = {
                    "id": row["id"],
                    "deck_name": deck,
                    "subject": "General",
                    "question": q_text,
                    "options": [],
                    "correct_answer": row.get("answer", ""),
                    "difficulty": row.get("difficulty", "Medium"),
                    "next_review_date": row.get("next_review_date")
                }
                if deck not in cards_by_deck:
                    cards_by_deck[deck] = []
                cards_by_deck[deck].append(card)
        return cards_by_deck
    except Exception as e:
        print(f"Error getting decks: {e}")
        return {}

def update_flashcard_review(flashcard_id: str, is_correct: bool):
    """Updates spaced repetition next review date based on correct/wrong attempts."""
    if not supabase:
        return
    try:
        res = supabase.table("flashcards").select("streak").eq("id", flashcard_id).execute()
        if res.data:
            current_streak = res.data[0].get("streak") or 0
            new_streak = current_streak + 1 if is_correct else 0
            
            days_to_add = 1
            if is_correct:
                days_to_add = min(365, 2 ** new_streak) # limit to 1 year max
                
            from datetime import timedelta
            next_date = (datetime.utcnow() + timedelta(days=days_to_add)).isoformat()
            
            supabase.table("flashcards").update({
                "streak": new_streak,
                "next_review_date": next_date
            }).eq("id", flashcard_id).execute()
    except Exception as e:
        print(f"Error updating card: {e}")

if __name__ == "__main__":
    print("Database module ready")