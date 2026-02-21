"""
Writing Assistant - Web Application
A friendly AI-powered tool for improving your writing.
Free to use with Google Gemini AI.
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

# Custom CSS — Modern Dark Theme with Cyan Accents (Version 1)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-dark: #0f1419;
        --bg-darker: #0a0e14;
        --surface-primary: #1c2333;
        --surface-secondary: #252d3d;
        --text-primary: #e8ecf1;
        --text-secondary: #a8b0c0;
        --accent-cyan: #00d9ff;
        --accent-cyan-dim: #00d9ff33;
        --accent-cyan-hover: #00ffff;
        --border-color: #3a4452;
        --success: #4ade80;
        --warning: #fbbf24;
        --error: #ef4444;
        --sans: 'Inter', sans-serif;
        --mono: 'JetBrains Mono', monospace;
    }

    /* === Global overrides === */
    .main {
        background: var(--bg-dark) !important;
    }
    .main .block-container {
        padding: 2rem 2.5rem;
        max-width: 900px;
    }
    .stApp {
        background: var(--bg-dark) !important;
    }
    .stApp > header {
        background: transparent !important;
    }

    /* === Typography === */
    h1, h2, h3 {
        font-family: var(--sans) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    p, li, label, .stMarkdown {
        font-family: var(--sans) !important;
        color: var(--text-secondary) !important;
    }

    /* === Metrics — stat cards === */
    [data-testid="stMetricValue"] {
        font-family: var(--mono) !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: var(--accent-cyan) !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--mono) !important;
        font-size: 0.65rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary) !important;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        text-align: center;
    }

    /* === Text area === */
    .stTextArea textarea {
        border-radius: 6px !important;
        border: 1px solid var(--border-color) !important;
        font-family: var(--sans) !important;
        font-size: 0.95rem !important;
        line-height: 1.7 !important;
        background: var(--surface-primary) !important;
        color: var(--text-primary) !important;
        padding: 1rem 1.25rem !important;
        transition: all 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 3px var(--accent-cyan-dim) !important;
    }
    .stTextArea textarea::placeholder {
        color: var(--text-secondary) !important;
    }

    /* === Buttons === */
    .stButton > button {
        border-radius: 6px !important;
        padding: 0.7rem 1.5rem !important;
        font-family: var(--sans) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: none !important;
        background: var(--accent-cyan) !important;
        color: var(--bg-darker) !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: var(--accent-cyan-hover) !important;
        box-shadow: 0 0 16px var(--accent-cyan-dim) !important;
    }
    .stButton > button:active {
        opacity: 0.8;
    }

    /* === Section headers === */
    .section-header {
        font-family: var(--sans) !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin: 2rem 0 1.2rem 0;
        padding-bottom: 0;
        border-bottom: none;
        letter-spacing: 0;
    }
    .section-header::after {
        content: '';
        display: block;
        height: 2px;
        background: linear-gradient(to right, var(--accent-cyan), transparent);
        margin-top: 0.6rem;
    }

    /* === Sidebar toggle arrow — force dark on all states === */
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] *,
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] *,
    .st-emotion-cache-1dp5vir,
    .st-emotion-cache-1dp5vir *,
    button[kind="header"],
    button[kind="header"] * {
        color: #1a1a1a !important;
        fill: #1a1a1a !important;
        stroke: #1a1a1a !important;
    }
    /* Also target the sidebar close button inside the sidebar */
    [data-testid="stSidebar"] button[kind="header"],
    [data-testid="stSidebar"] button[kind="header"] *,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] * {
        color: #1a1a1a !important;
        fill: #1a1a1a !important;
        stroke: #1a1a1a !important;
    }

    /* === Hide Streamlit chrome === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* === Issue cards === */
    .issue-card {
        background: var(--surface-primary);
        border-radius: 6px;
        padding: 1rem 1.25rem;
        margin: 1rem 0 0.5rem 0;
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--accent-cyan);
        position: relative;
    }
    .issue-card:hover {
        border-color: var(--accent-cyan);
        background: var(--surface-secondary);
    }

    .category-badge {
        background: transparent;
        color: var(--accent-cyan);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-family: var(--mono) !important;
        font-size: 0.6rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        display: inline-block;
        margin-bottom: 0.5rem;
        border: 1px solid var(--accent-cyan);
    }

    .issue-title {
        font-family: var(--sans) !important;
        font-weight: 600;
        color: var(--text-primary) !important;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }

    /* === Text comparison boxes === */
    .text-box {
        padding: 1rem 1.25rem;
        border-radius: 6px;
        font-family: var(--sans) !important;
        font-size: 0.9rem;
        line-height: 1.7;
        margin: 0.5rem 0;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color);
    }

    .original-box {
        background: var(--surface-primary);
        border-left: 3px solid var(--warning);
        color: var(--text-secondary) !important;
    }

    .revised-box {
        background: var(--surface-primary);
        border-left: 3px solid var(--success);
        color: var(--text-primary) !important;
        font-weight: 500;
    }

    .placeholder-box {
        background: var(--surface-primary);
        border-left: 3px solid var(--text-secondary);
        color: var(--text-secondary) !important;
    }

    /* === Overall message box === */
    .message-box {
        background: var(--surface-primary);
        padding: 1.25rem 1.5rem;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        margin: 1.2rem 0;
        position: relative;
    }
    .message-box p {
        color: var(--text-primary) !important;
        font-family: var(--sans) !important;
        font-size: 1rem;
    }

    /* === AI feedback box === */
    .ai-feedback {
        background: var(--surface-primary);
        border-radius: 6px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        border-top: 2px solid var(--accent-cyan);
        line-height: 1.8;
        color: var(--text-secondary) !important;
        font-family: var(--sans) !important;
        font-size: 0.95rem;
        position: relative;
    }

    /* === Sidebar === */
    [data-testid="stSidebar"] {
        background: var(--surface-primary) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-secondary) !important;
    }

    /* === Toggle === */
    .stToggle label span {
        font-family: var(--sans) !important;
        color: var(--text-secondary) !important;
    }

    /* === Radio buttons === */
    .stRadio label {
        font-family: var(--sans) !important;
        color: var(--text-secondary) !important;
    }

    /* === Dividers === */
    hr {
        border: none !important;
        border-top: 1px solid var(--border-color) !important;
        margin: 1.5rem 0 !important;
    }

    /* === Scrollbar styling === */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-cyan);
    }

    /* === Score cards container === */
    .score-card {
        text-align: center;
        padding: 1.2rem 0.75rem;
        border: 1px solid var(--border-color);
        background: var(--surface-primary);
        border-radius: 6px;
        position: relative;
        transition: all 0.2s ease;
    }
    .score-card:hover {
        border-color: var(--accent-cyan);
        background: var(--surface-secondary);
    }
    .score-card::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 40%;
        height: 2px;
        background: var(--accent-cyan);
        border-radius: 1px;
    }
    .score-val {
        font-family: var(--mono);
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--accent-cyan);
        line-height: 1.2;
    }
    .score-label {
        font-family: var(--sans);
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        margin-top: 0.5rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Gemini
def get_client():
    """Get configured Gemini client."""
    api_key = os.environ.get("GOOGLE_API_KEY") or st.session_state.get("api_key", "")
    if api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            st.error(f"API Error: {e}")
            return None
    return None


def test_api_connection():
    """Test if API key works."""
    client = get_client()
    if client:
        try:
            # List models to verify API key works
            models = list(client.models.list())
            return len(models) > 0
        except Exception as e:
            st.error(f"Test failed: {e}")
            return False
    return False


def get_available_model(client):
    """Find an available model for text generation."""
    try:
        for model in client.models.list():
            model_name = model.name if hasattr(model, 'name') else str(model)
            # Look for gemini models that support generation
            if 'gemini' in model_name.lower() and 'flash' in model_name.lower():
                return model_name.replace('models/', '')
        # Fallback to any gemini model
        for model in client.models.list():
            model_name = model.name if hasattr(model, 'name') else str(model)
            if 'gemini' in model_name.lower():
                return model_name.replace('models/', '')
    except:
        pass
    return "gemini-1.5-flash-latest"  # Default fallback


def get_ai_suggestion(issue_type: str, original: str) -> tuple[str, str]:
    """Get AI-powered suggestion for a specific issue. Returns (suggestion, error)."""
    client = get_client()
    if not client:
        return None, "No API key configured"

    prompts = {
        "passive_voice": f"Rewrite this sentence in active voice. Return ONLY the rewritten sentence:\n\n{original}",
        "long_sentence": f"Break this into 2-3 shorter, clearer sentences. Return ONLY the rewritten text:\n\n{original}",
        "wordy": f"Make this more concise. Return ONLY the rewritten sentence:\n\n{original}",
        "complex_words": f"Simplify using everyday words. Return ONLY the rewritten sentence:\n\n{original}",
        "weak_words": f"Remove filler words and strengthen this. Return ONLY the rewritten sentence:\n\n{original}",
        "hedging": f"Make this more confident and direct. Return ONLY the rewritten sentence:\n\n{original}",
        "general": f"Improve clarity and impact. Return ONLY the rewritten sentence:\n\n{original}",
    }

    prompt = prompts.get(issue_type, prompts["general"])

    try:
        model_name = get_available_model(client)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip(), None
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return None, "Rate limit - wait 15 seconds"
        return None, f"AI error: {error_msg[:100]}"


def get_full_analysis(text: str) -> tuple[str, str]:
    """Get comprehensive AI analysis. Returns (analysis, error)."""
    client = get_client()
    if not client:
        return None, "No API key configured"

    prompt = f"""You are a helpful writing coach. Analyze this text and provide friendly, actionable feedback.

For each issue you find:
1. Quote the problematic text
2. Explain briefly why it could be improved
3. Provide a specific rewritten version

Focus on: clarity, conciseness, tone, and impact. Be encouraging!

TEXT:
{text}

Provide your feedback in a clear, organized format."""

    try:
        model_name = get_available_model(client)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip(), None
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return None, "Rate limit exceeded. Please wait 15-30 seconds and try again."
        return None, f"Error: {error_msg}"


# Helper functions
def get_sentences(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def get_words(text: str) -> list[str]:
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def get_overall_message(score: int) -> tuple[str, str]:
    if score >= 8:
        return "🌟", "Excellent work! Your writing is clear and polished."
    elif score >= 6:
        return "👍", "Good foundation! A few tweaks will make it even better."
    elif score >= 4:
        return "💪", "You're on the right track! Check the suggestions below."
    else:
        return "🌱", "Let's improve this together! See the suggestions below."


# Analysis patterns
WORDY_PHRASES = {
    'in order to': 'to', 'due to the fact that': 'because',
    'at this point in time': 'now', 'in the event that': 'if',
    'for the purpose of': 'to', 'at the present time': 'now',
    'in the near future': 'soon', 'has the ability to': 'can',
    'is able to': 'can', 'a large number of': 'many',
    'the majority of': 'most', 'in close proximity to': 'near',
    'take into consideration': 'consider', 'make a decision': 'decide',
}

COMPLEX_WORDS = {
    'utilize': 'use', 'implement': 'start', 'facilitate': 'help',
    'leverage': 'use', 'optimize': 'improve', 'methodology': 'method',
    'functionality': 'feature', 'subsequently': 'then',
    'approximately': 'about', 'commence': 'begin', 'terminate': 'end',
    'endeavor': 'try', 'sufficient': 'enough', 'numerous': 'many',
}

WEAK_WORDS = ['very', 'really', 'quite', 'rather', 'somewhat',
              'basically', 'actually', 'literally', 'just']

HEDGING_WORDS = ['maybe', 'perhaps', 'possibly', 'might', 'could be',
                 'seems like', 'sort of', 'kind of', 'I think', 'I believe']


def analyze_text(text: str) -> dict:
    """Analyze text for issues."""
    sentences = get_sentences(text)
    words = get_words(text)
    issues = []

    # Passive voice
    for sentence in sentences:
        if re.search(r'\b(is|are|was|were|been|being)\s+\w+ed\b', sentence, re.IGNORECASE):
            issues.append({
                'type': 'passive_voice',
                'category': 'Clarity',
                'issue': 'Passive voice detected',
                'original': sentence,
            })
            if len(issues) >= 2:
                break

    # Long sentences
    for sentence in sentences:
        word_count = len(get_words(sentence))
        if word_count > 30:
            issues.append({
                'type': 'long_sentence',
                'category': 'Clarity',
                'issue': f'Long sentence ({word_count} words)',
                'original': sentence,
            })

    # Wordy phrases
    for phrase, replacement in WORDY_PHRASES.items():
        for sentence in sentences:
            if phrase.lower() in sentence.lower():
                issues.append({
                    'type': 'wordy',
                    'category': 'Conciseness',
                    'issue': f'Wordy: "{phrase}" → "{replacement}"',
                    'original': sentence,
                    'fallback': re.sub(re.escape(phrase), replacement, sentence, flags=re.IGNORECASE)
                })
                break

    # Complex words
    found_complex = set()
    for sentence in sentences:
        for word, simple in COMPLEX_WORDS.items():
            if word in sentence.lower() and word not in found_complex:
                issues.append({
                    'type': 'complex_words',
                    'category': 'Style',
                    'issue': f'Complex: "{word}" → "{simple}"',
                    'original': sentence,
                    'fallback': re.sub(r'\b' + word + r'\b', simple, sentence, flags=re.IGNORECASE)
                })
                found_complex.add(word)
                break

    # Weak words
    weak_found = [w for w in words if w in WEAK_WORDS]
    if len(weak_found) > 2:
        for sentence in sentences:
            if any(w in sentence.lower() for w in WEAK_WORDS):
                issues.append({
                    'type': 'weak_words',
                    'category': 'Style',
                    'issue': 'Contains filler words',
                    'original': sentence,
                })
                break

    # Hedging
    for hedge in HEDGING_WORDS:
        for sentence in sentences:
            if hedge.lower() in sentence.lower():
                issues.append({
                    'type': 'hedging',
                    'category': 'Tone',
                    'issue': f'Hedging: "{hedge}"',
                    'original': sentence,
                })
                break
        if any(i['type'] == 'hedging' for i in issues):
            break

    # Calculate scores
    clarity_issues = len([i for i in issues if i['category'] == 'Clarity'])
    style_issues = len([i for i in issues if i['category'] == 'Style'])
    conciseness_issues = len([i for i in issues if i['category'] == 'Conciseness'])
    tone_issues = len([i for i in issues if i['category'] == 'Tone'])

    scores = {
        'clarity': max(5, 10 - clarity_issues * 2),
        'style': max(5, 10 - style_issues * 2),
        'conciseness': max(5, 10 - conciseness_issues * 2),
        'tone': max(5, 10 - tone_issues * 2),
    }
    scores['overall'] = round(sum(scores.values()) / 4)

    return {
        'issues': issues[:8],
        'scores': scores,
        'stats': {
            'words': len(words),
            'sentences': len(sentences),
            'avg_length': round(len(words) / max(len(sentences), 1), 1)
        }
    }


# ============== MAIN APP ==============

# Header
st.markdown("""
<div style="text-align: center; padding: 2.5rem 0 1.5rem 0;">
    <p style="font-family: var(--mono); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.2em; color: var(--accent-cyan); margin-bottom: 0.75rem;">✨ AI-Powered</p>
    <h1 style="font-family: var(--sans); font-size: 2.8rem; margin-bottom: 0.5rem; color: var(--text-primary); font-weight: 700; letter-spacing: -0.01em; line-height: 1.2;">Writing Assistant</h1>
    <p style="font-family: var(--sans); font-size: 0.95rem; color: var(--text-secondary);">Refine your prose with intelligent, real-time suggestions</p>
</div>
""", unsafe_allow_html=True)

# API Key in sidebar
with st.sidebar:
    st.markdown("### Settings")
    st.markdown("---")

    # Initialize session state
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    api_key_input = st.text_input(
        "Google API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="AIza...",
        help="Get a free key from Google AI Studio"
    )

    if api_key_input:
        st.session_state.api_key = api_key_input
        # Test the connection
        if st.button("Test API Key"):
            with st.spinner("Testing..."):
                if test_api_connection():
                    st.success("✅ API key works!")
                else:
                    st.error("❌ Invalid API key")

    if st.session_state.api_key:
        st.caption("✓ API key saved")

    st.markdown("---")
    st.markdown("""
    **Get your FREE API key:**
    1. Visit [aistudio.google.com](https://aistudio.google.com/apikey)
    2. Create API Key
    3. Paste it above

    **Free tier:** 15 requests/min
    """)

# Check API availability
has_api = bool(os.environ.get("GOOGLE_API_KEY") or st.session_state.get("api_key"))

st.markdown("---")

# Input section
st.markdown('<p class="section-header">your writing</p>', unsafe_allow_html=True)

input_method = st.radio(
    "Choose input:",
    ["Paste text", "Upload file"],
    horizontal=True,
    label_visibility="collapsed"
)

text = ""

if "Paste" in input_method:
    text = st.text_area(
        "Your text",
        height=220,
        placeholder="Begin typing or paste your text here...\n\nA few sentences will yield the richest feedback.",
        label_visibility="collapsed"
    )
else:
    uploaded = st.file_uploader("Upload", type=['txt', 'md'], label_visibility="collapsed")
    if uploaded:
        text = uploaded.read().decode('utf-8')
        st.info(f"Loaded {len(text.split())} words")

# Options row
st.markdown("")
col1, col2 = st.columns([1, 3])

with col1:
    use_ai = st.toggle(
        "AI Suggestions",
        value=has_api,
        disabled=not has_api,
        help="Enable AI-powered rewrites"
    )

with col2:
    if not has_api:
        st.caption("Add your free Google API key in the sidebar to enable AI suggestions")

# Analyze button
st.markdown("")
if st.button("Analyze My Writing", type="primary", use_container_width=True):

    if not text.strip():
        st.warning("Please enter some text to analyze.")
    else:
        st.markdown("---")

        # Run analysis
        with st.spinner("Analyzing..."):
            results = analyze_text(text)

        # Scores section
        st.markdown('<p class="section-header">assessment</p>', unsafe_allow_html=True)

        score_names = ['Overall', 'Clarity', 'Style', 'Conciseness', 'Tone']
        score_keys = ['overall', 'clarity', 'style', 'conciseness', 'tone']

        scores_html = '<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.75rem; margin: 1.5rem 0;">'
        for name, key in zip(score_names, score_keys):
            val = results['scores'][key]
            scores_html += f'''
            <div class="score-card">
                <div class="score-val">{val}</div>
                <div class="score-label">{name}</div>
            </div>'''
        scores_html += '</div>'
        st.markdown(scores_html, unsafe_allow_html=True)

        # Stats
        st.markdown("")
        st.markdown(
            f"<p style='color: var(--text-secondary); font-family: var(--mono); font-size: 0.75rem; letter-spacing: 0.05em;'>"
            f"<strong style=\"color: var(--accent-cyan);\">{results['stats']['words']}</strong> words &middot; "
            f"<strong style=\"color: var(--accent-cyan);\">{results['stats']['sentences']}</strong> sentences &middot; "
            f"<strong style=\"color: var(--accent-cyan);\">{results['stats']['avg_length']}</strong> avg words/sentence</p>",
            unsafe_allow_html=True
        )

        # Overall message
        emoji, message = get_overall_message(results['scores']['overall'])
        st.markdown(f"""
        <div class="message-box">
            <p style="color: var(--text-primary); font-size: 1rem; margin: 0; font-family: var(--sans);">
                {emoji} {message}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Suggestions
        if results['issues']:
            st.markdown("---")
            st.markdown('<p class="section-header">suggestions</p>', unsafe_allow_html=True)
            st.markdown(f"<p style='color: var(--text-secondary);'>{len(results['issues'])} areas to improve</p>", unsafe_allow_html=True)

            for i, issue in enumerate(results['issues']):
                st.markdown(f"""
                <div class="issue-card">
                    <span class="category-badge">{issue['category']}</span>
                    <div class="issue-title">{issue['issue']}</div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Original**")
                    st.markdown(f"""
                    <div class="text-box original-box">{issue['original']}</div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown("**Revised**")

                    suggestion = issue.get('fallback')
                    ai_error = None

                    if use_ai:
                        with st.spinner("AI thinking..."):
                            ai_suggestion, ai_error = get_ai_suggestion(issue['type'], issue['original'])
                            if ai_suggestion:
                                suggestion = ai_suggestion

                    if suggestion:
                        st.markdown(f"""
                        <div class="text-box revised-box">{suggestion}</div>
                        """, unsafe_allow_html=True)
                        if ai_error and use_ai:
                            st.caption(f"⚠️ {ai_error} (showing fallback)")
                    else:
                        msg = ai_error if ai_error else "Enable AI suggestions for a personalized rewrite"
                        st.markdown(f"""
                        <div class="text-box placeholder-box">{msg}</div>
                        """, unsafe_allow_html=True)

                st.markdown("")

        else:
            st.success("Excellent — no major issues found.")

        # Full AI Analysis
        if use_ai and has_api:
            st.markdown("---")
            st.markdown('<p class="section-header">ai feedback</p>', unsafe_allow_html=True)

            with st.spinner("Getting personalized feedback..."):
                ai_feedback, ai_error = get_full_analysis(text)

            if ai_feedback:
                st.markdown(f"""
                <div class="ai-feedback" style="white-space: pre-wrap;">
{ai_feedback}
                </div>
                """, unsafe_allow_html=True)
            elif ai_error:
                st.warning(f"⚠️ {ai_error}")

        # Footer message
        st.markdown("---")
        st.markdown("""
        <p style="text-align: center; color: var(--text-secondary); font-size: 0.9rem; padding: 1rem 0; font-family: var(--sans);">
            Keep refining your prose with every iteration.
        </p>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1.5rem 0 2rem 0;">
    <p style="font-family: var(--mono); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.15em; color: var(--text-secondary);">
        Writing Assistant &middot; Powered by Google Gemini
    </p>
</div>
""", unsafe_allow_html=True)
