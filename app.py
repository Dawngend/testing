import streamlit as st
import os
import sys
import traceback

# 1. DEBUG: Print where we are
print("🚀 Starting Tropa App...")

# 2. FORCE LOAD ENV
from dotenv import load_dotenv
load_dotenv()

# 3. TRY IMPORTING BACKEND WITH ERROR CATCHING
try:
    import main_backend as backend
    print("✅ Backend imported successfully")
except Exception as e:
    st.error(f"❌ CRITICAL ERROR: Could not import main_backend.")
    st.error(f"Error Details: {str(e)}")
    st.code(traceback.format_exc())
    st.stop() # Stop execution here so we don't crash further

# 4. PAGE CONFIG
st.set_page_config(page_title="Tropa: AI Study Companion", page_icon="🇵🇭", layout="centered")

# 5. SESSION STATE INIT
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 6. DEBUG: Check State
print(f"🔍 Current User ID: {st.session_state.user_id}")

# 7. UI FUNCTIONS
def login_screen():
    st.title("🇵🇭 Tropa: AI Study Companion")
    st.write("Debug: Login Screen Loaded")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", type="primary", use_container_width=True):
            if not email or not password:
                st.warning("Please enter email and password.")
            else:
                with st.spinner("Logging in..."):
                    try:
                        result = backend.login_user(email, password)
                        if result and result.get('success'):
                            st.session_state.user_id = result['user_id']
                            st.session_state.profile = result['profile']
                            st.success("Login successful! Refreshing...")
                            st.rerun()
                        else:
                            msg = result.get('message', 'Unknown error') if result else 'No response from backend'
                            st.error(f"Login failed: {msg}")
                    except Exception as e:
                        st.error(f"Exception during login: {str(e)}")

    with tab2:
        st.subheader("Sign Up")
        username = st.text_input("Username", key="reg_user")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        grade = st.number_input("Grade Level", 1, 12, 10, key="reg_grade")
        
        if st.button("Sign Up", type="primary", use_container_width=True):
            if not all([username, email, password]):
                st.warning("Please fill all fields.")
            else:
                with st.spinner("Creating account..."):
                    try:
                        result = backend.register_user(username, email, password, grade)
                        if result and result.get('success'):
                            st.success("Account created! Please login.")
                        else:
                            msg = result.get('message', 'Unknown error') if result else 'No response'
                            st.error(f"Signup failed: {msg}")
                    except Exception as e:
                        st.error(f"Exception during signup: {str(e)}")

def dashboard():
    st.title(f"👋 Hi, {st.session_state.profile.get('username', 'User')}!")
    st.write("Debug: Dashboard Loaded")
    
    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.profile = None
        st.rerun()

    st.metric("Mastery", f"{st.session_state.profile.get('mastery_score', 0):.1%}")
    
    tab1, tab2 = st.tabs(["Chat", "Upload"])
    
    with tab1:
        st.write("Chat Tab Loaded")
        # Simple test message
        if not st.session_state.messages:
            st.info("Start chatting below!")
            
        for msg in st.session_state.messages:
            with st.chat_message(msg['role']):
                st.write(msg['content'])
        
        if prompt := st.chat_input("Ask..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = backend.ask_study_companion(st.session_state.user_id, prompt)
                        if response and response.get('success'):
                            data = response['data']
                            # Just show the explanation for now to keep it simple
                            text = data.get('explanation_taglish', 'No text generated.')
                            st.session_state.messages.append({"role": "assistant", "content": text})
                            st.rerun()
                        else:
                            err = response.get('error', 'Unknown error') if response else 'No response'
                            st.error(f"AI Error: {err}")
                    except Exception as e:
                        st.error(f"Exception in chat: {str(e)}")

    with tab2:
        st.write("Upload Tab Loaded")
        f = st.file_uploader("Upload PDF", type=['pdf'])
        if f and st.button("Process"):
            with open(f"temp_{f.name}", "wb") as wf:
                wf.write(f.getvalue())
            try:
                res = backend.upload_and_process_material(f"temp_{f.name}", st.session_state.user_id, 10)
                st.json(res)
            except Exception as e:
                st.error(f"Upload Error: {str(e)}")
            finally:
                if os.path.exists(f"temp_{f.name}"):
                    os.remove(f"temp_{f.name}")

# 8. MAIN LOGIC
if __name__ == "__main__":
    try:
        if st.session_state.user_id:
            dashboard()
        else:
            login_screen()
    except Exception as e:
        st.error(f"💥 GLOBAL APP ERROR: {str(e)}")
        st.code(traceback.format_exc())