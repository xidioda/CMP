"""
Live API Integration Test

Tests the production-ready Zoho Books and Wio Bank integrations with proper error handling.
This test can run in both stub mode (without credentials) and production mode (with credentials).
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmp.integrations.invoices import zoho_books, wio_bank
from cmp.config import settings
from cmp.logging_config import get_logger

logger = get_logger("test_live_api")


async def test_zoho_books_integration():
    """Test Zoho Books API integration"""
    
    print("\n🔸 Testing Zoho Books Integration")
    print("=" * 50)
    
    # Check configuration status
    if zoho_books.is_configured:
        print("✅ Zoho Books: Production mode (credentials configured)")
    else:
        print("⚠️  Zoho Books: Stub mode (no credentials - safe for testing)")
    
    try:
        # Test 1: Get organizations
        print("\n1. Testing organizations fetch...")
        orgs = await zoho_books.get_organizations()
        print(f"   📊 Found {len(orgs)} organizations")
        
        # Test 2: Create a test contact
        print("\n2. Testing contact creation...")
        test_contact = {
            "name": "Test Customer LLC",
            "company": "Test Customer LLC", 
            "email": "test@testcustomer.ae",
            "phone": "+971-50-123-4567",
            "type": "customer"
        }
        contact_result = await zoho_books.create_contact(test_contact)
        print(f"   👤 Contact result: {contact_result.get('contact_id', 'N/A')}")
        
        # Test 3: Create a test invoice
        print("\n3. Testing invoice creation...")
        test_invoice = {
            "customer_name": "Test Customer LLC",
            "invoice_number": f"TEST-{datetime.now().strftime('%Y%m%d')}-001",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "currency": "AED",
            "line_items": [
                {
                    "description": "Software Development Services",
                    "quantity": 10,
                    "unit_price": 500.00
                },
                {
                    "description": "Consulting Services",
                    "quantity": 5,
                    "unit_price": 800.00
                }
            ]
        }
        invoice_result = await zoho_books.create_invoice(test_invoice)
        print(f"   📄 Invoice result: {invoice_result.get('invoice_id', 'N/A')}")
        
        # Test 4: Fetch transactions
        print("\n4. Testing transaction fetch...")
        transactions = await zoho_books.get_transactions("dummy_account")
        print(f"   💰 Found {len(transactions)} transactions")
        
        print("\n✅ Zoho Books integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Zoho Books integration test failed: {e}")
        logger.error(f"Zoho Books test error: {e}")
        return False


async def test_wio_bank_integration():
    """Test Wio Bank API integration"""
    
    print("\n🔸 Testing Wio Bank Integration")
    print("=" * 50)
    
    # Check configuration status
    if wio_bank.is_configured:
        print("✅ Wio Bank: Production mode (credentials configured)")
    else:
        print("⚠️  Wio Bank: Stub mode (no credentials - safe for testing)")
    
    try:
        # Test 1: Get account balance
        print("\n1. Testing account balance fetch...")
        balance = await wio_bank.get_balance()
        print(f"   💰 Balance: {balance.get('balance', 0)} {balance.get('currency', 'AED')}")
        print(f"   📊 Available: {balance.get('available_balance', 0)} {balance.get('currency', 'AED')}")
        
        # Test 2: Get account details
        print("\n2. Testing account details fetch...")
        details = await wio_bank.get_account_details()
        print(f"   🏦 Account: {details.get('account_name', 'N/A')}")
        print(f"   📋 Type: {details.get('account_type', 'N/A')}")
        print(f"   🔄 Status: {details.get('status', 'N/A')}")
        
        # Test 3: Fetch transactions (last 7 days)
        print("\n3. Testing transaction fetch (7 days)...")
        transactions = await wio_bank.fetch_transactions(days=7)
        print(f"   📈 Found {len(transactions)} transactions")
        
        if transactions:
            print("   Recent transactions:")
            for txn in transactions[:3]:  # Show first 3
                amount = txn.get('amount', 0)
                desc = txn.get('description', 'N/A')
                txn_type = txn.get('type', 'N/A')
                print(f"     • {amount:>10.2f} AED - {desc} ({txn_type})")
        
        # Test 4: Test transfer (safe in stub mode)
        print("\n4. Testing transfer initiation...")
        test_transfer = {
            "to_account": "1234567890",
            "amount": 100.00,
            "currency": "AED",
            "description": "Test Transfer",
            "reference": "TEST-TRANSFER-001"
        }
        transfer_result = await wio_bank.initiate_transfer(test_transfer)
        print(f"   🔄 Transfer ID: {transfer_result.get('transfer_id', 'N/A')}")
        print(f"   📊 Status: {transfer_result.get('status', 'N/A')}")
        
        print("\n✅ Wio Bank integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Wio Bank integration test failed: {e}")
        logger.error(f"Wio Bank test error: {e}")
        return False


async def test_combined_workflow():
    """Test a realistic combined workflow"""
    
    print("\n🔸 Testing Combined Workflow")
    print("=" * 50)
    
    try:
        # Step 1: Fetch bank transactions
        print("1. Fetching bank transactions...")
        bank_txns = await wio_bank.fetch_transactions(days=1)
        print(f"   Found {len(bank_txns)} bank transactions")
        
        # Step 2: Get Zoho Books transactions for comparison
        print("\n2. Fetching Zoho Books transactions...")
        zoho_txns = await zoho_books.get_transactions("main_account")
        print(f"   Found {len(zoho_txns)} Zoho transactions")
        
        # Step 3: Simulate invoice creation from bank transaction
        if bank_txns:
            print("\n3. Creating invoice from bank transaction...")
            first_txn = bank_txns[0]
            
            invoice_data = {
                "customer_name": "Auto-generated Customer",
                "invoice_number": f"AUTO-{datetime.now().strftime('%Y%m%d')}-001",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "currency": first_txn.get('currency', 'AED'),
                "line_items": [
                    {
                        "description": f"Service related to: {first_txn.get('description', 'Bank Transaction')}",
                        "quantity": 1,
                        "unit_price": abs(first_txn.get('amount', 1000))
                    }
                ]
            }
            
            invoice_result = await zoho_books.create_invoice(invoice_data)
            print(f"   📄 Created invoice: {invoice_result.get('invoice_id', 'N/A')}")
        
        print("\n✅ Combined workflow test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Combined workflow test failed: {e}")
        logger.error(f"Combined workflow test error: {e}")
        return False


async def main():
    """Run all integration tests"""
    
    print("🚀 Starting Live API Integration Tests")
    print("=====================================")
    
    print(f"\n📋 Configuration Status:")
    print(f"   • Environment: {settings.env}")
    print(f"   • Zoho Books URL: {settings.zoho_base_url}")
    print(f"   • Wio Bank URL: {settings.wio_base_url}")
    print(f"   • Rate Limit: {settings.api_rate_limit} req/min")
    print(f"   • Timeout: {settings.api_timeout}s")
    
    # Run tests
    tests = [
        ("Zoho Books Integration", test_zoho_books_integration),
        ("Wio Bank Integration", test_wio_bank_integration),
        ("Combined Workflow", test_combined_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API integration tests passed! Ready for production.")
    else:
        print("⚠️  Some tests failed. Please check configuration and try again.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
