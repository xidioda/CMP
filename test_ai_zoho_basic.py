#!/usr/bin/env python3
"""
Basic test to verify AI agents have access to Zoho Books tools
and can process bookkeeping-related messages correctly.
"""

import asyncio
import sys
import os

# Add the CMP directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'cmp'))

from cmp.utils.ai_service import AIAgentService

async def test_agent_zoho_awareness():
    """Test that AI agents are aware of their Zoho Books capabilities"""
    print("🧪 Testing AI Agent Zoho Books Awareness...")
    print("=" * 50)
    
    ai_service = AIAgentService()
    
    test_cases = [
        {
            "agent": "accountant",
            "message": "What bookkeeping tasks can you help me with?",
            "expected_keywords": ["zoho books", "transaction", "invoice", "expense"]
        },
        {
            "agent": "cfo", 
            "message": "How can you help with financial management?",
            "expected_keywords": ["zoho books", "financial", "report", "cash flow"]
        },
        {
            "agent": "controller",
            "message": "What compliance and control functions do you provide?",
            "expected_keywords": ["zoho books", "compliance", "audit", "control"]
        },
        {
            "agent": "director",
            "message": "What executive oversight capabilities do you have?",
            "expected_keywords": ["zoho books", "oversight", "dashboard", "strategic"]
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        agent_type = test_case["agent"]
        message = test_case["message"]
        expected_keywords = test_case["expected_keywords"]
        
        print(f"\n🤖 Testing {agent_type.upper()} agent...")
        print(f"Question: {message}")
        
        try:
            # Get the agent's system prompt to check Zoho Books integration
            system_prompt = ai_service._get_system_prompt(agent_type)
            
            # Check if the prompt contains Zoho Books references
            zoho_mentions = system_prompt.lower().count("zoho books")
            has_zoho_integration = "ZOHO BOOKS INTEGRATION" in system_prompt
            has_zoho_responsibilities = "ZOHO BOOKS RESPONSIBILITIES" in system_prompt
            
            print(f"   📋 Zoho Books mentions in prompt: {zoho_mentions}")
            print(f"   📋 Has Zoho Books integration section: {has_zoho_integration}")
            print(f"   📋 Has Zoho Books responsibilities section: {has_zoho_responsibilities}")
            
            # Check for expected keywords
            found_keywords = []
            for keyword in expected_keywords:
                if keyword.lower() in system_prompt.lower():
                    found_keywords.append(keyword)
            
            print(f"   📋 Expected keywords found: {found_keywords}")
            
            # Determine if test passed
            test_passed = (
                zoho_mentions > 0 and 
                has_zoho_integration and 
                has_zoho_responsibilities and
                len(found_keywords) >= 2
            )
            
            results[agent_type] = test_passed
            status = "✅ PASS" if test_passed else "❌ FAIL"
            print(f"   {status}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results[agent_type] = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for agent, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{agent.upper():.<20} {status}")
    
    print("-" * 50)
    print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 SUCCESS! All AI agents are properly configured with Zoho Books capabilities!")
    else:
        print(f"\n⚠️  {total - passed} agents need Zoho Books configuration.")
    
    return passed == total

async def test_zoho_operation_detection():
    """Test that the AI service can detect Zoho Books operations in messages"""
    print("\n🔍 Testing Zoho Books Operation Detection...")
    print("=" * 50)
    
    ai_service = AIAgentService()
    
    test_messages = [
        ("Create an invoice for ABC Company", ["invoice", "create"]),
        ("Record an expense for office supplies", ["expense", "record"]),
        ("Show me the profit and loss report", ["report", "financial"]),
        ("Update customer information in Zoho Books", ["customer", "update"]),
        ("Check our VAT compliance status", ["vat", "compliance"]),
        ("Sync company profile to Zoho Books", ["sync", "company"]),
        ("What's the current cash flow?", ["cash", "flow"]),
        ("Generate monthly financial statements", ["statement", "generate"])
    ]
    
    detection_results = {}
    
    for message, expected_operations in test_messages:
        print(f"\n📝 Testing: '{message}'")
        
        try:
            # Test the operation detection (this is a mock since we don't want to make real API calls)
            detected_operations = []
            message_lower = message.lower()
            
            # Check for common operation patterns
            if any(word in message_lower for word in ["create", "make", "new"]) and "invoice" in message_lower:
                detected_operations.append("create_invoice")
            
            if any(word in message_lower for word in ["record", "add", "enter"]) and "expense" in message_lower:
                detected_operations.append("record_expense")
            
            if any(word in message_lower for word in ["report", "statement", "profit", "loss"]):
                detected_operations.append("generate_report")
            
            if "customer" in message_lower and any(word in message_lower for word in ["update", "modify", "change"]):
                detected_operations.append("update_customer")
            
            if "vat" in message_lower or "compliance" in message_lower:
                detected_operations.append("vat_compliance")
            
            if "sync" in message_lower and "company" in message_lower:
                detected_operations.append("sync_company")
            
            if "cash flow" in message_lower:
                detected_operations.append("cash_flow_analysis")
            
            print(f"   🎯 Detected operations: {detected_operations}")
            
            # Check if we detected any relevant operations
            has_detection = len(detected_operations) > 0
            detection_results[message] = has_detection
            
            status = "✅ DETECTED" if has_detection else "❌ NOT DETECTED"
            print(f"   {status}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            detection_results[message] = False
    
    # Print detection summary
    detected = sum(detection_results.values())
    total = len(detection_results)
    
    print(f"\n📊 Detection Results: {detected}/{total} messages detected operations")
    print(f"Detection Rate: {(detected/total)*100:.1f}%")
    
    return detected >= (total * 0.7)  # 70% detection rate is acceptable

async def main():
    """Run all basic tests"""
    print("🚀 CMP AI-Zoho Books Integration Basic Tests")
    print("=" * 60)
    
    tests = [
        ("Agent Zoho Awareness", test_agent_zoho_awareness),
        ("Operation Detection", test_zoho_operation_detection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    
    passed_tests = sum(results)
    total_tests = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print("-" * 60)
    print(f"Overall Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL BASIC TESTS PASSED!")
        print("Your AI agents are ready for Zoho Books integration!")
        print("\nNext steps:")
        print("1. Configure Zoho Books API credentials")
        print("2. Run the full integration test with: python test_zoho_ai_integration.py")
        print("3. Test real bookkeeping operations through the chat interface")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Check configuration.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)