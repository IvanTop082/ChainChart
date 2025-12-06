# GitHub Setup Instructions

Your code has been committed locally! Follow these steps to push to GitHub:

## Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `ChainChart`)
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"

## Step 2: Add Remote and Push

After creating the repository, GitHub will show you commands. Use these:

### If using HTTPS:
```bash
git remote add origin https://github.com/YOUR_USERNAME/ChainChart.git
git branch -M main
git push -u origin main
```

### If using SSH:
```bash
git remote add origin git@github.com:YOUR_USERNAME/ChainChart.git
git branch -M main
git push -u origin main
```

## Quick Command (Replace YOUR_USERNAME)

Replace `YOUR_USERNAME` with your actual GitHub username:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/ChainChart.git
git push -u origin main
```

## Already have a repository?

If you already created a repository, just add the remote:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Troubleshooting

- **Authentication**: GitHub may prompt for credentials. Use a Personal Access Token if prompted.
- **Branch name**: If your default branch is `master`, use `git branch -M main` first.

