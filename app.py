from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import pdfplumber
import textstat
import spacy
import nltk
import re
from openai import OpenAI
import io
import logging

# Set up OpenAI API
app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")
client = OpenAI(api_key="yourAPIkey", organization="yourOrg")

# Define relevant entities and their explanations
# Updated list of relevant entities
relevant_entities = [
    'PERSON', 'ORG', 'GPE', 'EMAIL', 'PHONE', 'MONEY', 'LAW', 'PRODUCT'
]

# Updated entity explanations
entity_explanations = {
    'PERSON': "References to individuals, such as names, indicating users, employees, or data subjects mentioned in the policy.",
    'ORG': "Organizations, companies, or institutions, typically identifying data handlers, service providers, or third parties mentioned in the policy.",
    'GPE': "Geopolitical entities like cities, states, and countries, often used to specify data residency, jurisdiction, or geographic applicability.",
    'EMAIL': "Email addresses, often provided for communication, user queries, or data-related requests.",
    'PHONE': "Phone numbers, typically included for customer service or complaint escalations.",
    'MONEY': "Monetary references, including fines, compensations, or costs associated with services or data breaches.",
    'LAW': "References to legal acts, statutes, or regulations, such as GDPR or the California Consumer Privacy Act.",
    'PRODUCT': "References to products or services used in data collection, processing, or analysis."
}

# Updated keywords for keyword analysis
keywords = {
    'Data Collection': ['collect', 'gather', 'obtain', 'acquire', 'retrieve', 'harvest', 'access', 'log', 'record', 'track', 'survey', 'request', 'monitor', 'audit'],
    'Data Sharing': ['share', 'disclose', 'sell', 'disseminate', 'transfer', 'exchange', 'provide', 'distribute', 'broker', 'supply'],
    'Data Usage': ['use', 'process', 'store', 'retain', 'analyze', 'manage', 'utilize', 'optimize', 'customize', 'aggregate', 'profile', 'develop'],
    'Legal Compliance': ['comply', 'compliance', 'GDPR', 'CCPA', 'COPPA', 'HIPAA', 'FTC', 'opt-out', 'opt-in', 'rights', 'obligations', 'regulations', 'laws', 'enforce', 'consent', 'transparency'],
    'Security and Protection': ['secure', 'protect', 'safeguard', 'encrypt', 'anonymize', 'pseudonymize', 'detect', 'prevent', 'monitor', 'alert', 'end-to-end encryption', 'data encryption'],
    'Retention and Deletion': ['retain', 'retention', 'delete', 'deletion', 'remove', 'purge', 'erase', 'archive', 'duration', 'period', 'time frame'],
    'User Rights': ['rights', 'access', 'modify', 'correct', 'delete', 'portability', 'consent', 'withdraw', 'reject', 'preferences', 'settings', 'manage', 'update', 'opt-out mechanism'],
    'Sensitive Information': ['biometric', 'genetic', 'health', 'medical', 'financial', 'sensitive', 'private', 'confidential', 'minors', 'children', 'age', 'race', 'ethnicity', 'religion', 'sexual orientation'],
    'Cookies and Tracking': ['cookie', 'tracker', 'pixel', 'beacon', 'tag', 'fingerprint', 'device ID', 'session', 'persistent', 'analytic', 'browser settings'],
    'Third Parties': ['third-party', 'vendor', 'service provider', 'affiliate', 'subsidiary', 'joint venture', 'advertising network', 'analytics'],
    'Data Breach and Risk': ['breach', 'hack', 'leak', 'unauthorized', 'misuse', 'vulnerability', 'risk', 'threat', 'incident'],
    'Advertising': ['advertise', 'advertising', 'ad', 'promote', 'promotion', 'marketing', 'targeting', 'campaign', 'banner', 'sponsored', 'personalized']
}



def extract_text_from_pdf(file):
    # Convert the uploaded file to a file-like object in memory using BytesIO
    file_stream = io.BytesIO(file.read())

    # Now open the PDF file and extract text using pdfplumber
    text = ""
    with pdfplumber.open(file_stream) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # Ensure text was extracted from the page
                text += page_text

    return text


def readability_analysis(text):
    scores = {
        'Flesch-Kincaid Grade Level': textstat.flesch_kincaid_grade(text),
        'Gunning Fog Index': textstat.gunning_fog(text),
        'SMOG Index': textstat.smog_index(text),
        'Total Word Count': len(text.split()),
        'Total Sentences': textstat.sentence_count(text)
    }
    explanations = {
        'Flesch-Kincaid Grade Level': "Indicates the education level required to understand the text. Scores of 8-10 are ideal; a score above 12 may be challenging for the average reader.",
        'Gunning Fog Index': "Measures complexity based on sentence length and difficult words. Scores below 10 are easier to read; higher scores indicate more complexity.",
        'SMOG Index': "Designed for texts requiring thorough understanding. Scores around 10-12 are accessible for most readers, while higher scores suggest advanced reading skills.",
        'Total Word Count': "Indicates the document length. Higher word counts may signify longer or more detailed policies.",
        'Total Sentences': "Indicates the number of sentences, which can affect readability depending on sentence length."
    }
    return scores, explanations

# Updated keyword_analysis function to include sentences and counts
def keyword_analysis(text, keywords):
    # Tokenize the text into sentences
    sentences = nltk.sent_tokenize(text)
    findings = {}

    # Search each sentence for keywords
    for category, words in keywords.items():
        findings[category] = {
            "count": 0,
            "sentences": []
        }
        for sentence in sentences:
            # Check if any keyword in the current category appears in the sentence
            if any(re.search(rf'\b{re.escape(word)}\b', sentence, re.IGNORECASE) for word in words):
                findings[category]["sentences"].append(sentence.strip())
                findings[category]["count"] += 1

    return findings

def extract_pii_entities_with_context(text):
    # Process the text using spaCy
    doc = nlp(text)

    # Initialize the findings dictionary
    findings = {entity_type: {"count": 0, "unique_entities": set(), "sentences": []}
                for entity_type in relevant_entities}

    for ent in doc.ents:
        if ent.label_ in relevant_entities:
            entity_type = ent.label_
            cleaned_entity = ent.text.replace('\n', ' ').strip()

            # Add the entity and sentence to the findings
            findings[entity_type]["count"] += 1
            findings[entity_type]["unique_entities"].add(cleaned_entity)
            findings[entity_type]["sentences"].append(ent.sent.text.strip())

    # Convert sets to lists for JSON serialization
    for entity_type in findings:
        findings[entity_type]["unique_entities"] = list(findings[entity_type]["unique_entities"])

    return findings



@app.route('/analyze', methods=['POST'])
def analyze_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    pdf_text = extract_text_from_pdf(file)

    if not pdf_text.strip():
        return jsonify({'error': 'No text found in PDF'}), 400

    # Perform readability, keyword, and entity analyses
    readability_scores, readability_explanations = readability_analysis(pdf_text)
    keyword_findings = keyword_analysis(pdf_text, keywords)
    entity_findings = extract_pii_entities_with_context(pdf_text)

    # Return results in a structured JSON response
    response = {
        'readability_scores': readability_scores,
        'readability_explanations': readability_explanations,
        'keyword_findings': keyword_findings,
        'entity_findings': entity_findings
    }

    return jsonify(response)

def generate_summary_text(sentences):
    try:
        # Make OpenAI API call to generate summary
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{
                "role": "user",
                "content": f"Summarize the following text in one paragraph of 5 sentences or less:\n\n{sentences}"
            }],
            max_tokens=300,
        )

        # Return summary if the response exists
        return response.choices[0].message.content.strip() if response.choices else "No summary available."
    
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return "Error generating summary."
  
@app.route('/queryOpenAI', methods=['POST'])
def generate_category_summary():
    try:
        # Get the full JSON body from the request
        data = request.json  # Fixed here: remove `.get()`

        # Log the incoming request data
        logging.info(f"Received data: {data}")

        if not data or 'category' not in data or 'keyword_findings' not in data:
            logging.error(f"Missing category or keyword_findings: {data}")
            return jsonify({'error': 'Missing category or keyword_findings'}), 400

        category = data.get("category")
        keyword_findings = data.get("keyword_findings")

        # Log category and keyword findings to debug
        logging.info(f"Category: {category}")
        logging.info(f"Keyword findings: {keyword_findings}")

        # Check if the category exists in keyword findings
        if category not in keyword_findings:
            logging.error(f"Invalid category: {category} not in keyword_findings")
            return jsonify({'error': 'Invalid category'}), 400

        # Fetch the sentences for the selected category
        sentences = " ".join(keyword_findings[category].get("sentences", []))

        # Check if sentences were found
        if not sentences.strip():
            logging.error(f"No sentences found for category: {category}")
            return jsonify({'error': 'No sentences found for the selected category'}), 400

        # Log sentences for debugging
        logging.info(f"Sentences: {sentences}")

        # Now call the OpenAI API to summarize the sentences
        summary = generate_summary_text(sentences)

        return jsonify({'summary': summary})

    except Exception as e:
        logging.error(f"Error in generate_category_summary: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/')
def index():
    return send_from_directory(os.path.join(app.root_path, 'quarto_site'), 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze_text():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file type. Only PDFs are supported.'}), 400

    # Pass the FileStorage object directly to the analysis function
    readability_scores, explanations, keyword_findings, entities_analysis, _ = analyze_pdf(file)

    # Return the analysis results
    response = {
        'readability_scores': readability_scores,
        'explanations': explanations,
        'keyword_findings': keyword_findings,
        'entity_counts': entities_analysis[0],
        'unique_entities': {k: list(v) for k, v in entities_analysis[1].items()}
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
