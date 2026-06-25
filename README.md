## README.md

# Multi-AI Flashcard and Study Dashboard

A smart, pure Python web platform that leverages dual AI model pipelines to generate precise flashcards, evaluate formatting preferences, and serve as an active learning companion for uploaded study materials.

**Live Production URL:** [https://andyhub.org](https://andyhub.org)

## Core Features

### Multi-Account Cloud Authentication
* **Secure Access:** Built-in Python user onboarding flow with validation for multiple concurrent accounts.
* **Cloud Hosted Storage:** Registration data, credentials, and user preferences are saved and verified through secure cloud hosting upon opening the website.

### Intelligent Flashcard Generation (Dual-API Process)
After finishing a flashcard set, users can choose how to proceed:
1. **Refresh Used Cards:** Replays the exact same generated set from the current session.
2. **Generate New Set:** Triggers a two-stage Multi-AI verification pipeline:
    * **API 1 (The Generator):** Acts as the base engine to draft the questions from the text.
    * **API 2 (The Evaluator):** Intercepts the output, cross-checks it against user preferences and sample formats, and refines it before display.

### Document Upload and Expiry Cache
* **Temporary Storage:** Uploaded modules and materials are stored safely in the web application cache.
* **Auto-Expiry:** Uploaded documents remain viewable and accessible on a dedicated "View Saved Files" screen for exactly 4 days before automatic removal.
* **Format Imitation:** Upload sample questions during setup; API 2 forces the generated content to mimic your exact layout, question style, and structure.

### Processed Multi-AI Study Companion
* An integrated assistant within the main study dashboard that works directly in the context of your uploaded files.
* **Capabilities:** Adjusts, recommends, reads, and researches online.
* **Live Web Search:** Functions as an interactive reviewer companion, searching the web in real-time to provide credible, up-to-date answers to complex module questions.

---

## Getting Started

For full system prerequisites and detailed configuration steps, please refer to the accompanying [Setup Guide](SetupGuide.md).

### Quick Start (Local Development)

```bash
# Clone the project directory
git clone [https://github.com/Dawngend/Personal-Projects.git](https://github.com/Dawngend/Personal-Projects.git)
cd "Personal-Projects/All In One Reviewer"

# Set up environment and run
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py