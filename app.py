import streamlit as st
import os
import sys
import random
import json
import traceback
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Ensure env is loaded with override
load_dotenv(override=True)

# 1. IMPORT BACKEND MODULES
try:
    import main_backend as backend
    import database as db
except Exception as e:
    st.error(f"❌ CRITICAL ERROR: Could not import backend modules.")
    st.error(f"Error Details: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

# 2. PAGE CONFIGURATION
st.set_page_config(page_title="Tropa: AI Study Companion", page_icon="🇵🇭", layout="centered")

# 3. PREMIUM DARK NAVY & CREAM THEME STYLE INJECTION
st.markdown("""
    <style>
    /* Force main background to dark navy */
    .stApp {
        background-color: #0D1B2A !important; 
        color: #FDFDF9 !important;
    }
    
    /* Centralize content block */
    .main .block-container {
        max-width: 750px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }

    /* Cream Card styling for questions and metrics */
    .quiz-card {
        background-color: #FDFDF9 !important;
        color: #1A365D !important;
        padding: 25px !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4) !important;
        margin-bottom: 20px !important;
        border-top: 5px solid #2B6CB0;
    }
    
    .quiz-card h3 {
        color: #1A365D !important;
        font-weight: 700 !important;
        margin-top: 0px !important;
        margin-bottom: 8px !important;
    }
    .quiz-card p {
        font-size: 1.1rem !important;
        color: #334155 !important;
        margin-bottom: 0px !important;
    }

    /* Input label styling for Dark Mode visibility */
    label, .stMarkdown p {
        color: #E2E8F0 !important;
    }

    /* Custom layout for options/buttons */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        background-color: #1E293B; 
        color: #FDFDF9;
        font-weight: 600;
        border: 2px solid transparent;
        transition: all 0.2s ease-in-out;
        padding: 10px;
    }
    div.stButton > button:hover {
        border: 2px solid #2B6CB0;
        background-color: #0D1B2A;
    }
    
    /* Highlight correct options in green/blue */
    div.stButton > button[kind="primary"] {
        background-color: #2B6CB0 !important;
        color: #FDFDF9 !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1A365D !important;
    }

    /* Remove Streamlit default header/footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 4. SESSION STATE INITIALIZATION
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'cards_queue' not in st.session_state:
    st.session_state.cards_queue = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'wrong_attempts_on_card' not in st.session_state:
    st.session_state.wrong_attempts_on_card = set()
if 'failed_cards_pool' not in st.session_state:
    st.session_state.failed_cards_pool = []
if 'answered_correctly' not in st.session_state:
    st.session_state.answered_correctly = False
if 'active_deck_name' not in st.session_state:
    st.session_state.active_deck_name = None
if 'active_deck_subject' not in st.session_state:
    st.session_state.active_deck_subject = None

# Helper directory setup (Resolved absolutely)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file) -> str:
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# =============================================================================
# SCREEN A: LOGIN & SIGN UP
# =============================================================================
def login_screen():
    st.markdown("<h1 style='text-align: center; color: #FDFDF9; margin-bottom: 2rem;'>🇵🇭 Tropa: Study Companion</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Welcome Back, Tropa!")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In", type="primary", use_container_width=True):
            if not email or not password:
                st.warning("Please fill out your credentials.")
            else:
                with st.spinner("Logging in..."):
                    result = backend.login_user(email, password)
                    if result and result.get('success'):
                        st.session_state.user_id = result['user_id']
                        st.session_state.profile = result['profile']
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result.get('message', 'Invalid credentials.')}")

    with tab2:
        st.subheader("Create a New Account")
        username = st.text_input("Username", key="reg_user")
        email = st.text_input("Email Address", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("Sign Up", type="primary", use_container_width=True):
            if not all([username, email, password]):
                st.warning("Please fill all required fields.")
            else:
                with st.spinner("Creating account..."):
                    # Pass a default grade level of 10 to keep db triggers happy
                    result = backend.register_user(username, email, password, 10)
                    if result and result.get('success'):
                        st.success("Account created successfully! Please login using the Login tab.")
                    else:
                        st.error(f"Signup failed: {result.get('message', 'Failed to register.')}")

# =============================================================================
# SCREEN B: MAIN APP DASHBOARD
# =============================================================================
def dashboard():
    username = st.session_state.profile.get('username', 'Tropa')
    mastery = st.session_state.profile.get('mastery_score', 0.0)
    
    # Sidebar navigation
    st.sidebar.title(f"👋 Kumusta, {username}!")
    st.sidebar.metric("🏆 Mastery Score", f"{mastery:.1%}")
    
    st.sidebar.divider()
    app_mode = st.sidebar.radio("Navigate Menu", [
        "📚 Study Dojo", 
        "✨ Create Reviewer", 
        "📁 Saved Files", 
        "💬 AI Tutor Chat"
    ])
    
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Companion Settings")
    st.sidebar.selectbox("🗣️ Language Style", ["Taglish", "English", "Tagalog"], key="global_lang_pref")
    
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.profile = None
        st.session_state.quiz_started = False
        st.session_state.cards_queue = []
        st.rerun()
        
    # -------------------------------------------------------------------------
    # MODE 1: STUDY DOJO (FLASHCARDS/QUIZ)
    # -------------------------------------------------------------------------
    if app_mode == "📚 Study Dojo":
        st.markdown("<h2 style='color: #FDFDF9;'>📚 Reviewer Dojo</h2>", unsafe_allow_html=True)
        
        # Load Decks from Supabase
        decks_and_cards = backend.get_user_decks_and_cards(st.session_state.user_id)
        
        if not decks_and_cards:
            st.info("No study reviewers found. Head over to **✨ Create Reviewer** to generate questions from your modules!")
        else:
            deck_names = list(decks_and_cards.keys())
            selected_deck = st.selectbox("Select a Study Reviewer:", deck_names)
            
            # Display the subject name
            deck_subject = decks_and_cards[selected_deck][0].get("subject", "General")
            st.markdown(f"📖 **Subject Category**: `{deck_subject}`")
            
            if st.button("Start Quiz Session 🚀", type="primary"):
                deck_cards = decks_and_cards[selected_deck]
                random.shuffle(deck_cards)
                
                st.session_state.cards_queue = deck_cards
                st.session_state.current_index = 0
                st.session_state.wrong_attempts_on_card = set()
                st.session_state.failed_cards_pool = []
                st.session_state.answered_correctly = False
                st.session_state.active_deck_name = selected_deck
                st.session_state.active_deck_subject = deck_cards[0].get("subject", "General")
                st.session_state.quiz_started = True
                st.rerun()
                
        # Main Quiz Session loop
        if st.session_state.quiz_started and st.session_state.current_index < len(st.session_state.cards_queue):
            current_card = st.session_state.cards_queue[st.session_state.current_index]
            total_cards = len(st.session_state.cards_queue)
            
            # Progress bar
            progress_value = st.session_state.current_index / total_cards
            st.progress(progress_value)
            st.write(f"Question {st.session_state.current_index + 1} of {total_cards}")
            
            # Display the subject
            st.markdown(f"📖 **Subject**: `{st.session_state.active_deck_subject}`")
            
            # Question Card
            st.markdown(f"""
                <div class="quiz-card">
                    <h3>🤖 Tropa AI Companion:</h3>
                    <p style="font-weight: 500;">{current_card["question"]}</p>
                </div>
            """, unsafe_allow_html=True)
            
            options = current_card["options"]
            correct = current_card["correct_answer"]
            
            # Option buttons
            if not st.session_state.answered_correctly:
                cols = st.columns(2)
                for i, option in enumerate(options):
                    col_choice = cols[i % 2]
                    with col_choice:
                        if option in st.session_state.wrong_attempts_on_card:
                            st.button(f"❌ {option}", key=f"opt_{st.session_state.current_index}_{i}", disabled=True)
                        else:
                            if st.button(option, key=f"opt_{st.session_state.current_index}_{i}"):
                                if option == correct:
                                    st.session_state.answered_correctly = True
                                    # Update database spaced repetition log
                                    backend.update_flashcard_review(st.session_state.user_id, current_card["id"], is_correct=True)
                                    # Update local state for immediate feedback
                                    if st.session_state.profile:
                                        cur = st.session_state.profile.get('mastery_score', 0.0) or 0.0
                                        st.session_state.profile['mastery_score'] = min(1.0, cur + 0.05)
                                    st.rerun()
                                else:
                                    st.session_state.wrong_attempts_on_card.add(option)
                                    if current_card not in st.session_state.failed_cards_pool:
                                        st.session_state.failed_cards_pool.append(current_card)
                                        backend.update_flashcard_review(st.session_state.user_id, current_card["id"], is_correct=False)
                                        # Update local state for immediate feedback
                                        if st.session_state.profile:
                                            cur = st.session_state.profile.get('mastery_score', 0.0) or 0.0
                                            st.session_state.profile['mastery_score'] = max(0.0, cur - 0.02)
                                    st.rerun()
            else:
                # Correct choice selected review screen
                cols = st.columns(2)
                for i, option in enumerate(options):
                    col_choice = cols[i % 2]
                    with col_choice:
                        if option == correct:
                            st.button(f"✅ {option}", key=f"opt_{st.session_state.current_index}_{i}", type="primary", disabled=True)
                        else:
                            st.button(option, key=f"opt_{st.session_state.current_index}_{i}", disabled=True)
                            
                st.success("🎯 Tama ang sagot mo! Great job, Tropa!")
                
                # Next Question button
                if st.button("Next Scenario ➡️", type="primary"):
                    st.session_state.current_index += 1
                    st.session_state.wrong_attempts_on_card.clear()
                    st.session_state.answered_correctly = False
                    st.rerun()
                    
        elif st.session_state.quiz_started:
            # Round cleared
            st.balloons()
            st.markdown("""
                <div class="quiz-card" style="text-align: center;">
                    <h3>🏁 Dojo Round Cleared!</h3>
                    <p>Excellent effort. You have finished reviewing all cards in this session.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Show missed count
            missed_count = len(st.session_state.failed_cards_pool)
            if missed_count > 0:
                st.warning(f"⚠️ You missed {missed_count} question(s) on the first attempt in this session.")
            else:
                st.success("🎉 Perfect score on first attempt! You aced this deck!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Reflash Entire Deck"):
                    deck_cards = decks_and_cards.get(st.session_state.active_deck_name, [])
                    if deck_cards:
                        random.shuffle(deck_cards)
                        st.session_state.cards_queue = deck_cards
                    st.session_state.current_index = 0
                    st.session_state.wrong_attempts_on_card.clear()
                    st.session_state.failed_cards_pool = []
                    st.session_state.answered_correctly = False
                    st.rerun()
            with col2:
                if st.button("❌ Reflash Missed Questions", disabled=(missed_count == 0)):
                    st.session_state.cards_queue = list(st.session_state.failed_cards_pool)
                    random.shuffle(st.session_state.cards_queue)
                    st.session_state.current_index = 0
                    st.session_state.wrong_attempts_on_card.clear()
                    st.session_state.failed_cards_pool = []
                    st.session_state.answered_correctly = False
                    st.rerun()
            with col3:
                if st.button("🧠 Generate Focus Set", disabled=(missed_count == 0)):
                    with st.spinner("Generating new questions based on your mistakes..."):
                        g_lang = st.session_state.get("global_lang_pref", "Taglish")
                        res = backend.generate_focus_deck(
                            user_id=st.session_state.user_id,
                            deck_name=st.session_state.active_deck_name,
                            subject=st.session_state.active_deck_subject,
                            failed_questions=st.session_state.failed_cards_pool,
                            total_questions=max(3, len(st.session_state.failed_cards_pool)),
                            language=g_lang
                        )
                        if res and res.get("success"):
                            st.success(f"Successfully created focus deck: '{res['deck_name']}'!")
                            st.session_state.quiz_started = False
                            st.rerun()
                        else:
                            st.error(f"Failed to generate focus set: {res.get('message', 'AI error')}")

    # -------------------------------------------------------------------------
    # MODE 2: CREATE REVIEWER
    # -------------------------------------------------------------------------
    elif app_mode == "✨ Create Reviewer":
        st.markdown("<h2 style='color: #FDFDF9;'>✨ Craft a New Reviewer</h2>", unsafe_allow_html=True)
        
        # Part 1: Upload Study Modules
        st.markdown("""
            <div class="quiz-card">
                <h3>1. Upload Study Materials</h3>
                <p>Upload the PDF/PPTX chapters or notes that you want to study.</p>
            </div>
        """, unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Upload Modules", type=['pdf', 'pptx'], accept_multiple_files=True, label_visibility="collapsed")
        
        saved_paths = []
        if uploaded_files:
            for file in uploaded_files:
                path = save_uploaded_file(file)
                saved_paths.append(file.name)
            st.success(f"Uploaded {len(uploaded_files)} file(s)!")
            
        # Part 2: Upload Sample Formatting Questions (Format-Mimicking Upload Engine)
        st.markdown("""
            <div class="quiz-card" style="margin-top: 1.5rem;">
                <h3>2. Upload Sample Exam format (Optional)</h3>
                <p>Upload a file containing sample questions. Tropa will copy its exact layout, difficulty, and question style.</p>
            </div>
        """, unsafe_allow_html=True)
        sample_file = st.file_uploader("Upload Sample Questions Format", type=['pdf', 'pptx', 'txt'], label_visibility="collapsed")
        
        sample_path = None
        if sample_file:
            sample_path = save_uploaded_file(sample_file)
            st.success(f"Sample formatting loaded: {sample_file.name}")
            
        # Part 3: Configure deck generation
        st.markdown("""
            <div class="quiz-card" style="margin-top: 1.5rem;">
                <h3>3. Reviewer Configuration</h3>
                <p>Specify name, subject, and size of the reviewer dojo.</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("custom_reviewer_form"):
            deck_name = st.text_input("Reviewer Title (e.g. Midterm Unit 2)")
            subject_name = st.text_input("Subject Category (e.g. Philippine History)")
            
            # Select Language preference dropdown synced with global preference
            g_lang = st.session_state.get("global_lang_pref", "Taglish")
            g_index = ["Taglish", "English", "Tagalog"].index(g_lang) if g_lang in ["Taglish", "English", "Tagalog"] else 0
            language_pref = st.selectbox("Language Preference", ["Taglish", "English", "Tagalog"], index=g_index)
            
            num_questions = st.number_input("Total Questions to Generate", 3, 50, 10, step=1)
            
            submit = st.form_submit_button("Generate Reviewer Dojo 🚀", type="primary")
            
            if submit:
                if not saved_paths:
                    st.error("Please upload at least one study module PDF/PPTX first!")
                elif not deck_name or not subject_name:
                    st.error("Please provide a Reviewer Title and Subject Category.")
                else:
                    with st.spinner("Tropa is reading, digesting, and validating questions..."):
                        # Save document metadata first in Supabase
                        for fname in saved_paths:
                            db.save_document_metadata(st.session_state.user_id, fname, os.path.join(UPLOAD_DIR, fname))
                            
                        # Call generation
                        res = backend.generate_reviewer_deck(
                            user_id=st.session_state.user_id,
                            deck_name=deck_name,
                            subject=subject_name,
                            selected_files=saved_paths,
                            total_questions=num_questions,
                            sample_format_file=sample_path,
                            language=language_pref
                        )
                        
                        if res and res.get("success"):
                            st.success(f"Successfully created '{deck_name}' deck with {res.get('cards_count', 0)} cards!")
                            st.balloons()
                        else:
                            st.error(f"Failed to generate deck: {res.get('message', 'AI model error')}")

    # -------------------------------------------------------------------------
    # MODE 3: SAVED FILES
    # -------------------------------------------------------------------------
    elif app_mode == "📁 Saved Files":
        st.markdown("<h2 style='color: #FDFDF9;'>📁 Your Saved Files</h2>", unsafe_allow_html=True)
        st.write("Below are the modules uploaded to your companion cache. Files expire and are removed **4 days** after upload.")
        
        # Load user documents
        docs = db.get_user_documents(st.session_state.user_id)
        
        if not docs:
            st.info("You haven't uploaded any study files yet.")
        else:
            active_docs = []
            for doc in docs:
                uploaded_at_str = doc.get("uploaded_at") or doc.get("created_at")
                if uploaded_at_str:
                    try:
                        uploaded_at = datetime.fromisoformat(uploaded_at_str.replace("Z", "+00:00"))
                        age = datetime.now(timezone.utc) - uploaded_at
                        if age < timedelta(days=4):
                            # Calculate time left
                            time_left = timedelta(days=4) - age
                            hours_left = int(time_left.total_seconds() // 3600)
                            minutes_left = int((time_left.total_seconds() % 3600) // 60)
                            doc["expires_in"] = f"{hours_left}h {minutes_left}m"
                            active_docs.append(doc)
                    except:
                        doc["expires_in"] = "Active"
                        active_docs.append(doc)
                else:
                    doc["expires_in"] = "Active"
                    active_docs.append(doc)
            
            if not active_docs:
                st.warning("All your uploaded documents have expired (older than 4 days). Please upload them again.")
            else:
                for doc in active_docs:
                    st.markdown(f"""
                        <div class="quiz-card">
                            <h3>📄 {doc['filename']}</h3>
                            <p style="color: #64748B !important; font-size: 0.9rem;">
                                📅 <b>Uploaded</b>: {doc.get('uploaded_at', 'Unknown')[:10]} | ⏱️ <b>Cache Expires In</b>: {doc.get('expires_in')}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # MODE 4: AI TUTOR CHAT
    # -------------------------------------------------------------------------
    elif app_mode == "💬 AI Tutor Chat":
        st.markdown("<h2 style='color: #FDFDF9;'>💬 Tropa AI Tutor Chat</h2>", unsafe_allow_html=True)
        st.write("Ask your companion questions about modules or general study help.")
        
        # Option for web search
        search_online = st.checkbox("🌐 Search Online for Credible Sources")
        
        st.divider()
        
        # Display chat history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg['role']):
                st.write(msg['content'])
                
        # Input block
        if prompt := st.chat_input("Ask a question, Tropa..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Thinking (Nag-iisip)..."):
                    g_lang = st.session_state.get("global_lang_pref", "Taglish")
                    res = backend.ask_study_companion(st.session_state.user_id, prompt, search_online=search_online, language=g_lang)
                    if res and res.get("success"):
                        ans = res["data"].get("explanation_taglish", "Pasensya na, hindi ko nagawa ang sagot.")
                        
                        # Add consensus note if available
                        consensus = res["data"].get("ai_consensus_note", "")
                        if consensus:
                            ans += f"\n\n*(Note: {consensus})*"
                            
                        # Show motivational quote
                        quote = res["data"].get("motivation_quote", "")
                        if quote:
                            ans += f"\n\n💡 *Tropa says: '{quote}'*"
                            
                        st.session_state.chat_messages.append({"role": "assistant", "content": ans})
                        st.rerun()
                    else:
                        st.error(f"Error answering: {res.get('error', 'Unknown Error')}")

# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================
if __name__ == "__main__":
    if st.session_state.user_id:
        dashboard()
    else:
        login_screen()