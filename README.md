# Writing Assistant with Ollama Integration

A modern, distraction-free writing assistant with real-time AI-powered writing suggestions using local Ollama or Google Gemini.

## Features

- 📝 Clean, distraction-free editor
- ✨ Real-time writing analysis (7+ issue types)
- 🤖 AI-enhanced suggestions via Ollama or Gemini
- 🌙 Dark/Light mode toggle
- 💾 Auto-save to local database
- 📤 Export to PDF & Markdown
- 📚 Document management

## Quick Start (Local)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment (optional, defaults to local mode)**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the app**
   ```bash
   python app.py
   ```

4. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

## Configuration

### Using Ollama (Recommended)

1. **Install Ollama** from https://ollama.ai
2. **Pull a model** (e.g., llama3.2:3b)
3. **Set environment variables**
   ```bash
   export AI_PROVIDER=ollama
   export OLLAMA_ENDPOINT=http://localhost:11434
   ```

### Using Google Gemini

1. **Get API key** from https://makersuite.google.com/app/apikey
2. **Set environment variable**
   ```bash
   export AI_PROVIDER=gemini
   export GEMINI_API_KEY=your-api-key-here
   ```

### Local Mode (No AI)

```bash
export AI_PROVIDER=local
```

## Deployment to Railway

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Railway"
   git push
   ```

2. **Create Railway Project**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository
   - Railway will auto-detect Python

3. **Set Environment Variables**
   - In Railway dashboard → Variables
   - Add your AI provider configuration

4. **Deploy**
   - Railway deploys automatically on GitHub push

## Writing Analysis

Analyzes text for:
- Passive voice
- Long sentences
- Weak words (very, really, just, etc)
- Word repetition
- Spelling errors
- Clichés
- Jargon

## Browser Support

Chrome, Firefox, Safari, Edge
