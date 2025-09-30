# GitHub Token Setup Guide for Autonomous AI Agents

This guide explains how to create a GitHub Personal Access Token to enable autonomous AI agents to create and manage GitHub issues for task tracking.

## Step 1: Create Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"

## Step 2: Required Permissions

For autonomous AI agents to properly create and manage GitHub issues, select these **specific permissions**:

### ✅ **ESSENTIAL (Required)**
- **`repo`** - Full control of private repositories
  - **This is the main permission needed!**
  - Enables issue creation, project management, code access

- **`project`** - Full control of projects
  - Essential for GitHub Projects integration
  - Allows creating project boards and tracking tasks

### 🔧 **RECOMMENDED (Enhanced Features)**
- **`write:org`** - Read and write org and team membership, read and write org projects
  - For organization-level project management
  - Enhanced team collaboration features

- **`workflow`** - Update GitHub Action workflows
  - For CI/CD automation by agents
  - Advanced workflow management

- **`read:user`** - Read user profile data
  - Better attribution and user management

### ❌ **NOT NEEDED (Skip These)**
- `admin:org`, `delete_repo`, `admin:enterprise` (too powerful/dangerous)
- `copilot`, `codespace`, `audit_log` (unrelated to issue management)
- Any billing or enterprise scopes

## Step 3: Token Configuration

### Minimal Setup (Recommended to start):
Just select:
- ✅ **`repo`** 
- ✅ **`project`**

### Expiration:
- Set to **90 days** or **1 year**
- You can regenerate later if needed

## Step 4: Add to Environment

1. Copy your generated token
2. Add to `/Users/xidioda/Projects/CMP/.env`:
```bash
GITHUB_TOKEN=your_token_here
```

## Step 5: Verify Integration

Once configured, the autonomous agents will:
- ✅ Create GitHub issues for autonomous tasks
- ✅ Update issues with progress reports
- ✅ Manage project boards automatically
- ✅ Track task completion in real-time

## Capabilities Enabled

With this token, your AI agents can:

1. **Autonomous Issue Creation**
   - Create detailed GitHub issues for each task
   - Include technical details and execution plans
   - Add appropriate labels and priorities

2. **Progress Tracking**
   - Post real-time updates on task progress
   - Link code changes to specific issues
   - Automatically close issues when tasks complete

3. **Project Management**
   - Create and manage GitHub Projects
   - Move tasks through project workflows
   - Generate progress reports and analytics

4. **Code Integration**
   - Link commits to specific issues
   - Reference issues in code changes
   - Maintain audit trail of autonomous work

## Security Notes

- **Keep your token secure** - never commit to version control
- **Use minimal permissions** - start with `repo` + `project` only
- **Monitor usage** - check GitHub's token usage statistics
- **Rotate regularly** - regenerate tokens every 90 days

The autonomous agents are now ready for real GitHub project management!