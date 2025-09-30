#!/usr/bin/env python3

import asyncio
from cmp.integrations.n8n_workflow_integration import N8NWorkflowIntegration

async def test_workflow_pipeline():
    print('🔍 Testing N8N workflow pipeline step by step...')
    
    n8n_integration = N8NWorkflowIntegration()
    
    # Test data
    task_type = 'development'
    workflow_data = {
        'task_type': task_type,
        'task_details': {'id': 'pipeline_test'},
        'timestamp': '2024-09-30T18:40:00',
        'source': 'pipeline_test'
    }
    
    print('Step 1: Testing workflow creation...')
    creation_result = await n8n_integration._create_n8n_workflow(task_type, workflow_data)
    print(f'📊 Creation Result: {creation_result}')
    
    if creation_result.get('success'):
        print('✅ Workflow creation succeeded!')
        workflow_id = creation_result.get('workflow_id')
        
        print(f'Step 2: Testing workflow execution for ID {workflow_id}...')
        execution_result = await n8n_integration._execute_n8n_workflow(workflow_id, workflow_data)
        print(f'📊 Execution Result: {execution_result}')
        
        if execution_result.get('success'):
            print('✅ Complete workflow pipeline SUCCESS!')
        else:
            print(f'❌ Workflow execution failed: {execution_result.get("error")}')
    else:
        print(f'❌ Workflow creation failed: {creation_result.get("error")}')

if __name__ == "__main__":
    asyncio.run(test_workflow_pipeline())