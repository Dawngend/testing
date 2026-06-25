# AI Use and Data Disclosure

This application leverages a multi-model Artificial Intelligence (AI) architecture to provide dynamic flashcard generation, quality assurance, and interactive study assistance. Below is a disclosure of how AI models process data within this platform.

## AI Architecture (Dual-API Pipeline)

To ensure the highest accuracy and adherence to user-defined formatting preferences, this platform uses a two-stage AI pipeline executed entirely via our Python backend:

1. **API 1 (The Generator):** A primary AI language model engine optimized for content ingestion. It scans your uploaded files or topics to draft the initial set of flashcard questions and study answers.
2. **API 2 (The Evaluator):** A secondary, advanced LLM/chatbot layer. API 2 intercepts the raw draft from API 1 and evaluates it against your uploaded sample questions. It refines the format, checks for structural alignment, and acts as the gatekeeper before content reaches your dashboard.

## Live Web Research and Capabilities

The integrated AI Study Companion on the dashboard has the capability to:
* Read, analyze, adjust, and recommend adjustments to your study materials.
* Execute real-time online search queries to fetch up-to-date, credible reference data when user inquiries go beyond the scope of the uploaded document.

## Data Privacy and File Caching

* **File Storage:** Materials uploaded to the "Create New Reviewer" tab are processed into a secure backend cache to provide context to the AI models.
* **Auto-Deletion:** To respect user data privacy, all uploaded files are completely and automatically purged from the system after 4 days of storage.