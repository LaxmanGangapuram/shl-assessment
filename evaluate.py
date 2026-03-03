"""
Evaluation Script for SHL Recommendation System
Evaluates performance on training set and generates predictions for test set
"""

import pandas as pd
import numpy as np
from recommender import AssessmentRecommender
from typing import List, Dict
import json


def load_train_data(filename: str = 'Gen_AI Dataset.xlsx') -> pd.DataFrame:
    """Load training data from Excel file"""
    df = pd.read_excel(filename, sheet_name='Train-Set')
    return df


def load_test_data(filename: str = 'Gen_AI Dataset.xlsx') -> pd.DataFrame:
    """Load test data from Excel file"""
    df = pd.read_excel(filename, sheet_name='Test-Set')
    return df


def prepare_train_queries(df: pd.DataFrame) -> List[tuple]:
    """Prepare training queries with their relevant URLs"""
    queries_dict = {}
    
    for _, row in df.iterrows():
        query = row['Query']
        url = row['Assessment_url']
        
        if query not in queries_dict:
            queries_dict[query] = []
        
        queries_dict[query].append(url)
    
    return [(query, urls) for query, urls in queries_dict.items()]


def calculate_recall_at_k(recommended_urls: List[str], relevant_urls: List[str], k: int = 10) -> float:
    """Calculate Recall@K"""
    recommended_urls = recommended_urls[:k]
    
    # Count how many relevant URLs are in the recommendations
    relevant_found = sum(1 for url in relevant_urls if url in recommended_urls)
    
    # Recall = relevant found / total relevant
    recall = relevant_found / len(relevant_urls) if relevant_urls else 0
    
    return recall


def evaluate_on_train(recommender: AssessmentRecommender, train_queries: List[tuple]) -> Dict:
    """Evaluate recommender on training data"""
    print("\n" + "="*80)
    print("EVALUATING ON TRAINING DATA")
    print("="*80 + "\n")
    
    recalls = []
    detailed_results = []
    
    for query, relevant_urls in train_queries:
        # Get recommendations
        recommendations = recommender.recommend(query, top_k=10)
        recommended_urls = [rec['url'] for rec in recommendations]
        
        # Calculate recall
        recall = calculate_recall_at_k(recommended_urls, relevant_urls, k=10)
        recalls.append(recall)
        
        # Store detailed results
        result = {
            'query': query,
            'num_relevant': len(relevant_urls),
            'num_found': sum(1 for url in relevant_urls if url in recommended_urls),
            'recall': recall
        }
        detailed_results.append(result)
        
        print(f"Query: {query[:60]}...")
        print(f"Relevant URLs: {len(relevant_urls)}")
        print(f"Found in top 10: {result['num_found']}")
        print(f"Recall@10: {recall:.4f}")
        print("-" * 80)
    
    # Calculate mean recall
    mean_recall = np.mean(recalls)
    
    print(f"\n{'='*80}")
    print(f"MEAN RECALL@10: {mean_recall:.4f}")
    print(f"{'='*80}\n")
    
    return {
        'mean_recall_at_10': mean_recall,
        'individual_recalls': recalls,
        'detailed_results': detailed_results,
        'num_queries': len(train_queries)
    }


def generate_test_predictions(recommender: AssessmentRecommender, test_df: pd.DataFrame, 
                              output_file: str = 'test_predictions.csv'):
    """Generate predictions for test set"""
    print("\n" + "="*80)
    print("GENERATING TEST PREDICTIONS")
    print("="*80 + "\n")
    
    predictions = []
    
    for idx, row in test_df.iterrows():
        query = row['Query']
        
        print(f"\nQuery {idx + 1}: {query[:60]}...")
        
        # Get recommendations
        recommendations = recommender.recommend(query, top_k=10)
        
        # Add to predictions
        for rec in recommendations:
            predictions.append({
                'Query': query,
                'Assessment_url': rec['url']
            })
        
        print(f"Generated {len(recommendations)} recommendations")
    
    # Create DataFrame and save
    predictions_df = pd.DataFrame(predictions)
    predictions_df.to_csv(output_file, index=False)
    
    print(f"\n{'='*80}")
    print(f"Predictions saved to: {output_file}")
    print(f"Total rows: {len(predictions_df)}")
    print(f"{'='*80}\n")
    
    return predictions_df


def save_evaluation_report(eval_results: Dict, output_file: str = 'evaluation_report.json'):
    """Save evaluation results to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(eval_results, f, indent=2)
    
    print(f"Evaluation report saved to: {output_file}")


def main():
    """Main evaluation and prediction generation"""
    print("\n" + "="*80)
    print("SHL ASSESSMENT RECOMMENDATION SYSTEM - EVALUATION")
    print("="*80 + "\n")
    
    # Initialize recommender
    print("Initializing recommendation engine...")
    recommender = AssessmentRecommender()
    
    # Load data
    print("\nLoading datasets...")
    train_df = load_train_data()
    test_df = load_test_data()
    
    print(f"Training queries: {len(train_df)}")
    print(f"Test queries: {len(test_df)}")
    
    # Prepare training queries
    train_queries = prepare_train_queries(train_df)
    print(f"Unique training queries: {len(train_queries)}")
    
    # Evaluate on training data
    eval_results = evaluate_on_train(recommender, train_queries)
    
    # Save evaluation report
    save_evaluation_report(eval_results)
    
    # Generate test predictions
    predictions_df = generate_test_predictions(recommender, test_df)
    
    # Display sample predictions
    print("\nSample predictions:")
    print(predictions_df.head(10))
    
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80 + "\n")
    
    print("Summary:")
    print(f"  - Mean Recall@10 on training: {eval_results['mean_recall_at_10']:.4f}")
    print(f"  - Test predictions generated: {len(predictions_df)} rows")
    print(f"  - Output files:")
    print(f"    * test_predictions.csv")
    print(f"    * evaluation_report.json")


if __name__ == "__main__":
    main()
