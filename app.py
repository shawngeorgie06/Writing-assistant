from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re
import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///writing_assistant.db'
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

db = SQLAlchemy(app)

# ============ Database Models ============

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), default='Untitled Document')
    content = db.Column(db.Text, default='')
    folder = db.Column(db.String(100), default='Inbox')  # Folder/Category
    tags = db.Column(db.Text, default='')  # Comma-separated tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    versions = db.relationship('Version', backref='document', lazy=True, cascade='all, delete-orphan')

class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)

# ============ Text Analysis Engine ============

class TextAnalyzer:
    def __init__(self):
        self.common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        self.passive_patterns = [
            r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\bwas\s+\w+ed\s+by\b',
            r'\bbeing\s+\w+ed\b',
        ]
        self.weak_words = {
            'very': 'extremely, incredibly, remarkably, significantly',
            'really': 'genuinely, truly, actually',
            'just': 'simply, only',
            'quite': 'fairly, rather',
            'actually': 'in fact, realistically',
            'basically': 'essentially, fundamentally',
            'literally': 'truly, actually',
            'simply': 'merely',
            'merely': 'only',
            'sort of': 'somewhat',
            'kind of': 'somewhat',
            'like': 'such as, for example'
        }
        self.filler_words = ['um', 'uh', 'like', 'you know', 'sort of', 'kind of']
        self.spelling_corrections = {
            'teh': 'the', 'recieve': 'receive', 'occured': 'occurred', 'seperate': 'separate',
            'definate': 'definite', 'arguement': 'argument', 'untill': 'until', 'wich': 'which',
            'their': 'there/their', 'your': 'you\'re/your'
        }
        self.cliches = [
            ('at the end of the day', 'consider removing - overused phrase'),
            ('it goes without saying', 'redundant - just state your point'),
            ('in this day and age', 'outdated phrase - use "today" or "currently"'),
            ('last but not least', 'clichéd - just list the item'),
            ('it is what it is', 'vague - be more specific'),
            ('think outside the box', 'corporate jargon - be more specific'),
            ('at this point in time', 'verbose - use "now"'),
            ('24/7', 'informal for formal writing - use "constantly" or "around the clock"'),
            ('win-win', 'clichéd business phrase - use "mutually beneficial"'),
            ('break the ice', 'clichéd - more direct approach usually better'),
        ]
        self.jargon = [
            'synergy', 'leverage', 'paradigm shift', 'circle back', 'deep dive',
            'takeaway', 'holistic approach', 'low-hanging fruit', 'touch base',
            'moving the needle', 'best in class', 'value add', 'bandwidth'
        ]
        self.casual_words = ['gonna', 'wanna', 'kinda', 'sorta', 'gotta', 'dunno', 'ain\'t']
        self.formal_words = ['shall', 'thereby', 'heretofore', 'furthermore', 'notwithstanding']

    def analyze(self, text):
        sentences = self._split_sentences(text)
        words = self._extract_words(text)

        issues = []
        issues.extend(self._check_passive_voice(text, sentences))
        issues.extend(self._check_long_sentences(text, sentences))
        issues.extend(self._check_weak_words(text, sentences))
        issues.extend(self._check_repetition(text, words))
        issues.extend(self._check_spelling(text, words))
        issues.extend(self._check_cliches(text))
        issues.extend(self._check_jargon(text))
        issues.extend(self._check_tone_consistency(text, words))

        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        issues.sort(key=lambda x: severity_order.get(x.get('severity', 'low')))

        # Calculate scores
        clarity_score = max(4, 10 - len([i for i in issues if i['category'] == 'Clarity']) * 1.5)
        style_score = max(4, 10 - len([i for i in issues if i['category'] == 'Style']) * 1.0)
        readability_score = self._calculate_readability(sentences, words)
        overall_score = round((clarity_score + style_score + readability_score) / 3)

        return {
            'issues': issues[:15],
            'scores': {
                'overall': overall_score,
                'clarity': round(clarity_score),
                'style': round(style_score),
            },
            'stats': {
                'words': len(words),
                'sentences': len(sentences),
                'avg_word_length': round(sum(len(w) for w in words) / max(len(words), 1), 1),
                'readability': round(readability_score),
                'paragraphs': len([p for p in text.split('\n\n') if p.strip()]),
            }
        }

    def _split_sentences(self, text):
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _extract_words(self, text):
        return re.findall(r'\b[a-zA-Z]+\b', text.lower())

    def _find_location(self, text, phrase):
        """Find the sentence number where phrase appears"""
        sentences = self._split_sentences(text)
        for i, sentence in enumerate(sentences):
            if phrase.lower() in sentence.lower():
                return i + 1
        return 1

    def _check_passive_voice(self, text, sentences):
        issues = []
        for i, sentence in enumerate(sentences):
            for pattern in self.passive_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    problematic = match.group(0)
                    # Suggest an active voice rewrite
                    issues.append({
                        'type': 'passive_voice',
                        'category': 'Clarity',
                        'location': f'Sentence {i + 1}',
                        'problematic_text': problematic,
                        'issue': f'PASSIVE VOICE: "{sentence}"',
                        'severity': 'medium',
                        'suggestion': f'Rewrite in active voice:\n- Current: {sentence}\n- Better: Start with WHO is doing the action, then the action.\nExample: "The team completed the project" instead of "The project was completed by the team"'
                    })
                    break
        return issues[:3]

    def _check_long_sentences(self, text, sentences):
        issues = []
        for i, sentence in enumerate(sentences):
            words = self._extract_words(sentence)
            if len(words) > 25:
                word_count = len(words)
                issues.append({
                    'type': 'long_sentence',
                    'category': 'Clarity',
                    'location': f'Sentence {i + 1}',
                    'problematic_text': sentence[:50] + '...',
                    'issue': f'SENTENCE TOO LONG ({word_count} words): "{sentence}"',
                    'severity': 'low',
                    'suggestion': f'Break this into 2-3 sentences for better readability.\n\nCurrent ({word_count} words):\n{sentence}\n\nSuggestion - Split at commas or conjunctions:\n1. [First part of sentence]\n2. [Second part of sentence]\n3. [Additional detail if needed]'
                })
        return issues[:3]

    def _check_weak_words(self, text, sentences):
        issues = []
        for i, sentence in enumerate(sentences):
            for weak_word, replacements in self.weak_words.items():
                match = re.search(rf'\b{weak_word}\b', sentence, re.IGNORECASE)
                if match:
                    issues.append({
                        'type': 'weak_words',
                        'category': 'Style',
                        'location': f'Sentence {i + 1}',
                        'problematic_text': weak_word,
                        'issue': f'WEAK WORD "{weak_word}" IN: "{sentence}"',
                        'severity': 'low',
                        'suggestion': f'Replace "{weak_word}" with a stronger alternative:\n\nCurrent: {sentence}\n\nBetter options: {replacements}\n\nExample: "{sentence.replace(weak_word, replacements.split(",")[0].strip())}"'
                    })
                    break
        return issues[:3]

    def _check_repetition(self, text, words):
        issues = []
        word_freq = {}
        positions = {}

        for idx, word in enumerate(words):
            if len(word) > 5 and word not in self.common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
                if word not in positions:
                    positions[word] = []
                positions[word].append(idx)

        for word, count in word_freq.items():
            if count > 3:
                sentences_with_word = self._split_sentences(text)
                found_in = []
                for i, sent in enumerate(sentences_with_word):
                    if word in sent.lower():
                        found_in.append(f"Sentence {i + 1}")
                        if len(found_in) >= 3:
                            break

                issues.append({
                    'type': 'repetition',
                    'category': 'Style',
                    'location': ', '.join(found_in),
                    'problematic_text': word,
                    'issue': f'WORD REPEATED {count}X: "{word}"',
                    'severity': 'low',
                    'suggestion': f'You used "{word}" {count} times. Add variety:\n\nAppears in: {", ".join(found_in)}\n\nAlternatives: Use synonyms like "topic", "subject", "issue", etc.\n\nAction: Find 1-2 instances and replace with similar words to improve readability.'
                })
        return issues[:2]

    def _check_spelling(self, text, words):
        issues = []
        sentences = self._split_sentences(text)

        for word in words:
            if word in self.spelling_corrections:
                for i, sentence in enumerate(sentences):
                    if word in sentence.lower():
                        issues.append({
                            'type': 'spelling',
                            'category': 'Grammar',
                            'location': f'Sentence {i + 1}',
                            'problematic_text': word,
                            'issue': f'SPELLING ERROR: "{word}" in "{sentence}"',
                            'severity': 'high',
                            'suggestion': f'Spelling error found!\n\nCurrent: {sentence}\n\nCorrection: "{word}" should be "{self.spelling_corrections[word]}"\n\nFixed: {sentence.replace(word, self.spelling_corrections[word])}'
                        })
                        break
        return issues[:5]

    def _check_cliches(self, text):
        """Detect overused phrases and clichés"""
        issues = []
        sentences = self._split_sentences(text)

        for phrase, replacement in self.cliches:
            for i, sentence in enumerate(sentences):
                if phrase.lower() in sentence.lower():
                    issues.append({
                        'type': 'cliche',
                        'category': 'Style',
                        'location': f'Sentence {i + 1}',
                        'problematic_text': phrase,
                        'issue': f'CLICHE DETECTED: "{phrase}"',
                        'severity': 'low',
                        'suggestion': f'This is an overused phrase.\n\nCurrent: {sentence}\n\nSuggestion: {replacement}\n\nBetter: Remove this phrase and be more direct with your message.'
                    })
                    break
        return issues[:2]

    def _check_jargon(self, text):
        """Detect business jargon and overused corporate terms"""
        issues = []
        sentences = self._split_sentences(text)
        words = self._extract_words(text)

        for jargon_word in self.jargon:
            for i, sentence in enumerate(sentences):
                if jargon_word.lower() in sentence.lower():
                    issues.append({
                        'type': 'jargon',
                        'category': 'Style',
                        'location': f'Sentence {i + 1}',
                        'problematic_text': jargon_word,
                        'issue': f'BUSINESS JARGON: "{jargon_word}"',
                        'severity': 'low',
                        'suggestion': f'This is corporate jargon that may confuse readers.\n\nCurrent word: "{jargon_word}"\n\nBetter alternatives: Use plain language to be clearer.\n\nExample: Replace "{jargon_word}" with a specific, concrete term that your audience understands.'
                    })
                    break
        return issues[:2]

    def _check_tone_consistency(self, text, words):
        """Check for inconsistent tone (mixing formal and casual)"""
        issues = []
        sentences = self._split_sentences(text)

        casual_count = sum(1 for word in words if word.lower() in self.casual_words)
        formal_count = sum(1 for word in words if word.lower() in self.formal_words)

        # If using both casual and formal language, suggest consistency
        if casual_count > 0 and formal_count > 0:
            casual_found = [word for word in words if word.lower() in self.casual_words][:2]
            formal_found = [word for word in words if word.lower() in self.formal_words][:2]

            issues.append({
                'type': 'tone_inconsistency',
                'category': 'Style',
                'location': f'Multiple locations',
                'problematic_text': 'Tone inconsistency',
                'issue': f'TONE INCONSISTENCY: Mixing formal and casual language',
                'severity': 'low',
                'suggestion': f'Your writing mixes formal and casual tones.\n\nCasual words found: {", ".join(casual_found)}\nFormal words found: {", ".join(formal_found)}\n\nBetter: Choose one consistent tone throughout:\n- Formal: Use "shall", "therefore", "furthermore"\n- Casual: Use "will", "so", "also"\n\nPick the tone that matches your audience and keep it consistent.'
            })

        return issues

    def _calculate_readability(self, sentences, words):
        if not sentences or not words:
            return 5
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Flesch-Kincaid approximation
        flesch_kincaid = 0.39 * avg_sentence_length + 11.8 * (avg_word_length / 5) - 15.59
        readability = max(4, min(10, 10 - (flesch_kincaid / 10)))
        return round(readability)

analyzer = TextAnalyzer()

# ============ AI Providers ============

class OllamaProvider:
    def __init__(self, endpoint='http://localhost:11434', model='llama3.2:3b'):
        self.endpoint = endpoint
        self.model = model

    def test_connection(self):
        try:
            import requests
            resp = requests.get(f'{self.endpoint}/api/tags', timeout=3)
            return resp.status_code == 200
        except:
            return False

    def get_suggestion(self, issue_text):
        try:
            import requests
            prompt = f"Improve this writing suggestion to be more helpful: {issue_text}. Keep it concise (under 20 words)."
            resp = requests.post(
                f'{self.endpoint}/api/generate',
                json={'model': self.model, 'prompt': prompt, 'stream': False},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json().get('response', issue_text).strip()
            return issue_text
        except Exception as e:
            print(f"Ollama error: {e}")
            return issue_text

class GeminiProvider:
    def __init__(self, api_key):
        self.api_key = api_key

    def test_connection(self):
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            list(client.models.list())
            return True
        except:
            return False

    def get_suggestion(self, issue_text):
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            prompt = f"Improve this writing suggestion: {issue_text}. Keep it concise (under 20 words)."
            response = client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents=prompt
            )
            return response.text.strip()
        except:
            return issue_text

# ============ Routes ============

@app.route('/')
def index():
    return render_template('app.html')

# ============ Document API ============

@app.route('/api/documents', methods=['GET'])
def get_documents():
    folder = request.args.get('folder')
    search = request.args.get('search')

    query = Document.query

    if folder:
        query = query.filter_by(folder=folder)

    docs = query.all()

    # Filter by search term if provided
    if search:
        search_lower = search.lower()
        docs = [d for d in docs if search_lower in d.title.lower() or search_lower in d.tags.lower()]

    return jsonify([{
        'id': d.id,
        'title': d.title,
        'folder': d.folder,
        'tags': d.tags,
        'updated_at': d.updated_at.isoformat(),
        'word_count': len(re.findall(r'\b\w+\b', d.content))
    } for d in sorted(docs, key=lambda x: x.updated_at, reverse=True)])

@app.route('/api/documents', methods=['POST'])
def create_document():
    doc = Document(
        title=request.json.get('title', 'Untitled Document'),
        content='',
        folder=request.json.get('folder', 'Inbox'),
        tags=request.json.get('tags', '')
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({
        'id': doc.id,
        'title': doc.title,
        'folder': doc.folder,
        'tags': doc.tags
    })

@app.route('/api/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id):
    doc = Document.query.filter_by(id=doc_id).first_or_404()
    return jsonify({
        'id': doc.id,
        'title': doc.title,
        'content': doc.content,
        'updated_at': doc.updated_at.isoformat(),
        'created_at': doc.created_at.isoformat()
    })

@app.route('/api/documents/<int:doc_id>', methods=['PUT'])
def update_document(doc_id):
    doc = Document.query.filter_by(id=doc_id).first_or_404()
    data = request.json

    if 'title' in data:
        doc.title = data['title']
    if 'content' in data:
        # Save version
        version = Version(content=doc.content, document_id=doc.id)
        db.session.add(version)
        doc.content = data['content']
        doc.updated_at = datetime.utcnow()
    if 'folder' in data:
        doc.folder = data['folder']
    if 'tags' in data:
        doc.tags = data['tags']

    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    doc = Document.query.filter_by(id=doc_id).first_or_404()
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/documents/<int:doc_id>/versions', methods=['GET'])
def get_versions(doc_id):
    doc = Document.query.filter_by(id=doc_id).first_or_404()
    versions = Version.query.filter_by(document_id=doc_id).order_by(Version.created_at.desc()).all()
    return jsonify([{
        'id': v.id,
        'created_at': v.created_at.isoformat(),
        'preview': v.content[:100] + '...' if len(v.content) > 100 else v.content
    } for v in versions[:10]])

@app.route('/api/documents/<int:doc_id>/versions/<int:v_id>', methods=['GET'])
def restore_version(doc_id, v_id):
    doc = Document.query.filter_by(id=doc_id).first_or_404()
    version = Version.query.filter_by(id=v_id, document_id=doc_id).first_or_404()
    return jsonify({'content': version.content})

# ============ Analysis API ============

@app.route('/api/analyze', methods=['POST'])
def analyze():
    text = request.json.get('text', '')
    if not text.strip():
        return jsonify({'error': 'No text provided'}), 400

    result = analyzer.analyze(text)

    # Enhance top suggestions with AI if configured (only first 2 to keep response fast)
    provider = os.getenv('AI_PROVIDER', 'local')

    if provider == 'ollama':
        endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434')
        ollama = OllamaProvider(endpoint=endpoint)
        if ollama.test_connection():
            for issue in result['issues'][:2]:  # Only enhance top 2 issues
                issue['suggestion'] = ollama.get_suggestion(issue.get('suggestion', issue.get('issue')))

    elif provider == 'gemini':
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            gemini = GeminiProvider(api_key=api_key)
            if gemini.test_connection():
                for issue in result['issues'][:2]:  # Only enhance top 2 issues
                    issue['suggestion'] = gemini.get_suggestion(issue.get('suggestion', issue.get('issue')))

    return jsonify(result)

# ============ Settings API ============

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({
        'ai_provider': os.getenv('AI_PROVIDER', 'local'),
        'ai_endpoint': os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434'),
        'has_api_key': bool(os.getenv('GEMINI_API_KEY', ''))
    })

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    # Settings are read from environment variables (set in .env or system env)
    # Client can't change them without modifying the server environment
    return jsonify({'success': True, 'message': 'Settings are configured via environment variables'})

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    provider = request.json.get('provider')
    api_key = request.json.get('api_key')
    endpoint = request.json.get('endpoint', 'http://localhost:11434')

    try:
        if provider == 'ollama':
            ollama = OllamaProvider(endpoint=endpoint)
            if ollama.test_connection():
                return jsonify({'success': True, 'message': 'Connected to Ollama!'})
            return jsonify({'success': False, 'message': 'Could not connect to Ollama'}), 400

        elif provider == 'gemini':
            gemini = GeminiProvider(api_key=api_key)
            if gemini.test_connection():
                return jsonify({'success': True, 'message': 'Gemini API connected!'})
            return jsonify({'success': False, 'message': 'Invalid Gemini API key'}), 400

        return jsonify({'success': False, 'message': 'Unknown provider'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ Organization API ============

@app.route('/api/folders', methods=['GET'])
def get_folders():
    """Get all folders for current user"""
    docs = Document.query.all()
    folders = list(set([d.folder for d in docs if d.folder]))
    if not folders:
        folders = ['Inbox']
    return jsonify({'folders': sorted(folders)})

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """Get all tags for current user"""
    docs = Document.query.all()
    all_tags = set()
    for doc in docs:
        if doc.tags:
            all_tags.update([t.strip() for t in doc.tags.split(',')])
    return jsonify({'tags': sorted(list(all_tags))})

# ============ Export API ============

@app.route('/api/export/<int:doc_id>/pdf', methods=['GET'])
def export_pdf(doc_id):
    doc = Document.query.filter_by(id=doc_id).first_or_404()

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f71d9',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph(doc.title, title_style))

    # Metadata
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#80868b',
        spaceAfter=20
    )
    story.append(Paragraph(f"Created: {doc.created_at.strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 0.3*inch))

    # Content
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_LEFT
    )

    for paragraph in doc.content.split('\n\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), content_style))
            story.append(Spacer(1, 0.2*inch))

    pdf.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{doc.title}.pdf'
    )

@app.route('/api/export/<int:doc_id>/markdown', methods=['GET'])
def export_markdown(doc_id):
    doc = Document.query.filter_by(id=doc_id).first_or_404()

    markdown = f"# {doc.title}\n\n"
    markdown += f"*Created: {doc.created_at.strftime('%Y-%m-%d %H:%M')}*\n\n"
    markdown += doc.content

    buffer = io.BytesIO(markdown.encode('utf-8'))
    return send_file(
        buffer,
        mimetype='text/markdown',
        as_attachment=True,
        download_name=f'{doc.title}.md'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
