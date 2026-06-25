# 🧠 RUNTIME TERROR: AI-Powered Study Tool for Filipino Learners

**Live Web Application:** [andyhub.org](https://andyhub.org)

## 📖 Project Overview
An intelligent, pure Python web platform built to address the unique challenges of the Philippine educational landscape. This active learning companion acts as a dynamic study dashboard, leveraging a dual-API AI architecture to generate precise, format-matched flashcards and serve as a conversational tutor contextualized for Filipino learners.

### 🚀 Development Roadmap (What We Will Develop)
* **Localization for Filipino Curriculums:** Fine-tuning the background prompt engineering templates to natively understand localized academic contexts, including specific grading formats, regional subjects (such as Philippine History, Civic Education, and local legislation), and mixed-language instruction.
* **Optimized Taglish/Bilingual Processing:** Enhancing the Multi-AI Companion pipeline to accurately process and reply in fluent Taglish (Tagalog-English mix) and standard Filipino, ensuring complex academic explanations are highly accessible and sound like a helpful peer rather than an abstract machine.

---

## ✨ Features (What We Have Developed)
* **Cloud-Based Multi-Account Authentication Flow:** A functional sign-up and log-in system matching user credentials against secure cloud storage, ensuring individual students can save their preferences and access their accounts concurrently.
* **Dual-API Intelligent Flashcard Engine:** A functional, two-tier AI generation process where **API 1** acts as the primary question generator, and **API 2** serves as a real-time evaluator to screen, refine, and structure the flashcards to meet explicit formatting guidelines.
* **Format-Mimicking Upload Engine:** A feature in the "Create New Reviewer" dashboard that accepts user-uploaded sample questions. The background AI pipeline analyzes these samples and forces newly generated materials to replicate that exact layout and structure.

---

## 💻 Technologies Used
* **Frontend & Orchestration:** Python, Streamlit
* **Backend & Authentication:** Supabase (PostgreSQL)
* **Intelligence Layer (API 1):** Groq (Llama 3.3 70B) for rapid, conversational Taglish generation.
* **Evaluation Layer (API 2):** Qwen (3.5 397B) for strict structural layout matching and JSON schema enforcement.
* **Environment Management:** `python-dotenv`

---

## ⚙️ Setup Instructions

### Prerequisites
* Python 3.9+ installed locally.
* A valid `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
* API keys for Groq and Qwen.

### Local Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Dawngend/Runtime-Terrors-TECHSPRINT.git](https://github.com/Dawngend/Runtime-Terrors-TECHSPRINT.git)
   cd Runtime-Terrors-TECHSPRINT
   ```

2. **Initialize the virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Windows
   # source .venv/bin/activate    # Mac/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory and safely add your credentials:
   ```env
   SUPABASE_URL="your-supabase-project-url"
   SUPABASE_ANON_KEY="your-supabase-publishable-key"
   GROQ_API_KEY="your-groq-key"
   QWEN_API_KEY="your-qwen-key"
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

---

## 👥 Team Members and Rules

### Team: RUNTIME TERROR
* **Jibrael D. Gumba**
* **Vinz Emmanuel B. Cruz**
* **Dawn Andrei Pamesa**

### Collaboration Rules
1. **Branching:** Do not push directly to `main`. Create isolated feature branches for your assigned tasks (e.g., `feature/auth-ui`, `bugfix/flashcard-logic`).
2. **Commits:** Write clear, concise commit messages detailing the changes made.
3. **Security:** **NEVER** commit `.env` files or hardcode API keys into the Python scripts. Always use environment variables.
4. **Merging:** Pull the latest changes from `origin main` before submitting or merging your code to avoid terminal merge conflicts. Do not force push to `main` without team consensus.
