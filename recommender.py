"""
SHL Assessment Recommendation Engine
Uses embeddings and vector similarity for intelligent recommendations
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import os
import pickle


class AssessmentRecommender:
    def __init__(self, assessments_file: str = 'shl_assessments.json'):
        """Initialize the recommendation engine"""
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.assessments = []
        self.embeddings = None
        self.embeddings_file = 'assessment_embeddings.pkl'
        
        # Load assessments
        self.load_assessments(assessments_file)
        
        # Load or create embeddings
        if os.path.exists(self.embeddings_file):
            self.load_embeddings()
        else:
            self.create_embeddings()
    
    def load_assessments(self, filename: str):
        """Load assessment data"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.assessments = json.load(f)
            print(f"Loaded {len(self.assessments)} assessments")
        except Exception as e:
            print(f"Error loading assessments: {e}")
            self.assessments = []
    
    def create_embeddings(self):
        """Create embeddings for all assessments"""
        print("Creating embeddings for assessments...")
        
        # Create rich text representations for each assessment
        texts = []
        for assessment in self.assessments:
            # Combine multiple fields for better semantic representation
            text = f"{assessment['name']}. "
            text += f"Category: {assessment['category']}. "
            text += f"Test Type: {assessment['test_type']}. "
            text += f"{assessment.get('description', '')}"
            texts.append(text)
        
        # Create embeddings
        self.embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Save embeddings
        self.save_embeddings()
        
        print(f"Created embeddings with shape: {self.embeddings.shape}")
    
    def save_embeddings(self):
        """Save embeddings to file"""
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(self.embeddings, f)
        print(f"Saved embeddings to {self.embeddings_file}")
    
    def load_embeddings(self):
        """Load embeddings from file"""
        with open(self.embeddings_file, 'rb') as f:
            self.embeddings = pickle.load(f)
        print(f"Loaded embeddings with shape: {self.embeddings.shape}")
    
    def recommend(self, query: str, top_k: int = 10, balance_skills: bool = True) -> List[Dict]:
        """
        Recommend assessments based on a query
        
        Args:
            query: Natural language query or job description
            top_k: Number of recommendations to return (max 10)
            balance_skills: Whether to balance hard and soft skills
        
        Returns:
            List of recommended assessments with scores
        """
        # Encode the query
        query_embedding = self.model.encode([query])[0]
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]

        # Rank all assessments (not just top_k*3) so balancing can pull K/P items reliably
        ranked_indices = np.argsort(similarities)[::-1]

        # Create scored ranked list
        ranked_candidates = []
        for idx in ranked_indices:
            assessment = self.assessments[idx].copy()
            assessment['score'] = float(similarities[idx])
            ranked_candidates.append(assessment)
        
        # Balance skills if requested
        if balance_skills and self._needs_balance(query):
            recommendations = self._balance_recommendations(ranked_candidates, top_k)
        else:
            recommendations = ranked_candidates[:top_k]
        
        # Ensure we return at least 5 and at most 10
        if len(recommendations) < 5:
            recommendations = ranked_candidates[:5]
        recommendations = recommendations[:10]
        
        return recommendations
    
    def _needs_balance(self, query: str) -> bool:
        """Determine if query needs balanced recommendations"""
        query_lower = query.lower()
        
        # Check for both technical and soft skill keywords
        technical_keywords = ['java', 'python', 'programming', 'coding', 'sql', 'javascript', 'technical', 'development', '.net', 'c++', 'c#']
        # Soft skill keywords - catch root forms and variants
        soft_keywords = ['collaborat', 'communicat', 'teamwork', 'leadership', 'personality', 'behavior', 'motivat', 'soft skill', 'interperson', 'stakeholder']
        
        has_technical = any(keyword in query_lower for keyword in technical_keywords)
        has_soft = any(keyword in query_lower for keyword in soft_keywords)
        
        return has_technical and has_soft
    
    def _balance_recommendations(self, candidates: List[Dict], top_k: int) -> List[Dict]:
        """Balance recommendations between different test types for mixed-skill queries."""
        by_type = {
            'K': [],  # Knowledge & Skills
            'P': [],  # Personality & Behavior
            'A': [],  # Aptitude/Cognitive
            'S': [],  # Situational
            'O': []   # Other
        }

        for candidate in candidates:
            test_type = candidate.get('test_type', 'O')
            if test_type not in by_type:
                test_type = 'O'
            by_type[test_type].append(candidate)

        # If both technical and personality pools exist, enforce representation from both
        if by_type['K'] and by_type['P']:
            selected = []
            selected_urls = set()

            # Reserve roughly half-half between K and P
            k_target = top_k // 2
            p_target = top_k // 2

            for item in by_type['K'][:k_target]:
                selected.append(item)
                selected_urls.add(item['url'])

            for item in by_type['P'][:p_target]:
                if item['url'] not in selected_urls:
                    selected.append(item)
                    selected_urls.add(item['url'])

            # Fill remaining slots by global relevance from all types
            if len(selected) < top_k:
                for item in candidates:
                    if item['url'] in selected_urls:
                        continue
                    selected.append(item)
                    selected_urls.add(item['url'])
                    if len(selected) >= top_k:
                        break

            selected = selected[:top_k]
            selected.sort(key=lambda x: x['score'], reverse=True)
            return selected

        # Fallback: just top relevance
        return candidates[:top_k]
    
    def evaluate(self, test_queries: List[Tuple[str, List[str]]]) -> Dict:
        """
        Evaluate recommendation quality
        
        Args:
            test_queries: List of (query, relevant_urls) tuples
        
        Returns:
            Dictionary with evaluation metrics
        """
        recalls = []
        
        for query, relevant_urls in test_queries:
            recommendations = self.recommend(query, top_k=10)
            recommended_urls = [r['url'] for r in recommendations]
            
            # Calculate recall@10
            relevant_found = sum(1 for url in relevant_urls if url in recommended_urls)
            recall = relevant_found / len(relevant_urls) if relevant_urls else 0
            recalls.append(recall)
        
        mean_recall = np.mean(recalls) if recalls else 0
        
        return {
            'mean_recall_at_10': mean_recall,
            'individual_recalls': recalls,
            'num_queries': len(test_queries)
        }
    
    def format_recommendation(self, recommendation: Dict) -> Dict:
        """Format recommendation for API response"""
        return {
            'assessment_name': recommendation['name'],
            'url': recommendation['url'],
            'relevance_score': round(recommendation['score'], 4),
            'category': recommendation.get('category', ''),
            'test_type': recommendation.get('test_type', '')
        }


if __name__ == "__main__":
    # Test the recommender
    recommender = AssessmentRecommender()
    
    # Test queries
    test_queries = [
        "I am hiring for Java developers who can also collaborate effectively with my business teams.",
        "Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript.",
        "I am hiring for an analyst and want to screen using Cognitive and personality tests"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("="*80)
        
        recommendations = recommender.recommend(query)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['name']}")
            print(f"   Score: {rec['score']:.4f}, Type: {rec['test_type']}, Category: {rec['category']}")
            print(f"   URL: {rec['url']}\n")
