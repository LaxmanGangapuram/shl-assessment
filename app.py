"""
Flask API for SHL Assessment Recommendation System
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from recommender import AssessmentRecommender
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize recommender
recommender = None


def initialize_recommender():
    """Initialize the recommendation engine"""
    global recommender
    if recommender is None:
        print("Initializing recommendation engine...")
        recommender = AssessmentRecommender()
        print("Recommendation engine ready!")


@app.before_request
def before_first_request():
    """Initialize recommender before first request"""
    initialize_recommender()


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns API status and version
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "SHL Assessment Recommendation API"
    }), 200


@app.route('/recommend', methods=['POST'])
def recommend_assessments():
    """
    Assessment recommendation endpoint
    
    Request body:
    {
        "query": "Job description or natural language query"
    }
    
    Response:
    {
        "query": "original query",
        "recommendations": [
            {
                "assessment_name": "Assessment name",
                "url": "Assessment URL",
                "relevance_score": 0.85,
                "category": "cognitive",
                "test_type": "A"
            },
            ...
        ],
        "count": 10
    }
    """
    try:
        # Get query from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing 'query' field in request body"
            }), 400
        
        query = data['query']
        
        if not query or not query.strip():
            return jsonify({
                "error": "Query cannot be empty"
            }), 400
        
        # Get top_k parameter (default 10, max 10, min 5)
        top_k = data.get('top_k', 10)
        top_k = max(5, min(10, top_k))
        
        # Get recommendations
        recommendations = recommender.recommend(query, top_k=top_k)
        
        # Format recommendations
        formatted_recommendations = [
            recommender.format_recommendation(rec)
            for rec in recommendations
        ]
        
        # Prepare response
        response = {
            "query": query,
            "recommendations": formatted_recommendations,
            "count": len(formatted_recommendations)
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500


@app.route('/', methods=['GET'])
def home():
    """API information endpoint"""
    return jsonify({
        "name": "SHL Assessment Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "Check API health status"
            },
            "recommend": {
                "method": "POST",
                "path": "/recommend",
                "description": "Get assessment recommendations",
                "body": {
                    "query": "string (required) - Job description or natural language query"
                }
            }
        }
    }), 200


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "status": 404
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "status": 500
    }), 500


if __name__ == '__main__':
    # Initialize recommender on startup
    initialize_recommender()
    
    # Run the app (debug=False for faster startup, no auto-reload)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
