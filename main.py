import os
from PyPDF2 import PdfReader
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from pathlib import Path
import nltk

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        total_pages = len(reader.pages)
        pages_with_text = 0
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text.strip():
                pages_with_text += 1
                text += page_text
            else:
                print(f"Warning: Page {i+1} appears to be empty or contains no extractable text")
        
        if not text.strip():
            raise ValueError("The PDF appears to be image-based or scanned. Please use a PDF with actual text content.")
        
        print(f"Successfully extracted text from {pages_with_text} out of {total_pages} pages")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise

def calculate_summary_length(text):
    """Calculate appropriate summary length based on text size."""
    # Count words in the text
    words = text.split()
    word_count = len(words)
    
    # Calculate summary length based on text size
    if word_count < 1000:
        return 3  # Very short text
    elif word_count < 5000:
        return 5  # Short text
    elif word_count < 10000:
        return 8  # Medium text
    elif word_count < 25000:
        return 12  # Long text
    else:
        return 15  # Very long text

def summarize_text(text):
    """Summarize the given text using LSA (Latent Semantic Analysis)."""
    try:
        # Download required NLTK data
        nltk.download('punkt')
        
        # Calculate appropriate summary length
        sentences_count = calculate_summary_length(text)
        print(f"Generating summary with {sentences_count} sentences")
        
        # Create parser and tokenizer
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        
        # Create summarizer
        summarizer = LsaSummarizer()
        
        # Generate summary
        summary_sentences = summarizer(parser.document, sentences_count)
        
        if not summary_sentences:
            raise ValueError("No summary sentences were generated")
            
        # Join sentences into a single string
        summary = " ".join(str(sentence) for sentence in summary_sentences)
        
        # Add a header with summary statistics
        summary_header = f"Summary ({sentences_count} key points):\n\n"
        return summary_header + summary
    except Exception as e:
        print(f"Error during summarization: {str(e)}")
        raise

def main():
    # Create summaries directory if it doesn't exist
    summaries_dir = Path("summaries")
    summaries_dir.mkdir(exist_ok=True)

    # Path to the PDF file
    pdf_path = "sample.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found. Please add your PDF file to the project directory.")
        return

    try:
        # Extract text from PDF
        print("Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        print(f"Successfully extracted {len(text)} characters from PDF")
        
        # Summarize the text
        print("Generating summary...")
        summary = summarize_text(text)
        print(f"Generated summary with {len(summary)} characters")
        
        # Save the summary
        output_path = summaries_dir / "summary.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        
        print(f"Summary saved to: {output_path}")
        print("Summary content:")
        print("-" * 50)
        print(summary)
        print("-" * 50)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check if:")
        print("1. The PDF file is not password protected")
        print("2. The PDF contains actual text (not just images)")
        print("3. The PDF is not corrupted")
        print("4. If the PDF is scanned, consider using OCR software to convert it to text first")

if __name__ == "__main__":
    main() 