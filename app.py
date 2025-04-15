from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from main import extract_text_from_pdf, summarize_text
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = secrets.token_hex(16)  # Secure random secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size
ALLOWED_EXTENSIONS = {'pdf'}

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("No GOOGLE_API_KEY found in environment variables")
    raise ValueError("GOOGLE_API_KEY is not set in .env file")

logger.info("Configuring Gemini API")
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    # Test the API connection
    models = genai.list_models()
    logger.info("Successfully connected to Gemini API")
    logger.info("Available models:")
    for model in models:
        logger.info(f"- {model.name}")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {str(e)}")
    raise ValueError(f"Failed to configure Gemini API: {str(e)}")

# Create uploads directory if it doesn't exist
upload_dir = Path(app.config['UPLOAD_FOLDER'])
upload_dir.mkdir(exist_ok=True)
logger.info(f"Upload directory: {upload_dir.absolute()}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_remove_file(filepath):
    """Safely remove a file if it exists."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Successfully removed file: {filepath}")
    except Exception as e:
        logger.error(f"Could not remove file {filepath}: {str(e)}")

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum file size is 200MB.')
    return redirect(url_for('landing'))

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/index.html', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Log file details
                logger.info(f"Processing file: {filename}")
                
                # Save the file
                file.save(filepath)
                logger.info(f"File saved to: {filepath}")
                
                try:
                    # Extract text
                    logger.info("Starting text extraction")
                    text = extract_text_from_pdf(filepath)
                    
                    if not text.strip():
                        flash('No text could be extracted from the PDF. Please ensure it contains text content.')
                        return redirect(request.url)
                    
                    # Generate summary
                    logger.info("Starting summarization")
                    summary = summarize_text(text)
                    logger.info("Summarization completed")
                    
                    # Clean up
                    os.remove(filepath)
                    logger.info("File cleaned up")
                    
                    return render_template('result.html', summary=summary)
                    
                except Exception as e:
                    logger.error(f"Error processing PDF: {str(e)}")
                    flash(f'Error processing PDF: {str(e)}')
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return redirect(request.url)
                    
            else:
                flash('Please upload a PDF file')
                return redirect(request.url)
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            flash(f'An unexpected error occurred: {str(e)}')
            return redirect(request.url)
            
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        logger.info("Received chat request")
        
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        message = data.get('message', '')
        summary = data.get('summary', '')
        
        logger.info(f"Chat message: {message[:100]}...")  # Log first 100 chars of message
        logger.info(f"Summary length: {len(summary)} characters")
        
        if not message:
            logger.error("Missing message")
            return jsonify({'error': 'Missing message'}), 400
            
        if not summary:
            logger.error("Missing summary")
            return jsonify({'error': 'Missing summary'}), 400
            
        try:
            # Initialize Gemini model
            model = genai.GenerativeModel('gemini-1.5-pro')  # Updated model name
            
            # Create a prompt that includes both the summary and the user's question
            prompt = f"""Here is a summary of a document:
            
            {summary}
            
            Please answer the following question based on the summary above:
            {message}
            
            If the answer cannot be found in the summary, please say so."""
            
            logger.info("Generating response with Gemini")
            # Generate response
            response = model.generate_content(prompt)
            
            if not response.text:
                logger.error("Empty response from Gemini")
                return jsonify({'error': 'Empty response from AI model'}), 500
                
            logger.info("Successfully generated response")
            return jsonify({'response': response.text})
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            # Provide a more user-friendly error message
            error_message = str(e)
            if "404" in error_message:
                return jsonify({
                    'error': 'AI model not found. Please check the model name and try again.'
                }), 404
            if "503" in error_message:
                return jsonify({
                    'error': 'AI service is currently unavailable. Please try again later.'
                }), 503
            return jsonify({'error': f'AI model error: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)