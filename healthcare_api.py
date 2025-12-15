from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
import os
import logging
from werkzeug.serving import WSGIRequestHandler
from dotenv import load_dotenv
import json
import unicodedata
import re

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Allow large payloads
WSGIRequestHandler.protocol_version = "HTTP/1.1"

# Flask app setup
app = Flask(__name__)
CORS(app)
load_dotenv("env.env")
# Azure credentials from environment variables
ENDPOINT = os.getenv("endpoint")
API_KEY = os.getenv("key")

if not ENDPOINT or not ENDPOINT.startswith("https://"):
    raise ValueError("Azure endpoint must start with 'https://'")

if not API_KEY:
    raise ValueError("Azure key must be set as an environment variable.")

client = TextAnalyticsClient(ENDPOINT, AzureKeyCredential(API_KEY))

@app.route('/', methods=['GET'])
def home():
    return "Healthcare API is running Fine!", 200

@app.route('/analyze-health', methods=['POST'])
def analyze_health():
    logging.debug("Received request for healthcare entity analysis")

    try:
        data = request.get_json()
        if not data or "documents" not in data:
            logging.warning("Invalid or missing input data")
            return jsonify({"error": "Invalid input"}), 400

        logging.debug(f"Request data: {data}")

        documents = data.get("documents", [])
        if not documents:
            logging.warning("No documents provided")
            return jsonify({"error": "No input documents"}), 400

        # Send to Azure for healthcare entity analysis
        poller = client.begin_analyze_healthcare_entities(documents)

        try:
            result = poller.result(timeout=300)
        except HttpResponseError as e:
            logging.error(f"HTTP Error: {e.status_code} - {e.message}")
            return jsonify({"error": f"Request failed: {e.message}"}), e.status_code

        entities = []
        for doc in result:
            if not doc.is_error:
                for entity in doc.entities:
                    entities.append({
                        "text": entity.text,
                        "category": entity.category,
                        "confidence": entity.confidence_score
                    })
            else:
                logging.error(f"Document error: {doc.error}")
                return jsonify({"error": doc.error}), 400

        logging.debug(f"Extracted entities: {entities}")
        return jsonify({"entities": entities}), 200

    except Exception as e:
        logging.error(f"Error during analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
