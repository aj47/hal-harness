# 🚀 GitHub Actions SWE-bench Evaluation Setup Guide

## Current Status
✅ **Workflow file created locally**: `.github/workflows/swe-bench-evaluation.yml`  
✅ **Predictions ready**: `results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl`  
✅ **SWE-bench source ready**: `src/swebench/` directory  
❌ **Files need to be uploaded to GitHub**: Your fork is missing the latest changes  

## 🎯 Quick Setup (3 Steps)

### Step 1: Upload Workflow File
1. Go to: https://github.com/AugmentedAJ/hal-harness
2. Click **"Create new file"**
3. Type path: `.github/workflows/swe-bench-evaluation.yml`
4. Copy content from your local file: `.github/workflows/swe-bench-evaluation.yml`
5. Commit with message: "Add SWE-bench evaluation workflow"

### Step 2: Upload Required Files

**Option A: Using GitHub Web Interface**
1. **Upload predictions file**:
   - Navigate to `results/swe-lite-20250809-161802/`
   - Upload `swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl`

2. **Upload SWE-bench source**:
   - Upload entire `src/swebench/` directory
   - This contains the evaluation harness

**Option B: Fix Git Authentication (Recommended)**
```bash
# Check your git remote
git remote -v

# If using HTTPS, switch to SSH or use personal access token
git remote set-url fork git@github.com:AugmentedAJ/hal-harness.git

# Or use GitHub CLI
gh auth login
git push fork agent/auggie
```

### Step 3: Run the Evaluation
1. Go to **Actions** tab: https://github.com/AugmentedAJ/hal-harness/actions
2. Find **"SWE-bench Evaluation"** workflow
3. Click **"Run workflow"**
4. Use these parameters:
   - **Run ID**: `swe-lite-20250809-161802`
   - **Max workers**: `4`
   - **Timeout**: `1800`
5. Click **"Run workflow"**

## 📊 Expected Results

- **Runtime**: 4-6 hours for all 300 instances
- **Success Rate**: ~66.7% (200/300 resolved instances)
- **Cost**: Free (within GitHub Actions limits)
- **Artifacts**: Complete evaluation results and logs

## 🔧 Alternative: GitHub CLI Upload

If you have GitHub CLI installed:

```bash
# Login to GitHub CLI
gh auth login

# Upload workflow file
gh api repos/AugmentedAJ/hal-harness/contents/.github/workflows/swe-bench-evaluation.yml \
  --method PUT \
  --field message="Add SWE-bench evaluation workflow" \
  --field content="$(base64 -i .github/workflows/swe-bench-evaluation.yml)" \
  --field branch="agent/auggie"

# Upload predictions file (if under 100MB)
gh api repos/AugmentedAJ/hal-harness/contents/results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl \
  --method PUT \
  --field message="Add SWE-bench predictions" \
  --field content="$(base64 -i results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl)" \
  --field branch="agent/auggie"
```

## 🎯 Workflow Features

The GitHub Actions workflow includes:

✅ **Docker setup** with proper permissions  
✅ **Disk space optimization** (removes unnecessary packages)  
✅ **Micromamba installation** for conda environment management  
✅ **SWE-bench installation** from your source code  
✅ **Predictions file verification** before starting evaluation  
✅ **Comprehensive logging** and error handling  
✅ **Artifact upload** for results and logs  
✅ **8-hour timeout** to handle long evaluations  
✅ **Configurable parameters** (workers, timeout, run_id)  

## 🔍 Monitoring Progress

**Option 1: GitHub Web Interface**
- Go to Actions tab and watch the workflow progress
- Click on the running workflow to see detailed logs

**Option 2: Use the monitoring script**
```bash
python scripts/monitor_github_evaluation.py AugmentedAJ hal-harness [your_github_token]
```

## 📁 Required Files Summary

Make sure these files are in your GitHub repository:

### Essential Files:
- ✅ `.github/workflows/swe-bench-evaluation.yml` (workflow definition)
- ❌ `results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl` (predictions)
- ❌ `src/swebench/` (evaluation harness source code)

### File Sizes:
- Workflow file: ~6KB
- Predictions file: ~5.4MB (300 predictions)
- SWE-bench source: ~50MB (entire evaluation framework)

## 🚨 Troubleshooting

### If workflow fails:
1. **Check the Actions logs** for specific error messages
2. **Verify file paths** - ensure predictions file exists
3. **Check disk space** - workflow includes cleanup steps
4. **Monitor memory usage** - 7GB available on GitHub Actions

### Common issues:
- **File not found**: Ensure predictions file is uploaded correctly
- **Docker errors**: GitHub Actions handles Docker setup automatically
- **Memory issues**: Should not occur with 7GB available
- **Timeout**: Increase timeout parameter if needed

## 🎉 Success Criteria

The evaluation should produce:
1. **Final report**: `Auggie(sonnet4).swe-lite-20250809-161802.json`
2. **Resolved instances**: ~200 out of 300 (66.7% success rate)
3. **Complete logs**: Build and evaluation logs for all instances
4. **No OOM failures**: All instances either resolve, fail tests, or hit timeout

## 📞 Next Steps

1. **Upload the workflow file** to GitHub (Step 1 above)
2. **Upload the predictions and source files** (Step 2 above)
3. **Run the workflow** from the Actions tab (Step 3 above)
4. **Monitor progress** and download results when complete

The evaluation should complete successfully and give you the full results for all 300 SWE-bench Lite instances!

---

**Need help?** The workflow is designed to be robust and handle all the issues from your local evaluation. GitHub Actions provides the native x86_64 environment and sufficient resources to complete the evaluation successfully.
