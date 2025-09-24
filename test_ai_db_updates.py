#!/usr/bin/env python3
"""
Test AI Agent Database Modification Capabilities

Tests the new functionality where AI agents can update company information
when users provide new details through conversation.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cmp.utils.ai_service import AIAgentService
from cmp.db import init_db

async def test_agent_db_updates():
    """Test AI agents updating database information"""
    
    print("🧪 Testing AI Agent Database Update Capabilities")
    print("=" * 60)
    
    # Initialize database
    print("📊 Initializing database...")
    init_db()
    
    # Create AI service
    ai_service = AIAgentService()
    
    # Test messages that should trigger database updates
    test_messages = [
        {
            "agent": "accountant",
            "message": "Our VAT TRN is now 123456789012345",
            "expected_update": "vat_registration"
        },
        {
            "agent": "accountant", 
            "message": "Update our corporate tax number to CTN-789123456",
            "expected_update": "corporate_tax"
        },
        {
            "agent": "director",
            "message": "Our trade license number is now DED-12345-2024",
            "expected_update": "trade_license"
        },
        {
            "agent": "cfo",
            "message": "Change our company legal name to \"Advanced Financial Solutions LLC\"",
            "expected_update": "company_info"
        },
        {
            "agent": "controller",
            "message": "We moved to \"123 Business Bay, Dubai, UAE\"",
            "expected_update": "company_info"
        },
        {
            "agent": "accountant",
            "message": "What's our current VAT registration status?",
            "expected_update": None  # No update expected, just query
        }
    ]
    
    print(f"\n🔍 Testing {len(test_messages)} message scenarios...\n")
    
    for i, test in enumerate(test_messages, 1):
        print(f"Test {i}: {test['agent'].title()} Agent")
        print(f"Message: \"{test['message']}\"")
        
        try:
            # Process message with potential database updates
            response = await ai_service.process_message_with_db_updates(
                test["agent"], 
                test["message"]
            )
            
            # Check if database updates occurred
            has_updates = "db_updates" in response and len(response.get("db_updates", [])) > 0
            
            print(f"Response Type: {response.get('type', 'unknown')}")
            print(f"Database Updates: {'✅ YES' if has_updates else '❌ NO'}")
            
            if has_updates:
                print("Updates performed:")
                for update in response["db_updates"]:
                    status = "✅" if update["result"]["success"] else "❌"
                    print(f"  {status} {update['type']}: {update['action']} = {update['value']}")
            
            print(f"AI Response: {response['message'][:100]}...")
            
            if test["expected_update"]:
                if has_updates:
                    update_types = [u["type"] for u in response["db_updates"]]
                    if test["expected_update"] in update_types:
                        print("✅ Expected update type found")
                    else:
                        print(f"⚠️  Expected {test['expected_update']}, got {update_types}")
                else:
                    print(f"❌ Expected {test['expected_update']} update but none occurred")
            else:
                if not has_updates:
                    print("✅ No updates expected and none occurred")
                else:
                    print("⚠️  Unexpected database updates occurred")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)
    
    # Test getting company information to verify updates
    print("\n📋 Final Company Information Check:")
    
    try:
        from cmp.utils.agent_db_tools import AgentDatabaseTools
        db_tools = AgentDatabaseTools("test")
        company_info = await db_tools.get_company_info()
        
        if company_info["success"]:
            company = company_info["company"]
            print(f"Company Name: {company.get('legal_name', 'Not set')}")
            print(f"VAT Registered: {company.get('vat_registered', False)}")
            print(f"VAT TRN: {company.get('vat_registration_number', 'Not set')}")
            print(f"Corporate Tax Number: {company.get('corporate_tax_number', 'Not set')}")
            print(f"Trade License: {company.get('trade_license_number', 'Not set')}")
            print(f"Address: {company.get('address_line_1', 'Not set')}")
        else:
            print(f"❌ Error getting company info: {company_info.get('error')}")
            
    except Exception as e:
        print(f"❌ Error checking final company info: {e}")
    
    print("\n✅ AI Agent Database Update Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_agent_db_updates())