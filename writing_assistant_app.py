"""
Writing Assistant - Google Docs Style Interface
AI-powered writing companion with professional layout
"""

import streamlit as st
import re
import os
from google import genai

# Page configuration
st.set_page_config(
    page_title="Writing Assistant",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Clean, Professional Light Theme
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
    * {
        margin: 0;
        padding: 0;
    }

    body {
        background: #ffffff !important;
    }

    .stApp {
        background: #ffffff !important;
    }

    .main {
        background: #ffffff !important;
        padding: 0 !important;
    }

    [data-testid="stAppViewContainer"] {
        background: #ffffff !important;
    }

    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Hide Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    header { display: none !important; }

    /* Toolbar styling */
    .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        border-bottom: 1px solid #e0e0e0;
        background: #ffffff;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .doc-title {
        font-family: 'Roboto', sans-serif;
        font-size: 1.4rem;
        font-weight: 500;
        color: #202124;
    }

    .doc-info {
        font-family: 'Roboto', sans-serif;
        font-size: 0.85rem;
        color: #80868b;
        margin-top: 0.25rem;
    }

    /* Main container */
    .main-container {
        display: flex;
        min-height: calc(100vh - 80px);
    }

    .editor-column {
        flex: 2.5;
        padding: 2rem 3rem;
        border-right: 1px solid #e0e0e0;
        background: #ffffff;
        overflow-y: auto;
        max-height: calc(100vh - 80px);
    }

    .panel-column {
        flex: 1.2;
        padding: 2rem;
        background: #f8f9fa;
        overflow-y: auto;
        max-height: calc(100vh - 80px);
    }

    /* Text area */
    .stTextArea textarea {
        font-family: 'Roboto', sans-serif !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        color: #202124 !important;
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        resize: none !important;
    }

    .stTextArea textarea:focus {
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* Buttons */
    .stButton > button {
        background: #1f71d9 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.6rem 1.2rem !important;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: #1765cc !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    /* Panel styling */
    .panel-section {
        margin-bottom: 2rem;
    }

    .panel-title {
        font-family: 'Roboto', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #202124;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .score-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: white;
        border-radius: 4px;
        margin-bottom: 0.5rem;
        border: 1px solid #e8eaed;
    }

    .score-label {
        font-family: 'Roboto', sans-serif;
        font-size: 0.9rem;
        color: #5f6368;
    }

    .score-value {
        font-family: 'Roboto', sans-serif;
        font-weight: 600;
        color: #1f71d9;
        font-size: 1rem;
    }

    .stat-line {
        font-family: 'Roboto', sans-serif;
        font-size: 0.85rem;
        color: #5f6368;
        padding: 0.5rem 0;
        line-height: 1.6;
    }

    .divider {
        height: 1px;
        background: #e8eaed;
        margin: 1.5rem 0;
    }

    .issue-card {
        background: white;
        border: 1px solid #e8eaed;
        border-radius: 4px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .issue-card:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    .issue-category {
        font-family: 'Roboto', sans-serif;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #d33b27;
        letter-spacing: 0.5px;
        margin-bottom: 0.4rem;
    }

    .issue-text {
        font-family: 'Roboto', sans-serif;
        font-size: 0.85rem;
        color: #202124;
        line-height: 1.4;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #80868b;
    }

    .empty-state-text {
        font-family: 'Roboto', sans-serif;
        font-size: 0.95rem;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #999;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "text" not in st.session_state:
    st.session_state.text = ""
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "results" not in st.session_state:
    st.session_state.results = None

# Gemini setup
def get_client():
    api_key = os.environ.get("GOOGLE_API_KEY") or st.session_state.get("api_key", "")
    if api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            return None
    return None

def test_api_connection():
    client = get_client()
    if client:
        try:
            models = list(client.models.list())
            return len(models) > 0
        except:
            return False
    return False

def get_available_model(client):
    try:
        for model in client.models.list():
            model_name = model.name if hasattr(model, 'name') else str(model)
            if 'gemini' in model_name.lower() and 'flash' in model_name.lower():
                return model_name.replace('models/', '')
        for model in client.models.list():
            model_name = model.name if hasattr(model, 'name') else str(model)
            if 'gemini' in model_name.lower():
                return model_name.replace('models/', '')
    except:
        pass
    return "gemini-1.5-flash-latest"

def get_ai_suggestion(issue_type: str, original: str):
    client = get_client()
    if not client:
        return None, "No API key configured"
    prompts = {
        "passive_voice": f"Rewrite in active voice: {original}",
        "long_sentence": f"Break into shorter sentences: {original}",
        "wordy": f"Make more concise: {original}",
        "complex_words": f"Simplify: {original}",
        "weak_words": f"Strengthen: {original}",
        "hedging": f"Make more confident: {original}",
        "general": f"Improve: {original}",
    }
    prompt = prompts.get(issue_type, prompts["general"])
    try:
        model_name = get_available_model(client)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.strip(), None
    except Exception as e:
        return None, str(e)[:50]

# Analysis engine
WORDY_PHRASES = {
    'in order to': 'to', 'due to the fact that': 'because',
    'at this point in time': 'now', 'in the event that': 'if',
}

COMPLEX_WORDS = {
    'utilize': 'use', 'implement': 'start', 'facilitate': 'help',
    'leverage': 'use', 'optimize': 'improve',
}

def analyze_text(text: str) -> dict:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    issues = []

    # Passive voice
    for sentence in sentences:
        if re.search(r'\b(is|are|was|were)\s+\w+ed\b', sentence, re.IGNORECASE):
            issues.append({
                'type': 'passive_voice',
                'category': 'Clarity',
                'issue': 'Consider active voice',
                'original': sentence,
            })
            if len(issues) >= 2:
                break

    # Long sentences
    for sentence in sentences:
        word_count = len(re.findall(r'\b[a-zA-Z]+\b', sentence))
        if word_count > 30:
            issues.append({
                'type': 'long_sentence',
                'category': 'Clarity',
                'issue': f'Long sentence ({word_count} words)',
                'original': sentence,
            })

    scores = {
        'overall': max(5, 10 - len(issues)),
        'clarity': max(5, 10 - len([i for i in issues if i['category'] == 'Clarity'])),
        'style': max(5, 10 - len([i for i in issues if i['category'] == 'Style'])),
        'tone': 8,
    }

    return {
        'issues': issues[:5],
        'scores': scores,
        'stats': {
            'words': len(words),
            'sentences': len(sentences),
        }
    }

# TOOLBAR
st.markdown("""
<div class="toolbar">
    <div>
        <div class="doc-title">Untitled Document</div>
        <div class="doc-info">Saved in Cloud • Last edited now</div>
    </div>
    <button style="background: white; border: 1px solid #e0e0e0; padding: 0.6rem 1.2rem; border-radius: 4px; color: #1f71d9; cursor: pointer; font-family: Roboto; font-weight: 500; font-size: 0.9rem;">Share</button>
</div>
""", unsafe_allow_html=True)

# API Key setup in sidebar
with st.sidebar:
    with st.expander("🔑 API Setup"):
        api_key = st.text_input("Google API Key", type="password", placeholder="AIza...")
        if api_key:
            st.session_state.api_key = api_key
        if st.button("Test API"):
            if test_api_connection():
                st.success("✅ Works!")
            else:
                st.error("❌ Invalid")

# MAIN LAYOUT
col_editor, col_panel = st.columns([2.5, 1.2], gap="small")

# LEFT COLUMN - EDITOR
with col_editor:
    st.markdown('<div class="editor-column">', unsafe_allow_html=True)

    text = st.text_area(
        "editor",
        value=st.session_state.text,
        height=600,
        placeholder="Start typing or paste your document...",
        label_visibility="collapsed"
    )
    st.session_state.text = text

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        use_ai = st.toggle("AI Suggestions")
    with col_btn2:
        if st.button("📊 Analyze"):
            if text.strip():
                st.session_state.results = analyze_text(text)
                st.session_state.analysis_done = True

    st.markdown('</div>', unsafe_allow_html=True)

# RIGHT COLUMN - AI PANEL
with col_panel:
    st.markdown('<div class="panel-column">', unsafe_allow_html=True)

    if st.session_state.analysis_done and st.session_state.results:
        results = st.session_state.results

        # Document Intelligence
        st.markdown('<div class="panel-title">📋 Document Intelligence</div>', unsafe_allow_html=True)

        for label, key in [('Overall', 'overall'), ('Clarity', 'clarity'), ('Style', 'style')]:
            st.markdown(f"""
            <div class="score-item">
                <span class="score-label">{label}</span>
                <span class="score-value">{results['scores'][key]}/10</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Stats
        st.markdown('<div class="panel-title">📊 Statistics</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-line"><strong>Words:</strong> {results['stats']['words']}</div>
        <div class="stat-line"><strong>Sentences:</strong> {results['stats']['sentences']}</div>
        """, unsafe_allow_html=True)

        if results['issues']:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="panel-title">⚠️ Suggestions ({len(results["issues"])})</div>', unsafe_allow_html=True)

            for issue in results['issues']:
                st.markdown(f"""
                <div class="issue-card">
                    <div class="issue-category">{issue['category']}</div>
                    <div class="issue-text">{issue['issue']}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <p class="empty-state-text">💡 Click "Analyze" to see insights</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
