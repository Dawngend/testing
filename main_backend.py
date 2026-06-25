"""
RUNTIME TERRORS: Unified Backend Controller
"""
import os
from typing import Dict, Any, List, Optional

# Import internal modules
import database as db
import extractor as ext
import rag_engine as rag
import generator as ai

# Ensure directories exist
os.makedirs("./extraction_cache", exist_ok=True)
os.makedirs("./chroma_db", exist_ok=True)

def register_user(username: str, email: str, password: str, grade_level: int) -> Dict[str, Any]:
    try:
        user = db.sign_up(email, password, username, grade_level)
        if user:
            return {"success": True, "user_id": user.id, "message": "Account created!"}
        return {"success": False, "message": "Failed to create account."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def login_user(email: str, password: str) -> Dict[str, Any]:
    try:
        user = db.sign_in(email, password)
        if user:
            profile = db.get_user_profile(user.id)
            return {"success": True, "user_id": user.id, "profile": profile}
        return {"success": False, "message": "Invalid credentials."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_user_profile(user_id: str) -> Optional[Dict]:
    return db.get_user_profile(user_id)

def upload_and_process_material(file_path: str, user_id: str, grade_level: int) -> Dict[str, Any]:
    try:
        filename = os.path.basename(file_path)
        extraction_result = ext.process_file(file_path, user_id)
        text = extraction_result['text']
        chunks = ext.chunk_text_for_rag(text)
        
        if not chunks:
            return {"success": False, "message": "No text extracted."}

        doc_id = extraction_result['metadata']['file_hash']
        rag.ingest_document(user_id, grade_level, doc_id, chunks)
        db.save_document_metadata(user_id, filename, file_path)
        
        return {"success": True, "message": "Processed!", "chunks_count": len(chunks)}
    except Exception as e:
        return {"success": False, "message": str(e)}

def ask_study_companion(user_id: str, query: str, search_online: bool = False) -> Dict[str, Any]:
    try:
        profile = db.get_user_profile(user_id)
        if not profile:
            return {"error": "User not found"}
        
        grade_level = profile.get('grade_level', 10)
        mastery_score = profile.get('mastery_score', 0.5)
        preferences = profile.get('preferences', {})
        
        context = rag.retrieve_context(user_id, grade_level, query, n_results=3)
        
        if search_online:
            web_context = web_search(query)
            if web_context:
                context += "\n\n--- ONLINE LIVE SEARCH KNOWLEDGE ---\n" + web_context
        
        response_data = ai.generate_adaptive_content(
            topic=query,
            grade_level=grade_level,
            user_mastery=mastery_score,
            context=context,
            user_preferences=preferences
        )
        
        return {"success": True, "data": response_data}
    except Exception as e:
        return {"success": False, "error": str(e)}

def web_search(query: str) -> str:
    """DuckDuckGo HTML search crawler to perform live online research (no API key needed)."""
    import requests
    import re
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            results = re.findall(r'<a class="result__snippet" href=".*?">(.*?)</a>', r.text)
            if results:
                cleaned = []
                for res in results[:3]:
                    text = re.sub(r'<[^>]*>', '', res).strip()
                    cleaned.append(text)
                return "\n".join([f"- {c}" for c in cleaned])
    except Exception as e:
        print(f"  [Warning] Web search failed: {e}")
    return ""

def generate_reviewer_deck(
    user_id: str,
    deck_name: str,
    subject: str,
    grade_level: int,
    selected_files: List[str],
    total_questions: int,
    sample_format_file: str = None
) -> Dict[str, Any]:
    """Combines study modules, extracts text, generates MCQ questions, and saves them to Supabase."""
    try:
        print(f"Starting custom deck generation for user {user_id}...")
        combined_text = ""
        
        # 1. Combine module texts
        for filename in selected_files:
            # Check temp folder first, then cache
            file_path = f"temp_{filename}"
            if not os.path.exists(file_path):
                file_path = filename # fallback
            
            res = ext.process_file(file_path, user_id)
            if res and 'text' in res:
                combined_text += f"\n\n--- Content from {filename} ---\n\n" + res['text']
                
        if len(combined_text) < 50:
            return {"success": False, "message": "Could not extract enough text from selected files."}
            
        # 2. Extract sample question formatting if provided
        sample_format_text = None
        if sample_format_file:
            res_sample = ext.process_file(sample_format_file, user_id)
            if res_sample and 'text' in res_sample:
                sample_format_text = res_sample['text']
                
        # 3. Ingest documents into ChromaDB
        chunks = ext.chunk_text_for_rag(combined_text)
        doc_id = f"deck_{deck_name.replace(' ', '_').lower()}"
        rag.ingest_document(user_id, grade_level, doc_id, chunks)
        
        # 4. Generate Deck Questions using Dual-API
        cards = ai.generate_custom_deck_cards(
            context_text=combined_text,
            subject=subject,
            deck_name=deck_name,
            total_questions=total_questions,
            sample_format_text=sample_format_text
        )
        
        if not cards:
            return {"success": False, "message": "Failed to generate any valid cards."}
            
        # 5. Insert into Supabase Table
        saved_count = 0
        for card in cards:
            success = db.add_flashcard_card(
                user_id=user_id,
                deck_name=deck_name,
                subject=subject,
                question_text=card["question"],
                options=card["options"],
                correct_answer=card["correct_answer"]
            )
            if success:
                saved_count += 1
                
        return {"success": True, "message": f"Successfully generated '{deck_name}'!", "cards_count": saved_count}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"success": False, "message": str(e)}

def get_user_decks_and_cards(user_id: str) -> Dict[str, List[Dict]]:
    return db.get_user_decks_and_cards(user_id)

def update_flashcard_review(flashcard_id: str, is_correct: bool):
    db.update_flashcard_review(flashcard_id, is_correct)

def save_flashcard_result(user_id: str, question: str, answer: str, difficulty: str, is_correct: bool):
    try:
        flashcard_id = db.add_flashcard(user_id, question, answer, difficulty)
        
        profile = db.get_user_profile(user_id)
        current_score = profile.get('mastery_score', 0.5)
        new_score = min(1.0, max(0.0, current_score + (0.05 if is_correct else -0.02)))
        
        db.update_user_mastery(user_id, new_score)
        
        if not is_correct:
            db.update_learning_pattern(user_id, "General", is_struggle=True)
        else:
            db.update_learning_pattern(user_id, "General", is_struggle=False)
            
        return {"new_mastery": new_score}
    except Exception as e:
        print(f"Error saving flashcard: {e}")
        return {"error": str(e)}

def get_user_dashboard_data(user_id: str) -> Dict[str, Any]:
    profile = db.get_user_profile(user_id)
    docs = db.get_user_documents(user_id)
    due_cards = db.get_due_flashcards(user_id)
    
    return {
        "profile": profile,
        "saved_files": docs,
        "due_flashcards_count": len(due_cards)
    }

if __name__ == "__main__":
    print("🚀 Backend Controller Ready")