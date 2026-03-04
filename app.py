from flask import Flask, render_template, request, jsonify
import os, uuid
from utils.text_extractor import extract_text
from utils.single_check import analyze_single_document

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    try:
        text = ''
        filename_used = ''

        if 'file' in request.files and request.files['file'].filename:
            f = request.files['file']
            if not allowed_file(f.filename):
                return jsonify({'error': 'Only TXT, PDF, DOCX files are supported.'}), 400
            fname = str(uuid.uuid4()) + '_' + f.filename
            path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            f.save(path)
            text = extract_text(path, f.filename)
            filename_used = f.filename
            os.remove(path)
        else:
            text = request.form.get('text', '').strip()
            filename_used = 'Pasted Text'

        if not text or len(text.strip()) < 30:
            return jsonify({'error': 'Document is too short or empty. Please provide more content.'}), 400

        result = analyze_single_document(text)
        result['filename'] = filename_used
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    import threading, webbrowser, time
    def open_browser():
        time.sleep(1.3)
        webbrowser.open('http://127.0.0.1:5000')
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, port=5000)
