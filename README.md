# Privacy Policy Web App

This web application is designed to analyze privacy policies in an accessible way. It scans PDFs of privacy policies, extracting and analyzing text for readability, keyword frequency, and personally identifiable information (PII). The app provides detailed insights on the structure and content of privacy policies to help users understand how their data is handled.

## Features

- **PDF Upload**: Upload a PDF of a privacy policy for analysis.
- **Readability Scores**: Assess the readability of the document with various metrics (e.g., Flesch Reading Ease, Gunning Fog Index).
- **Keyword Analysis**: Extract and display key phrases related to privacy policies such as data collection, user rights, and security.
- **PII Detection**: Identify and count personally identifiable information (PII) such as names, email addresses, and other sensitive data.
- **Interactive Web Interface**: An intuitive, user-friendly interface built using Flask.

## Installation

Follow these steps to set up the project on your local machine.

### 1. Clone the repository

```bash
git clone https://github.com/braeden-falzarano/PrivacyPolicyWebApp.git
cd PrivacyPolicyWebApp
```

### 2. Set up a virtual environment (Optional but recommended)
If you haven't already, create a virtual environment to keep dependencies isolated.
```bash
python -m venv venv
```

### 3. Activate the virtual environment
On macOS/Linux:
```bash
source venv/bin/activate
```
On Windows:
```bash
.\venv\Scripts\activate
```

### 4. Install dependencies
Install the required Python packages from requirements.txt.
```bash
pip install -r requirements.txt
```

### 5. Download spaCy model
This app uses the spaCy language model for text analysis. You can download the required model with the following command:
```bash
python -m spacy download en_core_web_sm
```

6. Run the app
Once dependencies are installed and the model is downloaded, you can start the Flask server by running:
```bash
python app.py
```
By default, the app will be accessible at http://127.0.0.1:5000/ in your browser.

## Usage
Upload PDF: Navigate to the web page and upload a privacy policy PDF file.
View Analysis: After uploading, the app will analyze the document and provide insights such as readability scores, keyword findings, and PII count.

## Acknowledgements
- Flask for the web framework.
- spaCy for natural language processing.
- pdfplumber for extracting text from PDF files.
- Textstat for readability metrics.
- OpenAI for integration with GPT models (if applicable).

## **NOTE**
If you do not have an OPENAI API Key the summarise sentences feature will not work. If you want to learn more about getting an API key go [HERE](https://medium.com/@lorenzozar/how-to-get-your-own-openai-api-key-f4d44e60c327)




