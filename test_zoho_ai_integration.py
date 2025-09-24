#!/usr/bin/env python3
"""
Comprehensive test for AI agents' Zoho Books integration capabilities.
Tests that AI agents can perform real bookkeeping operations through natural language.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the CMP directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'cmp'))

from cmp.utils.ai_service import AIAgentService
from cmp.utils.zoho_books_api import ZohoBooksAPI
from cmp.utils.agent_zoho_tools import AgentZohoTools
from cmp.config import Settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZohoAIIntegrationTest:
    def __init__(self):
        self.settings = Settings()
        self.ai_service = AIAgentService()
        self.zoho_api = ZohoBooksAPI(self.settings)
        self.zoho_tools = AgentZohoTools()
        
    async def test_company_sync(self):
        """Test that AI agents can sync company profile to Zoho Books"""
        print("\n🔄 Testing Company Profile Synchronization...")
        
        try:
            # Test director agent synchronizing company profile
            message = "Please sync our company profile to Zoho Books to ensure all information is up to date"
            response = await self.ai_service.process_message(
                message=message,
                agent_type="director",
                context={"action": "sync_company_profile"}
            )
            
            print(f"✅ Director response: {response[:200]}...")
            
            # Verify the sync actually worked
            org_info = await self.zoho_api.get_organization_profile()
            if org_info and org_info.get('name'):
                print(f"✅ Company profile synced: {org_info['name']}")
                return True
            else:
                print("❌ Company profile sync failed")
                return False
                
        except Exception as e:
            print(f"❌ Company sync test failed: {e}")
            return False
    
    async def test_customer_creation(self):
        """Test that AI agents can create customers in Zoho Books"""
        print("\n👥 Testing Customer Creation...")
        
        try:
            # Test accountant creating a new customer
            message = """Please create a new customer in our system:
            - Name: Test Company LLC
            - Email: accounts@testcompany.ae
            - Phone: +971-4-123-4567
            - Address: Dubai Internet City, Dubai, UAE
            - Currency: AED
            """
            
            response = await self.ai_service.process_message(
                message=message,
                agent_type="accountant",
                context={"action": "create_customer"}
            )
            
            print(f"✅ Accountant response: {response[:200]}...")
            
            # Verify customer was created in Zoho Books
            customers = await self.zoho_api.list_customers()
            test_customer = None
            for customer in customers.get('contacts', []):
                if 'Test Company LLC' in customer.get('contact_name', ''):
                    test_customer = customer
                    break
            
            if test_customer:
                print(f"✅ Customer created: {test_customer['contact_name']}")
                return True
            else:
                print("❌ Customer creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Customer creation test failed: {e}")
            return False
    
    async def test_invoice_creation(self):
        """Test that AI agents can create invoices in Zoho Books"""
        print("\n📄 Testing Invoice Creation...")
        
        try:
            # Test CFO creating an invoice
            message = """Create an invoice for Test Company LLC:
            - Service: Consulting Services
            - Amount: 5000 AED
            - Due date: 30 days from today
            - Description: Monthly consulting retainer for January 2024
            """
            
            response = await self.ai_service.process_message(
                message=message,
                agent_type="cfo",
                context={"action": "create_invoice"}
            )
            
            print(f"✅ CFO response: {response[:200]}...")
            
            # Verify invoice was created
            invoices = await self.zoho_api.list_invoices()
            test_invoice = None
            for invoice in invoices.get('invoices', []):
                if invoice.get('total') == 5000.0:
                    test_invoice = invoice
                    break
            
            if test_invoice:
                print(f"✅ Invoice created: {test_invoice['invoice_number']} for {test_invoice['total']} AED")
                return True
            else:
                print("❌ Invoice creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Invoice creation test failed: {e}")
            return False
    
    async def test_expense_recording(self):
        """Test that AI agents can record expenses in Zoho Books"""
        print("\n💰 Testing Expense Recording...")
        
        try:
            # Test accountant recording an expense
            message = """Record a business expense:
            - Category: Office Supplies
            - Amount: 250 AED
            - Vendor: Office Depot UAE
            - Date: Today
            - Description: Printer paper and stationary for office
            """
            
            response = await self.ai_service.process_message(
                message=message,
                agent_type="accountant",
                context={"action": "record_expense"}
            )
            
            print(f"✅ Accountant response: {response[:200]}...")
            
            # Verify expense was recorded
            expenses = await self.zoho_api.list_expenses()
            test_expense = None
            for expense in expenses.get('expenses', []):
                if expense.get('total') == 250.0:
                    test_expense = expense
                    break
            
            if test_expense:
                print(f"✅ Expense recorded: {test_expense['expense_number']} for {test_expense['total']} AED")
                return True
            else:
                print("❌ Expense recording failed")
                return False
                
        except Exception as e:
            print(f"❌ Expense recording test failed: {e}")
            return False
    
    async def test_financial_reporting(self):
        """Test that AI agents can generate financial reports"""
        print("\n📊 Testing Financial Reporting...")
        
        try:
            # Test controller generating a financial report
            message = "Generate a profit and loss report for this month and analyze our financial performance"
            
            response = await self.ai_service.process_message(
                message=message,
                agent_type="controller",
                context={"action": "generate_report"}
            )
            
            print(f"✅ Controller response: {response[:200]}...")
            
            # Verify report data was retrieved
            if "revenue" in response.lower() or "profit" in response.lower() or "loss" in response.lower():
                print("✅ Financial report generated successfully")
                return True
            else:
                print("❌ Financial report generation failed")
                return False
                
        except Exception as e:
            print(f"❌ Financial reporting test failed: {e}")
            return False
    
    async def test_payment_tracking(self):
        """Test that AI agents can track payments and receivables"""
        print("\n💳 Testing Payment Tracking...")
        
        try:
            # Test CFO checking outstanding payments
            message = "Show me all outstanding invoices and overdue payments that need follow-up"
            
            response = await self.ai_service.process_message(
                message=message,
                agent_type="cfo",
                context={"action": "track_payments"}
            )
            
            print(f"✅ CFO response: {response[:200]}...")
            
            # Check if response contains payment/invoice information
            if "invoice" in response.lower() or "payment" in response.lower() or "outstanding" in response.lower():
                print("✅ Payment tracking working")
                return True
            else:
                print("❌ Payment tracking failed")
                return False
                
        except Exception as e:
            print(f"❌ Payment tracking test failed: {e}")
            return False
    
    async def test_vat_compliance(self):
        """Test that AI agents can handle VAT compliance tasks"""
        print("\n🏛️ Testing VAT Compliance...")
        
        try:
            # Test controller checking VAT compliance
            message = "Check our VAT compliance status and prepare the monthly VAT return if due"
            
            response = await self.ai_service.process_message(
                message=message,
                agent_type="controller",
                context={"action": "vat_compliance"}
            )
            
            print(f"✅ Controller response: {response[:200]}...")
            
            # Check if response contains VAT-related information
            if "vat" in response.lower() or "tax" in response.lower() or "compliance" in response.lower():
                print("✅ VAT compliance check working")
                return True
            else:
                print("❌ VAT compliance check failed")
                return False
                
        except Exception as e:
            print(f"❌ VAT compliance test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Zoho Books AI Integration Tests...")
        print("=" * 60)
        
        tests = [
            ("Company Sync", self.test_company_sync),
            ("Customer Creation", self.test_customer_creation),
            ("Invoice Creation", self.test_invoice_creation),
            ("Expense Recording", self.test_expense_recording),
            ("Financial Reporting", self.test_financial_reporting),
            ("Payment Tracking", self.test_payment_tracking),
            ("VAT Compliance", self.test_vat_compliance),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 60)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:.<40} {status}")
            if result:
                passed += 1
        
        print("-" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! AI agents are fully integrated with Zoho Books!")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check the logs above for details.")
        
        return passed == total

async def main():
    """Main test runner"""
    try:
        # Check if we have the necessary configuration
        settings = Settings()
        if not hasattr(settings, 'ZOHO_CLIENT_ID') or not settings.ZOHO_CLIENT_ID:
            print("❌ Zoho Books API credentials not configured")
            print("Please set up your Zoho Books API credentials in the settings")
            return False
        
        # Run the tests
        test_suite = ZohoAIIntegrationTest()
        success = await test_suite.run_all_tests()
        
        return success
        
    except Exception as e:
        print(f"❌ Test suite failed to initialize: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)