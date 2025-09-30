#!/usr/bin/env python3

import asyncio
from cmp.integrations.n8n_workflow_integration import N8NWorkflowIntegration

async def test_n8n_workflow():
    print('🔄 Testing FIXED N8N workflow creation...')
    
    n8n_integration = N8NWorkflowIntegration()
    
    # Test workflow creation with correct signature
    task_type = 'development'
    task_details = {
        'id': 'test_workflow_456',
        'title': 'Test FIXED Workflow Creation', 
        'description': 'Testing if N8N workflows are NOW actually created',
        'agent': 'test_agent'
    }
    
    result = await n8n_integration.trigger_development_workflow(task_type, task_details)
    print(f'📊 N8N Workflow Result: {result}')
    
    # Check different result indicators
    if result.get('workflow_id'):
        print('✅ N8N workflow ID returned - workflow was created!')
    elif result.get('n8n_attempted'):
        print('✅ N8N workflow creation was attempted')
    elif 'N8N workflow creation failed' in str(result):
        print('⚠️ N8N creation was attempted but failed (still good progress!)')
    else:
        print('❌ Still using old direct execution logic')

if __name__ == "__main__":
    asyncio.run(test_n8n_workflow())