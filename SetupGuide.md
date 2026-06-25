# 🚀 Runtime Terrors: Hackathon Setup Guide

## Step 1: Install Python
Since your laptop says "python not found", you need to install it first.
1. Go to [python.org/downloads](https://www.python.org/downloads/).
2. Download the latest version (e.g., Python 3.11 or 3.12).
3. **CRITICAL:** During installation, check the box that says **"Add Python to PATH"**.
4. Click "Install Now".

## Step 2: Verify Installation
1. Close your current terminal/command prompt.
2. Open a **NEW** terminal window.
3. Type: `python --version`
   - If it shows a version number (e.g., `Python 3.11.0`), you are ready!
   - If it still says "not found", restart your computer and try again.

## Step 3: Create Virtual Environment (Recommended)
This keeps your hackathon project isolated.
```bash
python -m venv venv
```

## Step 4: Activate the Environment
**Windows:**
```bash
venv\Scripts\activate
```
**Mac/Linux:**
```bash
source venv/bin/activate
```
*(You should see `(venv)` appear at the start of your command line)*

## Step 5: Install Dependencies
Now that Python is working and the environment is active:
```bash
pip install -r requirements.txt
```

## Step 6: Configure Secrets
1. Rename the `.env` file if you haven't already.
2. Paste your **Supabase URL**, **Supabase Key**, and **Groq API Key** into the `.env` file.

## Step 7: Run the Database Check
```bash
python database.py
```
If you see "✅ Supabase Client Connected Successfully!", you are ready to code!