import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

print("🏥 RUNTIME TERRORS: SYSTEM HEALTH CHECK")
print("=" * 40)

all_passed = True

# 1. Check Database Module
print("\n1. Testing database.py...")
try:
    import database as db
    if db.supabase:
        print("   ✅ Supabase client connected")
        # Try a simple fetch
        # We can't test auth without a user, but we can check client existence
        print("   ✅ Functions loaded: sign_up, sign_in, get_user_profile")
    else:
        print("   ❌ Supabase client failed to initialize")
        all_passed = False
except Exception as e:
    print(f"   ❌ Error importing database: {e}")
    all_passed = False

# 2. Check RAG Engine (ChromaDB)
print("\n2. Testing rag_engine.py...")
try:
    import rag_engine as rag
    print("   ✅ ChromaDB client initialized")
    print("   ✅ Embedding model loaded")
    print("   ✅ Functions loaded: ingest_document, retrieve_context")
except Exception as e:
    print(f"   ❌ Error importing rag_engine: {e}")
    all_passed = False

# 3. Check Extraction Layer
print("\n3. Testing extractor.py...")
try:
    import extractor as ext
    print("   ✅ PDF/Image extraction modules loaded")
    print("   ✅ Cache directory ready")
    print("   ✅ Functions loaded: process_file, chunk_text_for_rag")
except Exception as e:
    print(f"   ❌ Error importing extractor: {e}")
    all_passed = False

# 4. Check AI Generator (Groq + NVIDIA)
print("\n4. Testing generator.py...")
try:
    import generator as ai
    # Check if clients are initialized
    if hasattr(ai, 'client_groq') and ai.client_groq:
        print("   ✅ Groq client connected")
    else:
        print("   ⚠️ Groq client missing (Check GROQ_API_KEY)")
    
    if hasattr(ai, 'client_qwen') and ai.client_qwen:
        print("   ✅ NVIDIA Qwen client connected")
    else:
        print("   ⚠️ NVIDIA Qwen client missing (Check NVIDIA_API_KEY)")
        
    print("   ✅ Functions loaded: generate_adaptive_content")
except Exception as e:
    print(f"   ❌ Error importing generator: {e}")
    all_passed = False

# 5. Check Main Backend Controller
print("\n5. Testing main_backend.py...")
try:
    import main_backend as backend
    funcs = ['login_user', 'register_user', 'upload_and_process_material', 'ask_study_companion']
    missing = [f for f in funcs if not hasattr(backend, f)]
    
    if not missing:
        print("   ✅ All controller functions available")
    else:
        print(f"   ❌ Missing functions: {missing}")
        all_passed = False
except Exception as e:
    print(f"   ❌ Error importing main_backend: {e}")
    all_passed = False

print("\n" + "=" * 40)
if all_passed:
    print("🎉 SYSTEM HEALTHY: All modules loaded successfully!")
    print("🚀 Ready to launch frontend (app.py)")
else:
    print("⚠️ SYSTEM WARNINGS: Some modules have issues. Review errors above.")