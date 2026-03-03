# SHL Assessment Recommendation System

An intelligent recommendation system that helps hiring managers and recruiters find the most relevant SHL assessments based on natural language queries or job descriptions.

## 🎯 Project Overview

This system uses advanced NLP techniques and semantic similarity to recommend 5-10 most relevant "Individual Test Solutions" from SHL's product catalog based on job descriptions or hiring queries.

## 🏗️ Architecture

### Components

1. **Web Scraper** (`scraper.py`)
   - Scrapes SHL product catalog
   - Extracts assessment information (377+ Individual Test Solutions)
   - Stores structured data for recommendation engine

2. **Recommendation Engine** (`recommender.py`)
   - Uses Sentence Transformers for semantic embeddings
   - Implements vector similarity search
   - Balances recommendations between hard and soft skills
   - Supports intelligent reranking based on query context

3. **Flask API** (`app.py`)
   - RESTful API with health check and recommendation endpoints
   - JSON request/response format
   - CORS enabled for frontend access

4. **Frontend** (`index.html`)
   - Clean, responsive web interface
   - Real-time recommendations
   - Sample queries for easy testing

5. **Evaluation System** (`evaluate.py`)
   - Calculates Mean Recall@10 on training data
   - Generates test predictions in required CSV format
   - Produces detailed evaluation reports

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 1. Scrape SHL Catalog

```bash
python scraper.py
```

This will create:
- `shl_assessments.json` - Structured assessment data
- `shl_assessments.csv` - CSV format for viewing

### 2. Run Evaluation and Generate Test Predictions

```bash
python evaluate.py
```

This will:
- Evaluate the system on training data
- Calculate Mean Recall@10
- Generate `test_predictions.csv` for submission
- Create `evaluation_report.json` with detailed metrics

### 3. Start the API Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### 4. Open Frontend

Open `index.html` in your browser or serve it using:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000`

## 📡 API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-02T10:30:00",
  "version": "1.0.0",
  "service": "SHL Assessment Recommendation API"
}
```

### Get Recommendations

```bash
POST /recommend
Content-Type: application/json

{
  "query": "I am hiring for Java developers who can collaborate with teams"
}
```

Response:
```json
{
  "query": "I am hiring for Java developers...",
  "recommendations": [
    {
      "assessment_name": "Java Programming Test",
      "url": "https://www.shl.com/...",
      "relevance_score": 0.8542,
      "category": "skills",
      "test_type": "K"
    },
    ...
  ],
  "count": 10
}
```

## 🧪 Testing

### Sample Queries

1. "I am hiring for Java developers who can also collaborate effectively with my business teams."
2. "Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript."
3. "I am hiring for an analyst and want to screen using Cognitive and personality tests."

### Run Tests

```bash
# Test the scraper
python scraper.py

# Test recommendations
python recommender.py

# Run full evaluation
python evaluate.py
```

## 📊 Evaluation Metrics

The system uses **Mean Recall@10**:

```
Recall@K = (Number of relevant assessments in top K) / (Total relevant assessments)
Mean Recall@K = Average of Recall@K across all queries
```

## 🎨 Features

### Intelligent Balancing

The system automatically balances recommendations when a query spans multiple domains:

- **Technical Skills** (Type K): Java, Python, SQL, etc.
- **Personality & Behavior** (Type P): Collaboration, teamwork, leadership
- **Cognitive Abilities** (Type A): Reasoning, problem-solving
- **Situational Judgment** (Type S): Decision-making scenarios

Example: A query for "Java developer who collaborates well" will return both:
- Technical assessments (Java, programming skills)
- Soft skill assessments (teamwork, collaboration)

### Semantic Understanding

Uses `sentence-transformers` for deep semantic understanding:
- Understands context beyond keywords
- Handles synonyms and related terms
- Works with full job descriptions or short queries

## 📁 Project Structure

```
SHL pro/
├── scraper.py              # Web scraper for SHL catalog
├── recommender.py          # Recommendation engine
├── app.py                  # Flask API server
├── evaluate.py             # Evaluation and prediction generation
├── index.html              # Frontend web application
├── requirements.txt        # Python dependencies
├── shl_assessments.json    # Scraped assessment data
├── test_predictions.csv    # Test set predictions (for submission)
└── evaluation_report.json  # Evaluation metrics
```

## 🛠️ Technology Stack

- **Backend**: Flask, Python 3.8+
- **NLP**: Sentence Transformers (all-MiniLM-L6-v2)
- **ML**: scikit-learn, numpy, pandas
- **Web Scraping**: BeautifulSoup4, requests
- **Frontend**: HTML, CSS, JavaScript (Vanilla)

## 📝 Submission Files

1. ✅ **API Endpoint**: Available after deployment
2. ✅ **GitHub Repository**: Complete code with experiments
3. ✅ **Frontend URL**: Web application interface
4. ✅ **Approach Document**: 2-page methodology (see APPROACH.md)
5. ✅ **Test Predictions**: `test_predictions.csv` in required format

## 🚢 Deployment

### Deploy API (Example with Render/Railway)

1. Push code to GitHub
2. Connect to deployment platform
3. Set environment variables if needed
4. Deploy and get public URL

### Deploy Frontend (Example with Netlify/Vercel)

1. Update API_URL in index.html to deployed API
2. Upload index.html to hosting platform
3. Get public URL

## 📈 Performance Optimization

The system employs several optimization strategies:

1. **Pre-computed Embeddings**: Assessments are embedded once and cached
2. **Efficient Vector Search**: Cosine similarity for fast retrieval
3. **Smart Balancing**: Ensures diverse, relevant results
4. **Caching**: Embeddings stored in pickle format for instant loading

## 🤝 Contributing

This is a take-home assignment project. For questions or issues, please contact the project maintainer.

## 📄 License

This project is created for the SHL AI Intern assessment.

## 👤 Author

SHL AI Intern Assignment Submission
- Project: Assessment Recommendation System
- Date: March 2026

---

**Note**: This system is designed to meet all requirements specified in the SHL GenAI assignment, including:
- ✅ Scraping 377+ Individual Test Solutions
- ✅ LLM/Retrieval-based recommendation
- ✅ Evaluation on training data
- ✅ API with specified endpoints
- ✅ Web frontend
- ✅ Test predictions in CSV format
- ✅ Balanced recommendations
