from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
import os
from dotenv import load_dotenv
from main import start_article_generation
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/generate-posts', methods=['POST'])
def generate_posts():
    current_app.logger.info("Backend has been hit")
    data = request.json
    current_app.logger.info("This is data" + json.dumps(data))
    required_fields = ['company', 'companyName', 'productName', 'keywords', 
                       'keywordInputType', 'keywordTheme'
                       'tone', 'intent', "customIntent",
                       'companyInfo', #This is the knowledge base about the company that is writing this article
                       'productInfo', #This is the knowledge specific to the product that is writing this article 
                       'customInstructions', #Custom instructions for blog given to GPT
                       'articleCount',
                       'externalLinking', 'internalLinking', 
                       'mentionProduct', 'specificProductInfo'] #Whether we should mention the customer's product in the article
    print("This is received data", data)
    if not all(field in data for field in required_fields):
        current_app.logger.info("Json shitty")
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        current_app.logger.info("Starting to generate articles")
        result = start_article_generation(data)
        return jsonify(result)
    except Exception as e:
        current_app.logger.info("Error generating article")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)