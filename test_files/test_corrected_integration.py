"""
Corrected Live API Integration Test

Tests realistic UAE banking integrations:
- Zoho Books (confirmed API available)
- Emirates NBD API Souq (confirmed public API)
- Bank file import for banks without APIs (like Wio Bank)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmp.integrations.invoices import zoho_books, emirates_nbd, bank_file_importer
from cmp.config import settings
from cmp.logging_config import get_logger

logger = get_logger("test_real_api")


async def test_zoho_books_integration():
    """Test Zoho Books API integration (confirmed real API)"""
    
    print("\n🔸 Testing Zoho Books Integration")
    print("=" * 50)
    
    if zoho_books.is_configured:
        print("✅ Zoho Books: Production mode (credentials configured)")
    else:
        print("⚠️  Zoho Books: Stub mode (no credentials - safe for testing)")
    
    try:
        # Test 1: Get organizations
        print("\n1. Testing organizations fetch...")
        orgs = await zoho_books.get_organizations()
        print(f"   📊 Found {len(orgs)} organizations")
        
        # Test 2: Create a test invoice
        print("\n2. Testing invoice creation...")
        test_invoice = {
            "customer_name": "UAE Test Customer LLC",
            "invoice_number": f"UAE-{datetime.now().strftime('%Y%m%d')}-001",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "currency": "AED",
            "line_items": [
                {
                    "description": "Software Development Services",
                    "quantity": 10,
                    "unit_price": 500.00
                }
            ]
        }
        invoice_result = await zoho_books.create_invoice(test_invoice)
        print(f"   📄 Invoice result: {invoice_result.get('invoice_id', 'N/A')}")
        
        print("\n✅ Zoho Books integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Zoho Books integration test failed: {e}")
        return False


async def test_emirates_nbd_integration():
    """Test Emirates NBD API Souq integration (confirmed real API)"""
    
    print("\n🔸 Testing Emirates NBD API Souq Integration")
    print("=" * 50)
    
    if emirates_nbd.is_configured:
        print("✅ Emirates NBD: Production mode (credentials configured)")
    else:
        print("⚠️  Emirates NBD: Stub mode (no credentials - safe for testing)")
    
    try:
        # Test 1: Get account balance
        print("\n1. Testing account balance fetch...")
        balance = await emirates_nbd.get_balance()
        print(f"   💰 Balance: {balance.get('balance', 0)} {balance.get('currency', 'AED')}")
        print(f"   🏦 Bank: {balance.get('bank', 'N/A')}")
        
        # Test 2: Get account details
        print("\n2. Testing account details fetch...")
        details = await emirates_nbd.get_account_details()
        print(f"   🏦 Account: {details.get('account_name', 'N/A')}")
        print(f"   🏢 Branch: {details.get('branch', 'N/A')}")
        print(f"   🔄 Status: {details.get('status', 'N/A')}")
        
        # Test 3: Fetch transactions
        print("\n3. Testing transaction fetch (7 days)...")
        transactions = await emirates_nbd.fetch_transactions(days=7)
        print(f"   📈 Found {len(transactions)} transactions")
        
        if transactions:
            print("   Recent transactions:")
            for txn in transactions[:3]:  # Show first 3
                amount = txn.get('amount', 0)
                desc = txn.get('description', 'N/A')
                txn_type = txn.get('type', 'N/A')
                ref = txn.get('reference', 'N/A')
                print(f"     • {amount:>10.2f} AED - {desc} ({txn_type}) - Ref: {ref}")
        
        print("\n✅ Emirates NBD integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Emirates NBD integration test failed: {e}")
        return False


async def test_bank_file_import():
    """Test bank file import for banks without APIs (like Wio Bank)"""
    
    print("\n🔸 Testing Bank File Import (for banks without APIs)")
    print("=" * 50)
    
    try:
        # Create a sample CSV file for testing
        sample_csv_path = Path("/Users/xidioda/Projects/CMP/test_files/sample_bank_statement.csv")
        
        print("1. Creating sample bank statement CSV...")
        sample_csv_content = """Date,Description,Amount,Balance,Reference
2025-08-20,Salary Transfer - ABC Company,12000.00,25000.00,SAL20250820001
2025-08-19,POS Transaction - Carrefour,-245.50,13000.00,POS20250819001
2025-08-18,Online Transfer to Savings,-1000.00,13245.50,TRF20250818001
2025-08-17,ATM Withdrawal,-500.00,14245.50,ATM20250817001"""
        
        with open(sample_csv_path, 'w') as f:
            f.write(sample_csv_content)
        
        print(f"   📄 Created sample CSV: {sample_csv_path}")
        
        # Test importing the CSV
        print("\n2. Testing CSV import...")
        transactions = await bank_file_importer.import_statement(sample_csv_path, "Wio Bank")
        print(f"   📊 Imported {len(transactions)} transactions")
        
        if transactions:
            print("   Imported transactions:")
            for txn in transactions[:3]:  # Show first 3
                amount = txn.get('amount', 0)
                desc = txn.get('description', 'N/A')
                date = txn.get('date', 'N/A')
                bank = txn.get('bank', 'N/A')
                print(f"     • {date} - {amount:>10.2f} AED - {desc} ({bank})")
        
        print("\n✅ Bank file import test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Bank file import test failed: {e}")
        return False


async def test_realistic_workflow():
    """Test a realistic workflow with actual UAE banking options"""
    
    print("\n🔸 Testing Realistic UAE Banking Workflow")
    print("=" * 50)
    
    try:
        # Step 1: Get Emirates NBD transactions (API)
        print("1. Fetching Emirates NBD transactions via API...")
        api_transactions = await emirates_nbd.fetch_transactions(days=1)
        print(f"   Found {len(api_transactions)} API transactions")
        
        # Step 2: Import Wio Bank statement (file)
        sample_csv = Path("/Users/xidioda/Projects/CMP/test_files/sample_bank_statement.csv")
        if sample_csv.exists():
            print("\n2. Importing Wio Bank statement from file...")
            file_transactions = await bank_file_importer.import_statement(sample_csv, "Wio Bank")
            print(f"   Imported {len(file_transactions)} file transactions")
        else:
            print("\n2. No Wio Bank statement file available")
            file_transactions = []
        
        # Step 3: Create invoice in Zoho Books from transactions
        all_transactions = api_transactions + file_transactions
        if all_transactions:
            print(f"\n3. Creating Zoho Books invoice from {len(all_transactions)} total transactions...")
            
            # Use the first credit transaction for invoice
            credit_txns = [t for t in all_transactions if t.get('type') == 'credit']
            if credit_txns:
                first_credit = credit_txns[0]
                
                invoice_data = {
                    "customer_name": "Auto-generated from Bank Transaction",
                    "invoice_number": f"BANK-{datetime.now().strftime('%Y%m%d')}-001",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "currency": "AED",
                    "line_items": [
                        {
                            "description": f"Service for: {first_credit.get('description', 'Bank Transaction')}",
                            "quantity": 1,
                            "unit_price": abs(first_credit.get('amount', 1000))
                        }
                    ]
                }
                
                invoice_result = await zoho_books.create_invoice(invoice_data)
                print(f"   📄 Created invoice: {invoice_result.get('invoice_id', 'N/A')}")
        
        print("\n✅ Realistic UAE banking workflow test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Realistic workflow test failed: {e}")
        return False


async def main():
    """Run corrected API integration tests"""
    
    print("🚀 Starting CORRECTED Live API Integration Tests")
    print("================================================")
    print("🇦🇪 UAE Banking Reality Check:")
    print("   ✅ Zoho Books - Confirmed public API")
    print("   ✅ Emirates NBD API Souq - Confirmed public API")
    print("   ⚠️  Wio Bank - No public API, using file import")
    print("   📄 Bank file import - CSV/Excel support")
    
    print(f"\n📋 Configuration Status:")
    print(f"   • Environment: {settings.env}")
    print(f"   • Zoho Books URL: {settings.zoho_base_url}")
    print(f"   • Emirates NBD URL: {settings.emirates_nbd_base_url}")
    print(f"   • Bank Import Dir: {getattr(settings, 'bank_import_directory', 'local_storage/bank_statements')}")
    
    # Run tests
    tests = [
        ("Zoho Books Integration", test_zoho_books_integration),
        ("Emirates NBD API Souq", test_emirates_nbd_integration),
        ("Bank File Import", test_bank_file_import),
        ("Realistic UAE Workflow", test_realistic_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 CORRECTED TEST RESULTS SUMMARY")
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
        print("🎉 All CORRECTED API integration tests passed!")
        print("💡 Ready for realistic UAE banking integration!")
    else:
        print("⚠️  Some tests failed. Please check configuration.")
    
    print(f"\n🔧 To use in production:")
    print("   1. Get Emirates NBD API Souq access")
    print("   2. Configure Zoho Books OAuth")
    print("   3. Set up bank file import for other banks")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
