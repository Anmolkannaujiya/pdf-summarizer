# PDF Summarizer

A Python application that extracts text from PDF files and generates summaries using the BART model.

## Project Structure
```
pdf_summarizer/
├── main.py
├── sample.pdf         # Add your PDF here
└── summaries/
    └── summary.txt    # Output saved here
```

## Requirements
- Python 3.7+
- Required packages listed in requirements.txt

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Place your PDF file in the project directory and rename it to `sample.pdf`
2. Run the script:
```bash
python main.py
```
3. The summary will be saved in the `summaries/summary.txt` file

## Features
- PDF text extraction
- Text summarization using BART model
- Automatic directory creation
- Error handling

## Note
The first run might take some time as it downloads the BART model. 