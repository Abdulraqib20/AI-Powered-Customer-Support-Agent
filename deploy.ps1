# DEPLOY.ps1 - One-Click GitHub Deployment
param(
    [string]$RepoName,
    [string]$Description = "AI-Powered-Customer-Support-Agent"
)

# 1. GitHub Connection
$GitHubUser = "Abdulraqib20"
git remote set-url origin "https://github.com/$GitHubUser/$RepoName.git"

# 2. Generate Professional README
@"
# 🚀 $RepoName

$Description

## ✨ Features
1️⃣ Meta's Llama 3.3 70-B model via Groq 

—Generates the profiles for different customer IDs
—Enables the agent to comprehend and respond to complex customer queries.
—Provides in-depth answers addressing order details, payment-related, product-related, account-related and service issues tailored to the Nigerian market.

2️⃣ mem0 (Mem0) 

—Serves as the memory layer for the system as it manages conversation history to ensure continuity in customer interactions.
—Helps the support agent recall previous details, making each conversation feel more personal and informed.

3️⃣ Qdrant Vector DB

—Enables efficient similarity searches, ensuring that responses are both timely and contextually accurate.
—Quickly retrieves relevant past interactions, making the convo better and more accurate.

4️⃣ Google's Embedding models

—Converts text into vector representations which improves matching of customer queries with right responses
—Enhances the agent's understanding of customer queries, leading to more accurate responses.

## 🛠️ Installation
```bash
git clone https://github.com/$GitHubUser/$RepoName.git
cd $RepoName
pip install -r requirements.txt
```

## ⚙️ Configuration
Create .env file with:
QDRANT_URL_LOCAL="your-qdrant-local-host"
GROQ_API_KEY="groq-api-key"
GOOGLE_API_KEY="google-key"

## 📧 Support
Report issues at: https://github.com/$GitHubUser/$RepoName/issues
"@ | Out-File README.md -Encoding UTF8

# 3. Commit Changes
git add --all
git commit -m "🚀 Deploy: $RepoName"

# 4. Force Push
git push -u origin main --force

Write-Host "✅ Deployment Successful: https://github.com/$GitHubUser/$RepoName" -ForegroundColor Green


#------------------------------------
# Steps to Deploy
#------------------------------------

# 1. Remove git repository
# rm -Recurse -Force .git OR Remove-Item -Recurse -Force .git

# 2. initialize with Main Branch
# git init -b main

# 3. Show current branch
# git branch --show-current  # Should output "main"

# 4. Set remote URL 
# git remote add origin https://github.com/Abdulraqib20/AI-Powered-Customer-Support-Agent

# 5. Run the below in PowerShell:
# ./deploy.ps1 -RepoName "AI-Powered-Customer-Support-Agent" -Description "This application is a Nigerian-based e-commerce customer support agent designed to deliver context-aware, intelligent assistance while keeping track of every conversation along the way."

# Credential Caching (One-Time Setup):
# git config --global credential.helper wincred


