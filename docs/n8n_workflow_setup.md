# N8N Workflow Setup for Autonomous AI Agents

## Current Status
✅ N8N Server Running: `http://localhost:5678`  
✅ Secure Cookie Issue Fixed  
✅ Webhook URL: `http://localhost:5678/webhook/lead_developer_automation`  
❌ Need to create workflow with webhook trigger  

## Quick Setup Instructions

### 1. Access N8N Editor
Open: http://localhost:5678

### 2. Create New Workflow
1. Click "Add Workflow" or "Create Workflow"
2. Name it: "Lead Developer Automation"

### 3. Add Webhook Trigger
1. Click "Add Node" 
2. Search for "Webhook" 
3. Select "Webhook" trigger node
4. Configure:
   - **HTTP Method:** POST
   - **Path:** `lead_developer_automation`
   - **Authentication:** None (for local development)

### 4. Add Processing Node (Optional)
1. Add "Set" node or "Code" node after webhook
2. Configure to process the incoming data:
   ```json
   {
     "task_id": "{{ $json.task_id }}",
     "agent": "{{ $json.agent }}",
     "timestamp": "{{ $json.timestamp }}",
     "status": "received"
   }
   ```

### 5. Add Response Node
1. Add "Respond to Webhook" node
2. Configure response:
   ```json
   {
     "status": "success",
     "message": "Task received by N8N automation",
     "task_id": "{{ $json.task_id }}"
   }
   ```

### 6. Save and Activate
1. Click "Save" 
2. Toggle "Active" switch ON
3. The webhook will be available at: `http://localhost:5678/webhook/lead_developer_automation`

## Advanced Configuration

### Multiple Agent Workflows
Create separate workflows for different agents:
- `lead_developer_automation` - Lead Developer tasks
- `system_optimization` - System optimization tasks  
- `git_operations` - Git operations
- `file_operations` - File operations

### Webhook Data Structure
The autonomous agents send this data structure:
```json
{
  "task_id": "lead_dev_real_n8n_integration",
  "agent": "Lead Developer",
  "timestamp": "2025-09-30T10:33:46.123456",
  "trigger_source": "lead_developer_agent",
  "action": "development_automation"
}
```

### Integration with External Services
You can extend the workflows to:
- Send notifications to Slack/Discord
- Create Jira tickets
- Update databases
- Trigger deployments
- Send emails

## Testing the Integration

Once the workflow is set up, test it:

```bash
curl -X POST http://localhost:5678/webhook/lead_developer_automation \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test_task",
    "agent": "Test Agent", 
    "timestamp": "2025-09-30T10:00:00"
  }'
```

Expected response:
```json
{
  "status": "success",
  "message": "Task received by N8N automation",
  "task_id": "test_task"
}
```

## Troubleshooting

### 404 Webhook Not Found
- Ensure workflow is saved and activated
- Check the webhook path matches exactly
- Verify N8N is running on port 5678

### 400 Bad Request  
- Check JSON format in webhook payload
- Verify Content-Type header is set correctly

### 500 Internal Server Error
- Check N8N logs for errors
- Verify workflow nodes are configured correctly

## Next Steps

1. **Create the basic webhook workflow** (5 minutes)
2. **Test with autonomous agents** 
3. **Add more sophisticated automation**
4. **Integrate with external services**
5. **Monitor and optimize workflows**

The autonomous AI organization will then have full N8N workflow automation! 🚀