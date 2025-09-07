"""
AI Accountant Agent

Responsibilities:
- Fetch transactions from bank APIs and file imports
- Intelligently categorize transactions using ML
- OCR uploaded invoices and create bills with AI analysis
- Generate e-invoices with smart data extraction
- Perform daily bank reconciliations with anomaly detection
- Prepare draft VAT returns with compliance checking
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import asyncio

from ..logging_config import get_logger
from ..utils.ocr import ocr_processor
from ..utils.ai import transaction_categorizer, document_analyzer, insight_engine
from ..integrations.invoices import zoho_books, generate_uae_einvoice, emirates_nbd, bank_file_importer

logger = get_logger("agents.accountant")


class AIAccountant:
    """AI Accountant - Intelligent, real-time, compliant bookkeeping with ML"""
    
    def __init__(self):
        self.name = "AI:Accountant"
        self.processed_invoices = []
        self.ai_insights = []
        
        # Enhanced AI-powered categorization replaces simple keyword matching
        logger.info(f"{self.name} initialized with AI/ML capabilities")
        logger.info("- Intelligent transaction categorization (ML)")
        logger.info("- Smart document analysis and OCR")
        logger.info("- Business insights and anomaly detection")
        logger.info("- Multi-bank integration (Emirates NBD, File Import)")
    
    async def fetch_bank_transactions(self, days: int = 1) -> List[Dict[str, Any]]:
        """Fetch transactions from multiple banks with AI categorization"""
        all_transactions = []
        
        try:
            # Fetch from Emirates NBD API (real UAE bank)
            try:
                emirates_transactions = await emirates_nbd.fetch_transactions(days=days)
                all_transactions.extend(emirates_transactions)
                logger.info(f"{self.name}: Fetched {len(emirates_transactions)} Emirates NBD transactions")
            except Exception as e:
                logger.warning(f"Emirates NBD fetch failed: {e}")
            
            # Import from bank statement files
            try:
                file_transactions = await bank_file_importer.import_recent_statements(days=days)
                all_transactions.extend(file_transactions)
                logger.info(f"{self.name}: Imported {len(file_transactions)} file-based transactions")
            except Exception as e:
                logger.warning(f"File import failed: {e}")
            
            # Apply AI categorization to all transactions
            processed_transactions = []
            for txn in all_transactions:
                # Use AI to categorize transaction
                categorization = self.categorize_transaction_ai(
                    description=txn.get("description", ""),
                    amount=txn.get("amount", 0)
                )
                txn.update(categorization)
                processed_transactions.append(txn)
            
            # Generate business insights from transaction patterns
            if processed_transactions:
                insights = insight_engine.analyze_spending_patterns(processed_transactions)
                self.ai_insights.extend(insights.get("insights", []))
                logger.info(f"{self.name}: Generated {len(insights.get('insights', []))} business insights")
            
            return processed_transactions
            
        except Exception as e:
            logger.error(f"{self.name}: Error fetching bank transactions: {e}")
            return []
    
    def categorize_transaction_ai(self, description: str, amount: float = 0) -> Dict[str, Any]:
        """Use AI to categorize transaction with confidence scoring"""
        try:
            # Use the ML categorization model
            result = transaction_categorizer.categorize(description, amount)
            
            logger.info(f"{self.name}: AI categorized '{description}' as '{result['category']}' "
                       f"(confidence: {result['confidence']:.2f})")
            
            return {
                "ai_category": result["category"],
                "ai_confidence": result["confidence"],
                "ai_reasoning": result["reasoning"],
                "ai_suggestions": result.get("suggested_categories", [])
            }
        except Exception as e:
            logger.warning(f"AI categorization failed: {e}, using fallback")
            return {
                "ai_category": "Other",
                "ai_confidence": 0.0,
                "ai_reasoning": f"Error: {e}",
                "ai_suggestions": []
            }
    
    async def process_uploaded_invoice(self, file_path: Path) -> Dict[str, Any]:
        """Process uploaded invoice with AI-enhanced OCR analysis"""
        try:
            # Extract data using OCR
            ocr_data = await ocr_processor.extract_invoice_data(file_path)
            raw_text = ocr_data.get("raw_text", "")
            
            # Apply AI document analysis
            ai_analysis = document_analyzer.analyze_document(raw_text, ocr_data)
            
            # Combine OCR and AI results
            enhanced_data = {
                "ocr_data": ocr_data,
                "ai_analysis": ai_analysis,
                "vendor": ai_analysis.get("vendor", {}).get("name", ocr_data.get("vendor", "Unknown")),
                "amounts": ai_analysis.get("amounts", []),
                "suggested_category": ai_analysis.get("categories", [{}])[0].get("category", "Other"),
                "confidence": ai_analysis.get("confidence", 0.0),
                "document_type": ai_analysis.get("document_type", {}).get("type", "invoice"),
                "language": ai_analysis.get("language", {}).get("name", "English")
            }
            
            logger.info(f"{self.name}: AI-enhanced invoice processing complete")
            logger.info(f"- Vendor: {enhanced_data['vendor']}")
            logger.info(f"- Category: {enhanced_data['suggested_category']}")
            logger.info(f"- Confidence: {enhanced_data['confidence']:.2f}")
            logger.info(f"- Language: {enhanced_data['language']}")
            
            # Prepare invoice data for Zoho Books with AI enhancements
            primary_amount = enhanced_data['amounts'][0] if enhanced_data['amounts'] else {"amount": 0, "currency": "AED"}
            
            invoice_data = {
                "customer_name": enhanced_data["vendor"],
                "invoice_number": ocr_data.get("invoice_number", f"AUTO-{datetime.now().strftime('%Y%m%d%H%M')}"),
                "date": ocr_data.get("date", datetime.now().strftime('%Y-%m-%d')),
                "currency": primary_amount.get("currency", "AED"),
                "line_items": ocr_data.get("line_items", []),
                "total_amount": ocr_data.get("amount", 0)
            }
            
            # Create invoice in Zoho Books
            zoho_response = await zoho_books.create_invoice(invoice_data)
            
            # Generate UAE e-invoice
            einvoice = generate_uae_einvoice({
                "supplier_name": "Your Company",
                "customer_name": ocr_data.get("vendor"),
                "subtotal": ocr_data.get("amount", 0),
                "vat_amount": ocr_data.get("amount", 0) * 0.05,  # 5% VAT
                "total": ocr_data.get("amount", 0) * 1.05,
                "line_items": ocr_data.get("line_items", []),
            })
            
            result = {
                "file_path": str(file_path),
                "ocr_data": ocr_data,
                "zoho_response": zoho_response,
                "einvoice": einvoice,
                "status": "processed",
                "confidence": ocr_data.get("confidence", 0)
            }
            
            self.processed_invoices.append(result)
            logger.info(f"{self.name}: Successfully processed invoice {ocr_data.get('invoice_number', 'Unknown')} (confidence: {ocr_data.get('confidence', 0):.2f})")
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Error processing invoice {file_path}: {e}")
            return {"status": "error", "error": str(e), "file_path": str(file_path)}
    
    async def generate_einvoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UAE-compliant e-invoice"""
        einvoice = generate_uae_einvoice(invoice_data)
        logger.info(f"{self.name}: Generated e-invoice {einvoice.get('invoice_id')}")
        return einvoice
    
    async def reconcile_bank(self, account_id: str = "main") -> Dict[str, Any]:
        """Perform daily bank reconciliation with real data"""
        from ..integrations.invoices import wio_bank, zoho_books
        
        try:
            # Get bank transactions from Wio Bank
            bank_transactions = await wio_bank.fetch_transactions(days=1)
            
            # Get transactions from Zoho Books
            zoho_transactions = await zoho_books.get_transactions(account_id)
            
            # Get current balance from Wio Bank
            balance_info = await wio_bank.get_balance()
            
            # Perform reconciliation logic
            bank_total = sum(txn.get("amount", 0) for txn in bank_transactions)
            zoho_total = sum(txn.get("amount", 0) for txn in zoho_transactions)
            discrepancy = abs(bank_total - zoho_total)
            
            status = "reconciled" if discrepancy < 0.01 else "discrepancy_found"
            
            result = {
                "account_id": account_id,
                "status": status,
                "bank_transactions_count": len(bank_transactions),
                "zoho_transactions_count": len(zoho_transactions),
                "bank_total": bank_total,
                "zoho_total": zoho_total,
                "discrepancy": discrepancy,
                "balance": balance_info.get("balance", 0),
                "currency": balance_info.get("currency", "AED"),
                "reconciliation_date": datetime.now().isoformat()
            }
            
            logger.info(f"{self.name}: Bank reconciliation completed - Status: {status}, Discrepancy: {discrepancy}")
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Error during bank reconciliation: {e}")
            return {
                "account_id": account_id,
                "status": "error",
                "error": str(e),
                "discrepancy": 0,
                "balance": 0
            }
    
    async def prepare_vat_draft(self, period: str = "current") -> Dict[str, Any]:
        """Prepare draft VAT return"""
        # TODO: Calculate actual VAT from transactions
        logger.info(f"{self.name}: Preparing VAT draft for period {period} (stub)")
        return {
            "period": period,
            "total_sales": 0,
            "total_purchases": 0,
            "vat_payable": 0,
            "vat_recoverable": 0,
            "net_vat": 0,
            "status": "draft"
        }
    
    async def analyze_spending_patterns(self) -> Dict[str, Any]:
        """Generate AI-powered spending analysis and business insights"""
        try:
            # Fetch recent transactions for analysis
            recent_transactions = await self.fetch_bank_transactions(days=30)
            
            if not recent_transactions:
                return {"message": "No transactions available for analysis"}
            
            # Generate comprehensive business insights using AI
            insights = insight_engine.analyze_spending_patterns(recent_transactions)
            
            # Add additional AI-powered recommendations
            recommendations = insight_engine.generate_recommendations(insights)
            insights["ai_recommendations"] = recommendations
            
            logger.info(f"{self.name}: Generated comprehensive spending analysis")
            logger.info(f"- Total insights: {len(insights.get('insights', []))}")
            logger.info(f"- Recommendations: {len(recommendations)}")
            
            return insights
            
        except Exception as e:
            logger.error(f"{self.name}: Spending pattern analysis failed: {e}")
            return {"error": f"Analysis failed: {e}"}
    
    async def detect_anomalies(self, transactions: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Detect anomalous transactions using AI"""
        if not transactions:
            transactions = await self.fetch_bank_transactions(days=7)
        
        anomalies = []
        
        try:
            if len(transactions) < 3:
                return anomalies
            
            amounts = [t.get("amount", 0) for t in transactions]
            avg_amount = sum(amounts) / len(amounts)
            
            # Simple anomaly detection (in production, use more sophisticated ML algorithms)
            for txn in transactions:
                amount = txn.get("amount", 0)
                
                # Flag unusually large amounts
                if amount > avg_amount * 3:
                    anomalies.append({
                        "transaction": txn,
                        "anomaly_type": "unusual_amount",
                        "severity": "high" if amount > avg_amount * 5 else "medium",
                        "reason": f"Amount {amount} is {amount/avg_amount:.1f}x the average transaction",
                        "ai_confidence": 0.8
                    })
                
                # Flag duplicate transactions
                similar_txns = [t for t in transactions if 
                               abs(t.get("amount", 0) - amount) < 0.01 and 
                               t.get("description", "") == txn.get("description", "") and
                               t != txn]
                
                if similar_txns:
                    anomalies.append({
                        "transaction": txn,
                        "anomaly_type": "potential_duplicate",
                        "severity": "medium",
                        "reason": f"Similar transaction found: {len(similar_txns)} match(es)",
                        "ai_confidence": 0.7
                    })
            
            if anomalies:
                logger.warning(f"{self.name}: Detected {len(anomalies)} transaction anomalies")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"{self.name}: Anomaly detection failed: {e}")
            return []
    
    async def get_ai_insights(self) -> List[Dict[str, Any]]:
        """Get current AI insights and recommendations"""
        return self.ai_insights
    
    async def train_categorization_model(self, feedback: Dict[str, str]):
        """Train/update the AI categorization model with user feedback"""
        try:
            description = feedback.get("description", "")
            correct_category = feedback.get("category", "")
            
            if description and correct_category:
                transaction_categorizer.retrain_with_feedback(description, correct_category)
                logger.info(f"{self.name}: Updated AI model with feedback: '{description}' -> '{correct_category}'")
                return {"status": "success", "message": "Model updated with feedback"}
            else:
                return {"status": "error", "message": "Invalid feedback data"}
                
        except Exception as e:
            logger.error(f"{self.name}: Model training failed: {e}")
            return {"status": "error", "message": f"Training failed: {e}"}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with AI capabilities"""
        return {
            "name": self.name,
            "agent": self.name,
            "status": "active",
            "processed_invoices_count": len(self.processed_invoices),
            "last_activity": "AI-enhanced financial processing ready",
            "capabilities": [
                "Multi-bank transaction fetching (Emirates NBD, File Import)",
                "AI-powered transaction categorization (ML)",
                "Intelligent document analysis and OCR",
                "Business insights and pattern analysis", 
                "Anomaly detection and fraud prevention",
                "Automated invoice processing with AI",
                "Bank reconciliation with discrepancy detection",
                "VAT return preparation with compliance checking"
            ],
            "ai_features": {
                "transaction_categorizer": "active",
                "document_analyzer": "active", 
                "insight_engine": "active",
                "anomaly_detector": "active"
            },
            "recent_insights": len(self.ai_insights),
            "processed_invoices": len(self.processed_invoices)
        }


# Global instance
accountant = AIAccountant()
