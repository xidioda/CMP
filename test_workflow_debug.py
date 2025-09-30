#!/usr/bin/env python3

import asyncio
from cmp.integrations.n8n_workflow_integration import N8NWorkflowIntegration

async def test_workflow_creation_debug():
    print('🔍 Testing N8N workflow creation with DEBUG...')
    
    n8n_integration = N8NWorkflowIntegration()
    
    # Test the _create_n8n_workflow method directly
    task_type = 'development'
    workflow_data = {
        'task_type': task_type,
        'task_details': {'id': 'debug_test'},
        'timestamp': '2024-09-30T18:30:00',
        'source': 'debug_test'
    }
    
    print(f'🌐 N8N URL: {n8n_integration.n8n_url}')
    print(f'🔑 API Key: {"SET" if n8n_integration.n8n_api_key else "NOT SET"}')
    
    # Test workflow creation directly
    result = await n8n_integration._create_n8n_workflow(task_type, workflow_data)
    print(f'📊 Workflow Creation Result: {result}')
    
    if result.get('success'):
        print('✅ Workflow creation SUCCEEDED!')
    else:
        print(f'❌ Workflow creation FAILED: {result.get("error")}')

if __name__ == "__main__":
    asyncio.run(test_workflow_creation_debug())