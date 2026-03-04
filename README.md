# 🔍 PlagiScan — PDF & Document Plagiarism Detector

Single-document plagiarism detector with word-level highlights.

## 🚀 Run in 3 Steps

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run
py app.py

# 3. Browser opens automatically at http://127.0.0.1:5000
```

## ✨ Features
- Upload PDF, DOCX, TXT or paste text
- Word-level highlights (🔴 Red = phrase repeated, 🟡 Yellow = word repeated)
- Plagiarism % score per sentence
- Full flagged words table with repeat count
- Repeated phrases list
- Auto-opens browser on run

## 📊 How Detection Works
- **Red**: 4-word phrases that appear more than once in the document
- **Yellow**: Individual words that appear 3+ times (excluding common words)
- **Score**: % of content words flagged as suspicious
