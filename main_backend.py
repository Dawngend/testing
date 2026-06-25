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

def ask_study_companion(user_id: str, query: str) -> Dict[str, Any]:
    try:
        profile = db.get_user_profile(user_id)
        if not profile:
            return {"error": "User not found"}
        
        grade_level = profile.get('grade_level', 10)
        mastery_score = profile.get('mastery_score', 0.5)
        preferences = profile.get('preferences', {})
        
        context = rag.retrieve_context(user_id, grade_level, query, n_results=3)
        
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

def save_flashcard_result(user_id: str, question: str, answer: str, difficulty: str, is_correct: bool):
    try:
        flashcard_id = db.add_flashcard(user_id, question, answer, difficulty)
        
        profile = db.get_user_profile(user_id)
        current_score = profile.get('mastery_score', 0.5)
        new_score = min(1.0, max(0.0, current_score + (0.05 if is_correct else -0.02)))
        
        db.update_user_mastery(user_id, new_score)
        
        # Update learning pattern
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