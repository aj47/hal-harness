# GitHub Actions Setup for SWE-bench Evaluation

## 🚀 Quick Start

Since you have authentication issues with git push, here's how to manually set up the GitHub Actions workflow:

### Step 1: Upload Files to GitHub

1. **Go to your fork**: https://github.com/AugmentedAJ/hal-harness
2. **Create the workflow directory**: 
   - Click "Create new file"
   - Type `.github/workflows/swe-bench-evaluation.yml`
   - Copy the content from the local file `.github/workflows/swe-bench-evaluation.yml`

3. **Upload the predictions file**:
   - Navigate to `results/swe-lite-20250809-161802/`
   - Upload `swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl`

4. **Upload the SWE-bench source**:
   - Upload the entire `src/swebench/` directory
   - This contains the evaluation harness

### Step 2: Run the Workflow

1. **Go to Actions tab**: https://github.com/AugmentedAJ/hal-harness/actions
2. **Find "SWE-bench Evaluation" workflow**
3. **Click "Run workflow"**
4. **Enter parameters**:
   - Run ID: `swe-lite-20250809-161802`
   - Max workers: `4` (default)
   - Timeout: `1800` (default)
5. **Click "Run workflow"**

### Step 3: Monitor Progress

**Option A: GitHub Web Interface**
- Go to Actions tab and watch the workflow progress
- Click on the running workflow to see detailed logs

**Option B: Use the monitoring script**
```bash
python scripts/monitor_github_evaluation.py AugmentedAJ hal-harness [your_github_token]
```

## 📁 Required Files

Make sure these files are uploaded to your GitHub repository:

### Essential Files:
- `.github/workflows/swe-bench-evaluation.yml` ✅ (Created)
- `results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl` ✅ (Ready)
- `src/swebench/` (entire directory) ✅ (Ready)

### Optional Files:
- `scripts/monitor_github_evaluation.py` (for monitoring)
- `EVALUATION_HANDOFF_REPORT.md` (documentation)

## ⚡ Alternative: Direct Upload via GitHub CLI

If you have GitHub CLI installed:

```bash
# Login to GitHub CLI
gh auth login

# Create the workflow file
gh api repos/AugmentedAJ/hal-harness/contents/.github/workflows/swe-bench-evaluation.yml \
  --method PUT \
  --field message="Add SWE-bench evaluation workflow" \
  --field content="$(base64 -i .github/workflows/swe-bench-evaluation.yml)"

# Upload predictions file (if under 100MB)
gh api repos/AugmentedAJ/hal-harness/contents/results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl \
  --method PUT \
  --field message="Add SWE-bench predictions" \
  --field content="$(base64 -i results/swe-lite-20250809-161802/swe-lite-20250809-161802_SWE_BENCH_SUBMISSIONS.jsonl)"
```

## 🎯 Expected Results

Once the workflow runs successfully, you'll get:

1. **Evaluation Results**: `Auggie(sonnet4).swe-lite-20250809-161802.json`
2. **Detailed Logs**: Build and evaluation logs for all instances
3. **Success Rate**: Expected ~66.7% (200/300 resolved instances)
4. **Runtime**: 4-6 hours

## 📊 Workflow Features

The GitHub Actions workflow includes:

- ✅ **Docker setup** with proper permissions
- ✅ **Disk space optimization** (removes unnecessary packages)
- ✅ **Micromamba installation** for conda environment management
- ✅ **SWE-bench installation** from your source code
- ✅ **Predictions file verification** before starting evaluation
- ✅ **Comprehensive logging** and error handling
- ✅ **Artifact upload** for results and logs
- ✅ **8-hour timeout** to handle long evaluations
- ✅ **Configurable parameters** (workers, timeout, run_id)

## 🔧 Troubleshooting

### If the workflow fails:

1. **Check the Actions logs** for specific error messages
2. **Verify file paths** - ensure predictions file exists
3. **Check disk space** - workflow includes cleanup steps
4. **Monitor memory usage** - 7GB available on GitHub Actions
5. **Review timeout settings** - increase if needed

### Common issues:

- **File not found**: Ensure predictions file is uploaded correctly
- **Docker errors**: GitHub Actions handles Docker setup automatically
- **Memory issues**: Should not occur with 7GB available
- **Timeout**: Increase timeout parameter if needed

## 📞 Next Steps

1. Upload the workflow file to GitHub
2. Upload the predictions file
3. Upload the SWE-bench source code
4. Run the workflow from the Actions tab
5. Monitor progress and download results

The evaluation should complete successfully and give you the full results for all 300 SWE-bench Lite instances!
