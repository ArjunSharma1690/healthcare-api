from flask import Flask, request, jsonify
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Flask app setup
app = Flask(__name__)

# Azure credentials
ENDPOINT = "https://neridslanguageservice.cognitiveservices.azure.com/"
API_KEY = "4ATbGpU5nQzbI4THYZ19NEf0kPGaBIime2mGUvoks88pq3tj05JgJQQJ99BCACYeBjFXJ3w3AAAaACOGHKQu"

# Create Azure Text Analytics client
client = TextAnalyticsClient(ENDPOINT, AzureKeyCredential(API_KEY))

# Route for checking if Flask is running
@app.route('/', methods=['GET'])
def home():
    return "Healthcare API is running!", 200

# Main route for healthcare entity analysis
@app.route('/analyze-health', methods=['POST'])
def analyze_health():
    logging.debug("Received request for healthcare entity analysis")

    try:
        # Get input data from request
        data = request.get_json()
        logging.debug(f"Request data: {data}")

        # Validate input
        documents = data.get("documents", [])
        if not documents:
            logging.warning("No documents provided")
            return jsonify({"error": "No input documents"}), 400

        # Start analysis process
        logging.debug("Starting healthcare entity analysis...")
        poller = client.begin_analyze_healthcare_entities(documents)

        # Wait for the operation to complete (timeout: 5 minutes)
        result = poller.wait(timeout=300)
        logging.debug("Polling complete")

        # Extract and format results
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

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
