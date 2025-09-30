"""
ML Model Performance Tracker for CMP
Tracks accuracy and performance metrics for AI/ML models
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import json
from pathlib import Path
import statistics

class ModelType(Enum):
    OCR = "ocr"
    DOCUMENT_CLASSIFIER = "document_classifier"
    EXPENSE_CATEGORIZER = "expense_categorizer"
    ANOMALY_DETECTOR = "anomaly_detector"

class PredictionResult:
    def __init__(self, model_type: ModelType, prediction: Any, actual: Any = None,
                 confidence: float = 0.0, processing_time: float = 0.0):
        self.id = f"pred_{int(datetime.now().timestamp() * 1000000)}"
        self.model_type = model_type
        self.prediction = prediction
        self.actual = actual
        self.confidence = confidence
        self.processing_time = processing_time
        self.timestamp = datetime.now()
        self.is_correct = None if actual is None else prediction == actual

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "model_type": self.model_type.value,
            "prediction": str(self.prediction),
            "actual": str(self.actual) if self.actual is not None else None,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat(),
            "is_correct": self.is_correct
        }

class MLPerformanceTracker:
    def __init__(self):
        self.storage_file = Path("local_storage/ml_performance.json")
        self.storage_file.parent.mkdir(exist_ok=True)
        self.predictions: List[PredictionResult] = []
        self._load_from_storage()

    def _load_from_storage(self):
        """Load prediction results from persistent storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for pred_data in data:
                        pred = PredictionResult(
                            ModelType(pred_data['model_type']),
                            pred_data['prediction'],
                            pred_data.get('actual'),
                            pred_data['confidence'],
                            pred_data['processing_time']
                        )
                        pred.id = pred_data['id']
                        pred.timestamp = datetime.fromisoformat(pred_data['timestamp'])
                        pred.is_correct = pred_data.get('is_correct')
                        self.predictions.append(pred)
            except Exception as e:
                print(f"Error loading ML performance data: {e}")

    def _save_to_storage(self):
        """Save prediction results to persistent storage"""
        try:
            # Keep only last 1000 predictions to avoid file bloat
            recent_predictions = sorted(self.predictions, key=lambda x: x.timestamp, reverse=True)[:1000]
            with open(self.storage_file, 'w') as f:
                json.dump([pred.to_dict() for pred in recent_predictions], f, indent=2)
            self.predictions = recent_predictions
        except Exception as e:
            print(f"Error saving ML performance data: {e}")

    def record_prediction(self, model_type: ModelType, prediction: Any, 
                         confidence: float = 0.0, processing_time: float = 0.0) -> str:
        """Record a new prediction"""
        pred = PredictionResult(model_type, prediction, None, confidence, processing_time)
        self.predictions.append(pred)
        self._save_to_storage()
        return pred.id

    def update_prediction_result(self, prediction_id: str, actual: Any) -> bool:
        """Update a prediction with the actual result"""
        for pred in self.predictions:
            if pred.id == prediction_id:
                pred.actual = actual
                pred.is_correct = pred.prediction == actual
                self._save_to_storage()
                return True
        return False

    def get_accuracy(self, model_type: Optional[ModelType] = None, days: int = 30) -> float:
        """Calculate accuracy for a model type within specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        relevant_predictions = [
            pred for pred in self.predictions
            if pred.timestamp >= cutoff and 
            pred.is_correct is not None and
            (model_type is None or pred.model_type == model_type)
        ]
        
        if not relevant_predictions:
            return 0.0
        
        correct_predictions = sum(1 for pred in relevant_predictions if pred.is_correct)
        return (correct_predictions / len(relevant_predictions)) * 100

    def get_average_processing_time(self, model_type: Optional[ModelType] = None, days: int = 30) -> float:
        """Calculate average processing time for a model type within specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        relevant_predictions = [
            pred for pred in self.predictions
            if pred.timestamp >= cutoff and 
            pred.processing_time > 0 and
            (model_type is None or pred.model_type == model_type)
        ]
        
        if not relevant_predictions:
            return 0.0
        
        processing_times = [pred.processing_time for pred in relevant_predictions]
        return statistics.mean(processing_times)

    def get_confidence_distribution(self, model_type: Optional[ModelType] = None, days: int = 30) -> Dict[str, float]:
        """Get confidence score distribution"""
        cutoff = datetime.now() - timedelta(days=days)
        relevant_predictions = [
            pred for pred in self.predictions
            if pred.timestamp >= cutoff and
            (model_type is None or pred.model_type == model_type)
        ]
        
        if not relevant_predictions:
            return {"high": 0.0, "medium": 0.0, "low": 0.0}
        
        high_confidence = sum(1 for pred in relevant_predictions if pred.confidence >= 0.8)
        medium_confidence = sum(1 for pred in relevant_predictions if 0.5 <= pred.confidence < 0.8)
        low_confidence = sum(1 for pred in relevant_predictions if pred.confidence < 0.5)
        
        total = len(relevant_predictions)
        return {
            "high": (high_confidence / total) * 100,
            "medium": (medium_confidence / total) * 100,
            "low": (low_confidence / total) * 100
        }

    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary for all models"""
        summary = {}
        
        for model_type in ModelType:
            accuracy = self.get_accuracy(model_type)
            avg_time = self.get_average_processing_time(model_type)
            confidence_dist = self.get_confidence_distribution(model_type)
            
            summary[model_type.value] = {
                "accuracy": accuracy,
                "average_processing_time": avg_time,
                "confidence_distribution": confidence_dist,
                "total_predictions": len([p for p in self.predictions if p.model_type == model_type])
            }
        
        # Overall performance
        summary["overall"] = {
            "accuracy": self.get_accuracy(),
            "average_processing_time": self.get_average_processing_time(),
            "confidence_distribution": self.get_confidence_distribution(),
            "total_predictions": len(self.predictions)
        }
        
        return summary

# Global ML performance tracker instance
ml_performance_tracker = MLPerformanceTracker()

def get_ml_performance_tracker() -> MLPerformanceTracker:
    """Get the global ML performance tracker instance"""
    return ml_performance_tracker

# Seed some sample data if empty
def seed_sample_data():
    """Add some sample ML performance data for demonstration"""
    if len(ml_performance_tracker.predictions) == 0:
        import random
        
        # Add some sample OCR predictions
        for _ in range(50):
            tracker = get_ml_performance_tracker()
            pred_id = tracker.record_prediction(
                ModelType.OCR,
                f"sample_text_{random.randint(1000, 9999)}",
                random.uniform(0.7, 0.99),
                random.uniform(0.5, 3.0)
            )
            # Simulate some being verified
            if random.random() > 0.3:
                tracker.update_prediction_result(pred_id, f"sample_text_{random.randint(1000, 9999)}")

# Seed data on module import
seed_sample_data()