"""
AI and Machine Learning Utilities for CMP

Provides intelligent transaction categorization, document analysis,
and decision-making capabilities for AI agents.
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from textblob import TextBlob
import pickle
import os
from pathlib import Path

from ..logging_config import get_logger

logger = get_logger("ai_utils")


class TransactionCategorizer:
    """
    Intelligent transaction categorization using machine learning.
    """
    
    def __init__(self):
        self.model = None
        self.categories = [
            "Office Supplies", "Travel & Transport", "Utilities", "Marketing",
            "Software & Technology", "Professional Services", "Food & Beverage",
            "Equipment", "Rent & Facilities", "Insurance", "Taxes", "Banking Fees",
            "Maintenance", "Telecommunications", "Training & Education", "Other"
        ]
        self.model_path = Path("local_storage/ml_models/transaction_categorizer.pkl")
        self._load_or_train_model()
    
    def _load_or_train_model(self):
        """Load existing model or train a new one"""
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("Loaded existing transaction categorizer model")
            else:
                self._train_initial_model()
        except Exception as e:
            logger.warning(f"Error loading model, training new one: {e}")
            self._train_initial_model()
    
    def _train_initial_model(self):
        """Train initial model with sample data"""
        logger.info("Training new transaction categorizer model...")
        
        # Sample training data (in production, this would come from historical data)
        training_data = [
            ("Office Depot supplies invoice", "Office Supplies"),
            ("Staples printer paper", "Office Supplies"),
            ("Uber ride to client meeting", "Travel & Transport"),
            ("Emirates airline ticket", "Travel & Transport"),
            ("DEWA electricity bill", "Utilities"),
            ("Etisalat internet service", "Telecommunications"),
            ("Google Ads campaign", "Marketing"),
            ("Facebook advertising", "Marketing"),
            ("Microsoft Office subscription", "Software & Technology"),
            ("Adobe Creative Cloud", "Software & Technology"),
            ("Legal consultation fee", "Professional Services"),
            ("Accounting services", "Professional Services"),
            ("Restaurant client lunch", "Food & Beverage"),
            ("Coffee shop meeting", "Food & Beverage"),
            ("Laptop purchase", "Equipment"),
            ("Office chair", "Equipment"),
            ("Office rent payment", "Rent & Facilities"),
            ("Cleaning service", "Maintenance"),
            ("Business insurance premium", "Insurance"),
            ("VAT payment", "Taxes"),
            ("Bank transfer fee", "Banking Fees"),
            ("Training course fee", "Training & Education"),
            ("Conference ticket", "Training & Education"),
            ("Repair service", "Maintenance"),
            ("Mobile phone bill", "Telecommunications"),
        ]
        
        descriptions, labels = zip(*training_data)
        
        # Create and train the model
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(lowercase=True, stop_words='english', max_features=1000)),
            ('classifier', MultinomialNB())
        ])
        
        self.model.fit(descriptions, labels)
        
        # Save the model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        logger.info("Transaction categorizer model trained and saved")
    
    def categorize(self, description: str, amount: float = None) -> Dict[str, Any]:
        """
        Categorize a transaction based on description and amount.
        
        Returns:
            Dict with category, confidence, and reasoning
        """
        if not self.model:
            return {"category": "Other", "confidence": 0.0, "reasoning": "Model not available"}
        
        try:
            # Clean the description
            clean_desc = self._clean_description(description)
            
            # Get prediction and probabilities
            prediction = self.model.predict([clean_desc])[0]
            probabilities = self.model.predict_proba([clean_desc])[0]
            confidence = max(probabilities)
            
            # Additional context-based adjustments
            reasoning = self._get_categorization_reasoning(clean_desc, prediction, amount)
            
            return {
                "category": prediction,
                "confidence": float(confidence),
                "reasoning": reasoning,
                "suggested_categories": self._get_top_suggestions(probabilities)
            }
        
        except Exception as e:
            logger.error(f"Error categorizing transaction: {e}")
            return {"category": "Other", "confidence": 0.0, "reasoning": f"Error: {e}"}
    
    def _clean_description(self, description: str) -> str:
        """Clean and normalize transaction description"""
        # Convert to lowercase
        clean = description.lower()
        
        # Remove common payment-related words that don't help categorization
        clean = re.sub(r'\b(payment|invoice|bill|charge|fee|purchase|order)\b', '', clean)
        
        # Remove numbers and special characters (except letters and spaces)
        clean = re.sub(r'[^a-zA-Z\s]', ' ', clean)
        
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        
        return clean
    
    def _get_categorization_reasoning(self, description: str, category: str, amount: float = None) -> str:
        """Generate human-readable reasoning for the categorization"""
        reasoning_parts = []
        
        # Keywords that influenced the decision
        keywords = {
            "Office Supplies": ["office", "supplies", "paper", "staples", "depot"],
            "Travel & Transport": ["uber", "taxi", "airline", "flight", "hotel", "travel"],
            "Utilities": ["dewa", "electricity", "water", "gas", "utility"],
            "Marketing": ["ads", "advertising", "marketing", "promotion", "campaign"],
            "Software & Technology": ["microsoft", "google", "adobe", "software", "cloud", "saas"],
            "Professional Services": ["legal", "accounting", "consulting", "professional"],
            "Food & Beverage": ["restaurant", "coffee", "food", "lunch", "dinner"],
            "Equipment": ["laptop", "computer", "chair", "desk", "equipment"],
            "Telecommunications": ["etisalat", "du", "phone", "internet", "telecom"],
        }
        
        if category in keywords:
            found_keywords = [kw for kw in keywords[category] if kw in description.lower()]
            if found_keywords:
                reasoning_parts.append(f"Contains keywords: {', '.join(found_keywords)}")
        
        # Amount-based reasoning
        if amount:
            if amount < 100:
                reasoning_parts.append("Small amount suggests routine expense")
            elif amount > 5000:
                reasoning_parts.append("Large amount suggests equipment or major service")
        
        return " | ".join(reasoning_parts) if reasoning_parts else "Based on description pattern matching"
    
    def _get_top_suggestions(self, probabilities: np.ndarray, top_n: int = 3) -> List[Dict[str, Any]]:
        """Get top N category suggestions with confidence scores"""
        top_indices = np.argsort(probabilities)[-top_n:][::-1]
        
        suggestions = []
        for idx in top_indices:
            suggestions.append({
                "category": self.categories[idx] if idx < len(self.categories) else "Other",
                "confidence": float(probabilities[idx])
            })
        
        return suggestions
    
    def retrain_with_feedback(self, description: str, correct_category: str):
        """Update model with user feedback (simplified version)"""
        # In production, this would retrain the model with the new data point
        logger.info(f"Received feedback: '{description}' -> '{correct_category}'")
        # For now, just log the feedback for future training


class DocumentAnalyzer:
    """
    Intelligent document analysis for invoices, receipts, and financial documents.
    """
    
    def __init__(self):
        self.vendor_patterns = self._load_vendor_patterns()
    
    def _load_vendor_patterns(self) -> Dict[str, Dict]:
        """Load known vendor patterns for UAE market"""
        return {
            "emirates_nbd": {
                "patterns": ["emirates nbd", "enbd", "emirates islamic"],
                "category": "Banking Fees",
                "country": "UAE"
            },
            "etisalat": {
                "patterns": ["etisalat", "etisalat.ae"],
                "category": "Telecommunications",
                "country": "UAE"
            },
            "dewa": {
                "patterns": ["dewa", "dubai electricity", "water authority"],
                "category": "Utilities",
                "country": "UAE"
            },
            "emirates": {
                "patterns": ["emirates airline", "emirates.com", "ek air"],
                "category": "Travel & Transport",
                "country": "UAE"
            },
            "carrefour": {
                "patterns": ["carrefour", "carrefour uae"],
                "category": "Office Supplies",
                "country": "UAE"
            }
        }
    
    def analyze_document(self, text: str, ocr_data: Dict = None) -> Dict[str, Any]:
        """
        Perform intelligent analysis of document text.
        
        Returns:
            Comprehensive analysis including vendor, amounts, categories, etc.
        """
        analysis = {
            "vendor": self._identify_vendor(text),
            "amounts": self._extract_amounts(text),
            "dates": self._extract_dates(text),
            "categories": self._suggest_categories(text),
            "language": self._detect_language(text),
            "confidence": 0.0,
            "key_entities": self._extract_entities(text),
            "document_type": self._classify_document_type(text, ocr_data)
        }
        
        # Calculate overall confidence
        analysis["confidence"] = self._calculate_confidence(analysis)
        
        return analysis
    
    def _identify_vendor(self, text: str) -> Dict[str, Any]:
        """Identify vendor/merchant from document text"""
        text_lower = text.lower()
        
        for vendor_key, vendor_info in self.vendor_patterns.items():
            for pattern in vendor_info["patterns"]:
                if pattern.lower() in text_lower:
                    return {
                        "name": vendor_key,
                        "confidence": 0.9,
                        "suggested_category": vendor_info["category"],
                        "country": vendor_info.get("country", "Unknown")
                    }
        
        # Try to extract business names using simple heuristics
        potential_vendors = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        if potential_vendors:
            return {
                "name": potential_vendors[0],
                "confidence": 0.6,
                "suggested_category": "Other",
                "country": "Unknown"
            }
        
        return {"name": "Unknown", "confidence": 0.0, "suggested_category": "Other", "country": "Unknown"}
    
    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from text"""
        # Patterns for different currency formats
        patterns = [
            r'AED\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # AED 1,000.00
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*AED',  # 1,000.00 AED
            r'د\.إ\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # د.إ 1,000.00 (Arabic)
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*د\.إ',  # 1,000.00 د.إ
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',   # $1,000.00
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',        # 1,000.00 (fallback)
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                amount_str = match.group(1) if match.groups() else match.group(0)
                try:
                    amount = float(amount_str.replace(',', ''))
                    amounts.append({
                        "amount": amount,
                        "currency": "AED",  # Default to AED for UAE
                        "raw_text": match.group(0),
                        "confidence": 0.8
                    })
                except ValueError:
                    continue
        
        # Sort by amount (descending) and remove duplicates
        amounts = sorted(amounts, key=lambda x: x["amount"], reverse=True)
        seen_amounts = set()
        unique_amounts = []
        
        for amount_info in amounts:
            amount_key = amount_info["amount"]
            if amount_key not in seen_amounts:
                seen_amounts.add(amount_key)
                unique_amounts.append(amount_info)
        
        return unique_amounts[:5]  # Return top 5 amounts
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from document text"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY
            r'\d{1,2}\.\d{1,2}\.\d{4}' # DD.MM.YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates
    
    def _suggest_categories(self, text: str) -> List[Dict[str, Any]]:
        """Suggest expense categories based on document content"""
        categorizer = TransactionCategorizer()
        result = categorizer.categorize(text)
        
        return [{
            "category": result["category"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"]
        }]
    
    def _detect_language(self, text: str) -> Dict[str, Any]:
        """Detect document language"""
        try:
            blob = TextBlob(text)
            detected_lang = blob.detect_language()
            
            lang_names = {
                'en': 'English',
                'ar': 'Arabic',
                'fr': 'French',
                'es': 'Spanish'
            }
            
            return {
                "code": detected_lang,
                "name": lang_names.get(detected_lang, "Unknown"),
                "confidence": 0.8
            }
        except:
            return {"code": "en", "name": "English", "confidence": 0.5}
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract key entities like emails, phone numbers, addresses"""
        entities = {
            "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
            "phones": re.findall(r'(?:\+971|0)[- ]?(?:\d[- ]?){8,9}', text),  # UAE phone format
            "websites": re.findall(r'(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text),
            "tax_numbers": re.findall(r'TRN[:\s]*(\d{15})', text, re.IGNORECASE)  # UAE TRN
        }
        
        return entities
    
    def _classify_document_type(self, text: str, ocr_data: Dict = None) -> Dict[str, Any]:
        """Classify the type of document"""
        text_lower = text.lower()
        
        document_types = {
            "invoice": ["invoice", "bill", "فاتورة"],
            "receipt": ["receipt", "إيصال"],
            "statement": ["statement", "كشف"],
            "contract": ["contract", "agreement", "عقد"],
            "report": ["report", "تقرير"]
        }
        
        for doc_type, keywords in document_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return {"type": doc_type, "confidence": 0.8}
        
        return {"type": "unknown", "confidence": 0.3}
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """Calculate overall analysis confidence"""
        confidence_factors = []
        
        if analysis["vendor"]["confidence"] > 0:
            confidence_factors.append(analysis["vendor"]["confidence"])
        
        if analysis["amounts"]:
            avg_amount_confidence = sum(a["confidence"] for a in analysis["amounts"]) / len(analysis["amounts"])
            confidence_factors.append(avg_amount_confidence)
        
        if analysis["language"]["confidence"] > 0:
            confidence_factors.append(analysis["language"]["confidence"])
        
        if analysis["document_type"]["confidence"] > 0:
            confidence_factors.append(analysis["document_type"]["confidence"])
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0


class BusinessInsightEngine:
    """
    Generate business insights from financial data using AI.
    """
    
    def __init__(self):
        self.categorizer = TransactionCategorizer()
        self.analyzer = DocumentAnalyzer()
    
    def analyze_spending_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze spending patterns and generate insights"""
        if not transactions:
            return {"insights": [], "recommendations": [], "trends": {}}
        
        df = pd.DataFrame(transactions)
        insights = []
        recommendations = []
        
        # Category analysis
        if 'category' in df.columns and 'amount' in df.columns:
            category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
            
            top_category = category_spending.index[0]
            top_amount = category_spending.iloc[0]
            total_spending = category_spending.sum()
            
            insights.append({
                "type": "spending_concentration",
                "message": f"Top spending category is {top_category} with AED {top_amount:,.2f} ({(top_amount/total_spending)*100:.1f}% of total)",
                "importance": "high"
            })
            
            # Check for unusual patterns
            if (top_amount / total_spending) > 0.4:
                recommendations.append({
                    "type": "diversification",
                    "message": f"Consider reviewing {top_category} expenses as they represent a large portion of spending",
                    "action": "review_category",
                    "category": top_category
                })
        
        # Trend analysis
        if 'date' in df.columns:
            monthly_trends = self._analyze_monthly_trends(df)
            insights.extend(monthly_trends["insights"])
            recommendations.extend(monthly_trends["recommendations"])
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "trends": self._calculate_trends(df),
            "summary": {
                "total_transactions": len(transactions),
                "total_amount": df['amount'].sum() if 'amount' in df.columns else 0,
                "avg_transaction": df['amount'].mean() if 'amount' in df.columns else 0
            }
        }
    
    def _analyze_monthly_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze monthly spending trends"""
        insights = []
        recommendations = []
        
        # This is a simplified version - in production you'd do proper time series analysis
        if len(df) >= 2:
            recent_avg = df.tail(10)['amount'].mean() if 'amount' in df.columns else 0
            older_avg = df.head(10)['amount'].mean() if 'amount' in df.columns else 0
            
            if recent_avg > older_avg * 1.2:
                insights.append({
                    "type": "increasing_trend",
                    "message": f"Spending has increased by {((recent_avg/older_avg-1)*100):.1f}% in recent transactions",
                    "importance": "medium"
                })
                
                recommendations.append({
                    "type": "budget_review",
                    "message": "Consider reviewing budget due to increasing spending trend",
                    "action": "budget_analysis"
                })
        
        return {"insights": insights, "recommendations": recommendations}
    
    def _calculate_trends(self, df: pd.DataFrame) -> Dict:
        """Calculate basic trend metrics"""
        trends = {}
        
        if 'amount' in df.columns and len(df) > 0:
            trends['spending_trend'] = 'stable'  # Simplified
            trends['volatility'] = df['amount'].std() if len(df) > 1 else 0
            trends['average_transaction'] = df['amount'].mean()
            trends['largest_transaction'] = df['amount'].max()
        
        return trends
    
    def generate_recommendations(self, analysis_results: Dict) -> List[Dict[str, Any]]:
        """Generate actionable business recommendations"""
        recommendations = []
        
        # Add AI-generated recommendations based on patterns
        if analysis_results.get('trends', {}).get('volatility', 0) > 1000:
            recommendations.append({
                "type": "expense_control",
                "priority": "high",
                "message": "High spending volatility detected. Consider implementing expense approval workflows.",
                "action": "setup_approval_workflow"
            })
        
        return recommendations


# Global instances
transaction_categorizer = TransactionCategorizer()
document_analyzer = DocumentAnalyzer()
insight_engine = BusinessInsightEngine()
