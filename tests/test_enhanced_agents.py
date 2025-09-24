"""
Tests for enhanced AI agents with performance monitoring and optimization features
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from cmp.agents.accountant import AIAccountant
from cmp.agents.cfo import AICFO


class TestEnhancedAIAccountant:
    """Test enhanced AI Accountant with performance monitoring"""
    
    @pytest.fixture
    def accountant(self):
        """Create AI Accountant instance for testing"""
        return AIAccountant()
    
    def test_accountant_initialization(self, accountant):
        """Test AI Accountant initializes with performance metrics"""
        assert accountant.name == "AI:Accountant"
        assert isinstance(accountant.processed_invoices, list)
        assert isinstance(accountant.ai_insights, list)
        assert isinstance(accountant.performance_metrics, dict)
        assert isinstance(accountant._categorization_cache, dict)
        
        # Check performance metrics structure
        assert "operations_count" in accountant.performance_metrics
        assert "total_processing_time" in accountant.performance_metrics
        assert "errors_count" in accountant.performance_metrics
        assert "cache_hits" in accountant.performance_metrics
    
    def test_performance_metrics_update(self, accountant):
        """Test performance metrics are updated correctly"""
        initial_count = accountant.performance_metrics["operations_count"]
        
        accountant._update_performance_metrics(0.5, error=False)
        
        assert accountant.performance_metrics["operations_count"] == initial_count + 1
        assert accountant.performance_metrics["total_processing_time"] == 0.5
        assert accountant.performance_metrics["errors_count"] == 0
        assert accountant.performance_metrics["last_operation_time"] is not None
    
    def test_performance_metrics_error_tracking(self, accountant):
        """Test error tracking in performance metrics"""
        initial_errors = accountant.performance_metrics["errors_count"]
        
        accountant._update_performance_metrics(0.3, error=True)
        
        assert accountant.performance_metrics["errors_count"] == initial_errors + 1
    
    @patch('cmp.agents.accountant.transaction_categorizer')
    def test_categorize_transaction_caching(self, mock_categorizer, accountant):
        """Test transaction categorization with caching"""
        # Mock the categorizer response
        mock_categorizer.categorize.return_value = {
            "category": "Office Supplies",
            "confidence": 0.85,
            "reasoning": "Keywords match office supplies patterns",
            "suggested_categories": ["Office Supplies", "Business Expenses"]
        }
        
        description = "Office supplies from Staples"
        amount = 150.0
        
        # First call - should hit the AI model
        result1 = accountant.categorize_transaction_ai(description, amount)
        
        assert result1["ai_category"] == "Office Supplies"
        assert result1["ai_confidence"] == 0.85
        assert "processed_at" in result1
        assert "processing_time" in result1
        assert mock_categorizer.categorize.call_count == 1
        
        # Second call - should hit the cache
        result2 = accountant.categorize_transaction_ai(description, amount)
        
        assert result2["ai_category"] == "Office Supplies"
        assert mock_categorizer.categorize.call_count == 1  # No additional call
        assert accountant.performance_metrics["cache_hits"] == 1
    
    @patch('cmp.agents.accountant.transaction_categorizer')
    def test_categorize_transaction_error_handling(self, mock_categorizer, accountant):
        """Test transaction categorization error handling and fallback"""
        # Mock the categorizer to raise an exception
        mock_categorizer.categorize.side_effect = Exception("AI model error")
        
        result = accountant.categorize_transaction_ai("Test transaction", 100.0)
        
        assert result["ai_category"] == "Other"
        assert result["ai_confidence"] == 0.0
        assert result["error"] is True
        assert "Fallback due to error" in result["ai_reasoning"]
        assert accountant.performance_metrics["errors_count"] == 1
    
    @pytest.mark.asyncio
    async def test_get_status_with_performance_metrics(self, accountant):
        """Test get_status includes performance metrics"""
        # Add some mock performance data
        accountant.performance_metrics["operations_count"] = 5
        accountant.performance_metrics["total_processing_time"] = 2.5
        accountant.performance_metrics["errors_count"] = 1
        accountant.performance_metrics["cache_hits"] = 3
        accountant._categorization_cache["test"] = {"result": "cached"}
        
        status = await accountant.get_status()
        
        assert "performance_metrics" in status
        assert "optimization_features" in status
        
        perf_metrics = status["performance_metrics"]
        assert perf_metrics["total_operations"] == 5
        assert perf_metrics["avg_processing_time"] == 0.5
        assert perf_metrics["error_rate"] == 20.0
        assert perf_metrics["cache_hit_rate"] == 60.0
        assert perf_metrics["cache_size"] == 1
        
        opt_features = status["optimization_features"]
        assert opt_features["caching"] == "enabled"
        assert opt_features["performance_monitoring"] == "active"
        assert opt_features["error_recovery"] == "enabled"
        assert opt_features["async_operations"] == "optimized"
    
    @pytest.mark.asyncio
    @patch('cmp.agents.accountant.emirates_nbd')
    @patch('cmp.agents.accountant.bank_file_importer')
    async def test_fetch_bank_transactions_monitoring(self, mock_file_importer, mock_emirates, accountant):
        """Test bank transaction fetching with performance monitoring"""
        # Mock responses
        mock_emirates.fetch_transactions = AsyncMock(return_value=[
            {"description": "ATM Withdrawal", "amount": 500, "date": "2025-09-20"}
        ])
        mock_file_importer.import_recent_statements = AsyncMock(return_value=[
            {"description": "Online Transfer", "amount": 1000, "date": "2025-09-20"}
        ])
        
        # Mock the categorization to avoid AI calls
        with patch.object(accountant, 'categorize_transaction_ai') as mock_categorize:
            mock_categorize.return_value = {
                "ai_category": "Transfer",
                "ai_confidence": 0.9,
                "ai_reasoning": "Transfer detected",
                "ai_suggestions": []
            }
            
            transactions = await accountant.fetch_bank_transactions(days=1)
            
            assert len(transactions) == 2
            assert all("ai_category" in txn for txn in transactions)


class TestEnhancedAICFO:
    """Test enhanced AI CFO with performance monitoring"""
    
    @pytest.fixture
    def cfo(self):
        """Create AI CFO instance for testing"""
        return AICFO()
    
    def test_cfo_initialization(self, cfo):
        """Test AI CFO initializes with performance metrics"""
        assert cfo.name == "AI:CFO"
        assert isinstance(cfo.strategic_kpis, dict)
        assert isinstance(cfo.performance_metrics, dict)
        
        # Check performance metrics structure
        assert "models_generated" in cfo.performance_metrics
        assert "scenarios_analyzed" in cfo.performance_metrics
        assert "optimization_cycles" in cfo.performance_metrics
        assert "total_processing_time" in cfo.performance_metrics
        assert "errors_count" in cfo.performance_metrics
    
    def test_performance_metrics_update(self, cfo):
        """Test CFO performance metrics updates"""
        initial_models = cfo.performance_metrics["models_generated"]
        
        cfo._update_performance_metrics(1.5, "model", error=False)
        
        assert cfo.performance_metrics["models_generated"] == initial_models + 1
        assert cfo.performance_metrics["total_processing_time"] == 1.5
        assert cfo.performance_metrics["last_operation_time"] is not None
    
    def test_performance_metrics_different_operations(self, cfo):
        """Test tracking different operation types"""
        cfo._update_performance_metrics(0.5, "scenario", error=False)
        cfo._update_performance_metrics(0.3, "optimization", error=False)
        
        assert cfo.performance_metrics["scenarios_analyzed"] == 1
        assert cfo.performance_metrics["optimization_cycles"] == 1
        assert cfo.performance_metrics["total_processing_time"] == 0.8
    
    @pytest.mark.asyncio
    async def test_get_status_with_performance_metrics(self, cfo):
        """Test CFO get_status includes performance metrics"""
        # Add some mock performance data
        cfo.performance_metrics["models_generated"] = 3
        cfo.performance_metrics["scenarios_analyzed"] = 5
        cfo.performance_metrics["optimization_cycles"] = 2
        cfo.performance_metrics["total_processing_time"] = 10.0
        cfo.performance_metrics["errors_count"] = 1
        
        status = await cfo.get_status()
        
        assert "performance_metrics" in status
        assert "optimization_features" in status
        
        perf_metrics = status["performance_metrics"]
        assert perf_metrics["models_generated"] == 3
        assert perf_metrics["scenarios_analyzed"] == 5
        assert perf_metrics["optimization_cycles"] == 2
        assert perf_metrics["total_operations"] == 10  # 3 + 5 + 2
        assert perf_metrics["avg_processing_time"] == 1.0  # 10.0 / 10
        assert perf_metrics["error_rate"] == 10.0  # 1 / 10 * 100
        
        opt_features = status["optimization_features"]
        assert opt_features["performance_monitoring"] == "active"
        assert opt_features["strategic_optimization"] == "continuous"
        assert opt_features["ml_model_optimization"] == "enabled"
        assert opt_features["scenario_caching"] == "active"
    
    @pytest.mark.asyncio
    @patch('cmp.utils.ai.insight_engine')
    async def test_develop_financial_model_monitoring(self, mock_insight_engine, cfo):
        """Test financial model development with performance monitoring"""
        # This test would require mocking the entire method or testing a simpler version
        # For now, we'll test that the decorator is applied
        assert hasattr(cfo.develop_financial_model, '__wrapped__')


class TestAgentIntegration:
    """Integration tests for enhanced AI agents"""
    
    @pytest.mark.asyncio
    async def test_agent_status_integration(self):
        """Test that all agents return proper status with performance metrics"""
        from cmp.agents.accountant import accountant
        from cmp.agents.cfo import cfo
        
        # Test accountant status
        acc_status = await accountant.get_status()
        assert "performance_metrics" in acc_status
        assert "optimization_features" in acc_status
        
        # Test CFO status
        cfo_status = await cfo.get_status()
        assert "performance_metrics" in cfo_status
        assert "optimization_features" in cfo_status
    
    def test_performance_decorator_integration(self):
        """Test that performance monitoring decorators are properly applied"""
        from cmp.agents.accountant import accountant
        from cmp.agents.cfo import cfo
        
        # Check that methods have the performance monitoring decorator
        assert hasattr(accountant.fetch_bank_transactions, '__wrapped__')
        assert hasattr(accountant.categorize_transaction_ai, '__wrapped__')
        assert hasattr(accountant.process_uploaded_invoice, '__wrapped__')
        assert hasattr(cfo.develop_financial_model, '__wrapped__')


if __name__ == "__main__":
    pytest.main([__file__])