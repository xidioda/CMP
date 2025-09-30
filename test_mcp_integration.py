import asyncio
from cmp.integrations.mcp_server_integration import mcp_integration

async def test_mcp():
    result = await mcp_integration.execute_tool('filesystem_mcp', 'write_file', {
        'file_path': 'test_autonomous_api.py', 
        'content': '# Test file created by autonomous developer\nprint("Real file creation works!")'
    })
    print('MCP Integration Test Result:', result)

if __name__ == "__main__":
    asyncio.run(test_mcp())