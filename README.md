PrepPilot — AI-Based Interview Preparation System

PrepPilot is an AI-powered mock interview platform that helps users practice job interviews across multiple roles and categories, with real-time AI-driven scoring, feedback, and performance analytics.

🔗Live App:https://preppilot-interview-coach-h2qqxzj4eh7r9jbkhatrnr.streamlit.app/


Overview

PrepPilot simulates a real interview experience: users log in, choose a job role and interview type, answer AI-generated questions (via text, voice, or code), and receive instant AI feedback with a score. Progress is tracked over time through a personal dashboard.

Core Pipeline

1. User registers/logs in
2. Selects a job role and interview type (Technical / HR / Coding)
3. AI generates a relevant question (optionally personalized using an uploaded resume)
4. User answers via text, voice, code, or attached media
5. NLP + AI evaluates the answer and generates a score
6. AI feedback and improvement suggestions are shown
7. Results are saved and visualized on a performance dashboard

Features

- User authentication with "remember me" (persistent login via secure tokens)
- Role & category selection (Technical / HR / Coding) across multiple job roles
- AI-generated interview questions, including resume-based personalization
- Voice input with speech-to-text transcription
- Media/file attachment support for answers
- Dedicated code evaluation flow for coding questions
- NLP-based answer scoring (keyword matching + semantic similarity)
- AI-generated, context-aware feedback per answer
- Personal dashboard: score trends, strengths/weaknesses by role and category, topic-level analysis
- Full answer history with feedback recall
- Publicly shareable, multi-user deployment (not just single-user/local)

Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Frontend / Web App | Streamlit |
| AI / LLM | Google Gemini API (question generation, answer evaluation, feedback) |
| NLP | spaCy |
| Semantic Analysis | Sentence Transformers |
| ML Utilities | Scikit-learn |
| Data Processing | Pandas, NumPy |
| Database | PostgreSQL / SQLite (via Supabase) |
| Visualization | Plotly |
| Resume Parsing | PyMuPDF |
| Voice Input | Speech-to-Text |
| Auth | Python + Database-backed authentication |
| Deployment | Streamlit Cloud |
| Version Control | Git + GitHub |

Database Structure

- Users — accounts, credentials, profile info
- Questions — question bank by role/category/difficulty
- Interview Results — stored answers, scores, feedback, timestamps per attempt

Project Links

- GitHub Repository:https://github.com/valli0796/preppilot-interview-coach
- Live App: https://preppilot-interview-coach-h2qqxzj4eh7r9jbkhatrnr.streamlit.app/

Future Scope

- Facial expression analysis during video answers
- Speaking speed and filler-word detection
- Grammar analysis on spoken/written answers
- AI-generated follow-up questions
- Personalized difficulty adjustment based on performance
- AI-driven long-term improvement plans

Built as part of an AI/ML Python internship project.