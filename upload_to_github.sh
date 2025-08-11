#!/bin/bash

# Upload SWE-bench evaluation files to GitHub
# This script will push the necessary files to your GitHub repository

set -e  # Exit on any error

echo "🚀 Uploading SWE-bench evaluation files to GitHub..."

# Check if we're in the right directory
if [ ! -f ".github/workflows/swe-bench-evaluation.yml" ]; then
    echo "❌ Error: .github/workflows/swe-bench-evaluation.yml not found"
    echo "Please run this script from the hal-harness directory"
    exit 1
fi

# Check if predictions file exists
PREDICTIONS_FILE="results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl"
if [ ! -f "$PREDICTIONS_FILE" ]; then
    echo "❌ Error: Predictions file not found at $PREDICTIONS_FILE"
    exit 1
fi

# Check if SWE-bench source exists
if [ ! -d "src/swebench" ]; then
    echo "❌ Error: src/swebench directory not found"
    exit 1
fi

echo "✅ All required files found"

# Add files to git
echo "📁 Adding files to git..."
git add .github/workflows/swe-bench-evaluation.yml
git add -f "$PREDICTIONS_FILE"  # Force add even if in .gitignore
git add src/swebench/

# Check git status
echo "📊 Git status:"
git status --porcelain

# Commit changes
echo "💾 Committing changes..."
git commit -m "Add SWE-bench evaluation setup

- Add GitHub Actions workflow for SWE-bench evaluation
- Include predictions file with 300 SWE-bench Lite predictions
- Add SWE-bench evaluation harness source code
- Ready for cloud evaluation on GitHub Actions"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
echo "Attempting to push to fork remote..."

if git remote get-url fork >/dev/null 2>&1; then
    echo "Using 'fork' remote"
    git push fork agent/auggie
elif git remote get-url origin >/dev/null 2>&1; then
    echo "Using 'origin' remote"
    git push origin agent/auggie
else
    echo "❌ Error: No suitable git remote found"
    echo "Available remotes:"
    git remote -v
    exit 1
fi

echo "✅ Successfully uploaded files to GitHub!"
echo ""
echo "🎯 Next steps:"
echo "1. Go to: https://github.com/AugmentedAJ/hal-harness/actions"
echo "2. Find 'SWE-bench Evaluation' workflow"
echo "3. Click 'Run workflow'"
echo "4. Use parameters:"
echo "   - Run ID: swe-lite-20250809-161802"
echo "   - Max workers: 4"
echo "   - Timeout: 1800"
echo "5. Click 'Run workflow' to start evaluation"
echo ""
echo "📊 Expected results:"
echo "- Runtime: 4-6 hours"
echo "- Success rate: ~66.7% (200/300 instances)"
echo "- Cost: Free (GitHub Actions)"
echo ""
echo "🔍 Monitor progress at:"
echo "https://github.com/AugmentedAJ/hal-harness/actions"
