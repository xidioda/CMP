# GitHub Project Management Workflow for CMP Development

## AI Assistant Instructions for Project Management

When working on CMP development, ALWAYS follow this workflow:

### 🔄 Before Starting Any Task
1. **Check current project status**: `gh project view 1 --owner xidioda`
2. **Review open issues**: `gh issue list --repo xidioda/CMP`
3. **Update issue status to "In Progress"** when starting work

### 📝 During Development
1. **Create subtasks as needed**: Break down large issues into smaller, trackable tasks
2. **Commit with issue references**: Use "Fix #N", "Close #N", or "Update #N" in commit messages
3. **Document progress** in issue comments for complex tasks

### ✅ After Completing Tasks
1. **Run tests**: Ensure all tests pass before marking complete
2. **Update issue status** to "Done" or close the issue
3. **Create new issues** for any discovered work or improvements
4. **Update project board** with new status

### 🏷️ Issue Management Best Practices
- **Label issues appropriately**: enhancement, bug, documentation, etc.
- **Assign priority levels**: Use GitHub's priority field
- **Link related issues**: Use "Relates to #N" or "Blocks #N"
- **Update milestones** for release planning

### 📊 Regular Project Maintenance
- **Weekly review**: Check all open issues and update priorities
- **Create new issues** for discovered improvements or bugs
- **Archive completed items** and update project status

## Current Project Status Commands

```bash
# View project board
gh project view 1 --owner xidioda

# List all issues
gh issue list --repo xidioda/CMP

# Create new issue
gh issue create --title "Title" --body "Description" --repo xidioda/CMP

# Update issue status (requires issue number)
gh issue edit <number> --add-label "in-progress" --repo xidioda/CMP

# Close issue
gh issue close <number> --repo xidioda/CMP
```

## Current Development Focus

**Active Issues:**
- #2: Install Tesseract OCR for Full Processing (NEXT)
- #1: Phase 2A: Live API Integration 
- #3: Implement User Authentication System
- #4: Phase 2B: Advanced AI Implementation
- #5: Production Deployment Setup

**Completed Issues:**
- Initial scaffolding (committed)
- Enhanced features with testing (committed)
- GitHub integration setup (committed)
