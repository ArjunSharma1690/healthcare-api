from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
import os
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Flask app setup
app = Flask(__name__)
CORS(app)

# Azure credentials from environment variables
ENDPOINT = os.getenv("ENDPOINT")
API_KEY = os.getenv("API_KEY")

client = TextAnalyticsClient(ENDPOINT, AzureKeyCredential(API_KEY))

@app.route('/', methods=['GET'])
def home():
    return "Healthcare API is running!", 200

@app.route('/analyze-health', methods=['POST'])
def analyze_health():
    logging.debug("Received request for healthcare entity analysis")

    try:
        data = request.get_json()
        logging.debug(f"Request data: {data}")

        documents = data.get("documents", [])
        if not documents:
            logging.warning("No documents provided")
            return jsonify({"error": "No input documents"}), 400

        poller = client.begin_analyze_healthcare_entities(documents)

        # Wait for completion with timeout handling
        try:
            result = poller.result(timeout=300)
        except HttpResponseError as e:
            logging.error(f"Timeout or HTTP error: {str(e)}")
            return jsonify({"error": f"Request failed: {str(e)}"}), 500

        entities = []
        for doc in result:
            for entity in doc.entities:
                entities.append({
                    "text": entity.text,
                    "category": entity.category,
                    "confidence": entity.confidence_score
                })

        logging.debug(f"Extracted entities: {entities}")
        return jsonify({"entities": entities})

    except Exception as e:
        logging.error(f"Error during analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
