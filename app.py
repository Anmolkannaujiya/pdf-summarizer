from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from main import extract_text_from_pdf, summarize_text
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size
ALLOWED_EXTENSIONS = {'pdf'}

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("Please set GOOGLE_API_KEY in your environment variables")
genai.configure(api_key=GOOGLE_API_KEY)

# Create uploads directory if it doesn't exist
upload_dir = Path(app.config['UPLOAD_FOLDER'])
upload_dir.mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_remove_file(filepath):
    """Safely remove a file if it exists."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Warning: Could not remove file {filepath}: {str(e)}")

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum file size is 200MB.')
    return redirect(url_for('upload_file'))

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                # Save the file
                file.save(filepath)
                
                # Extract and summarize text
                text = extract_text_from_pdf(filepath)
                summary = summarize_text(text)
                
                # Clean up the uploaded file
                safe_remove_file(filepath)
                
                return render_template('result.html', summary=summary)
            
            except ValueError as e:
                # Clean up the uploaded file
                safe_remove_file(filepath)
                flash(str(e))
                flash('Please try uploading a PDF with actual text content, not scanned images.')
                return redirect(request.url)
            except Exception as e:
                # Clean up the uploaded file
                safe_remove_file(filepath)
                flash(f'Error processing PDF: {str(e)}')
                return redirect(request.url)
        
        flash('Invalid file type. Please upload a PDF file.')
        return redirect(request.url)
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        message = data.get('message', '')
        summary = data.get('summary', '')
        
        if not message or not summary:
            return jsonify({'error': 'Missing message or summary'}), 400
            
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-pro')
        
        # Create a prompt that includes both the summary and the user's question
        prompt = f"""Here is a summary of a document:
        
        {summary}
        
        Please answer the following question based on the summary above:
        {message}
        
        If the answer cannot be found in the summary, please say so."""
        
        # Generate response
        response = model.generate_content(prompt)
        
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 