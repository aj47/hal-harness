#!/bin/bash

# Test script to run GitHub Actions workflow steps locally
# This helps debug issues before running on GitHub Actions

set -e  # Exit on any error

echo "=== Testing SWE-bench Evaluation Workflow Locally ==="
echo "Timestamp: $(date)"
echo

# Set default values (matching workflow defaults)
RUN_ID="${1:-swe-lite-20250809-161802}"
MAX_WORKERS="${2:-4}"
TIMEOUT="${3:-1800}"

echo "Configuration:"
echo "  Run ID: $RUN_ID"
echo "  Max workers: $MAX_WORKERS"
echo "  Timeout: $TIMEOUT"
echo

# Step 1: Check Docker
echo "=== Step 1: Checking Docker ==="
if command -v docker &> /dev/null; then
    echo "✓ Docker is available"
    docker --version
    # Don't start docker service on macOS (it should already be running)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start docker || echo "Docker service already running"
    fi
else
    echo "✗ Docker not found - this may cause issues in the actual workflow"
fi
echo

# Step 2: Setup SWE-bench source
echo "=== Step 2: Setting up SWE-bench source ==="
if [ ! -f "src/swebench/setup.py" ] && [ ! -f "src/swebench/pyproject.toml" ]; then
    echo "SWE-bench source not found, cloning from repository..."
    rm -rf src/swebench
    git clone https://github.com/princeton-nlp/SWE-bench.git src/swebench
else
    echo "✓ SWE-bench source found"
fi

# Verify setup files exist
echo "SWE-bench directory contents:"
ls -la src/swebench/ | head -10
if [ -f "src/swebench/setup.py" ]; then
    echo "✓ setup.py found"
fi
if [ -f "src/swebench/pyproject.toml" ]; then
    echo "✓ pyproject.toml found"
fi
echo

# Step 3: Install Micromamba (if not already installed)
echo "=== Step 3: Installing Micromamba ==="
if command -v micromamba &> /dev/null; then
    echo "✓ Micromamba already installed"
    micromamba --version
else
    echo "Installing Micromamba..."
    # Download and install micromamba using the official installer
    curl -Ls https://micro.mamba.pm/install.sh | bash
    
    # Add to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
    
    # Initialize micromamba
    $HOME/.local/bin/micromamba shell init -s bash -r $HOME/micromamba
    
    # Source the bashrc to activate micromamba
    source ~/.bashrc || source ~/.zshrc || echo "Could not source shell config"
    
    # Verify installation
    $HOME/.local/bin/micromamba --version
fi
echo

# Step 4: Create evaluation environment
echo "=== Step 4: Creating evaluation environment ==="
# Use full path to micromamba to avoid PATH issues
MICROMAMBA_PATH="$HOME/.local/bin/micromamba"
if [ ! -f "$MICROMAMBA_PATH" ]; then
    MICROMAMBA_PATH="micromamba"  # Fallback to PATH
fi

echo "Using micromamba at: $MICROMAMBA_PATH"

# Create environment
echo "Creating Python environment..."
$MICROMAMBA_PATH create -y -n swebench_hal python=3.11

# Install swebench
echo "Installing SWE-bench..."
$MICROMAMBA_PATH run -n swebench_hal pip install -e src/swebench

# Verify installation
echo "Verifying SWE-bench installation..."
$MICROMAMBA_PATH run -n swebench_hal python -c "import swebench; print('✓ SWE-bench installed successfully')"
echo

# Step 5: Verify predictions file exists
echo "=== Step 5: Verifying predictions file ==="
PREDICTIONS_PATH="results/$RUN_ID/${RUN_ID}_SWE_BENCH_SUBMISSIONS.jsonl"
if [ ! -f "$PREDICTIONS_PATH" ]; then
    echo "✗ Error: Predictions file not found at $PREDICTIONS_PATH"
    echo "Available files in results directory:"
    find results/ -name "*.jsonl" -type f 2>/dev/null || echo "No .jsonl files found"
    echo "This would cause the workflow to fail."
    echo
    echo "To fix this, you need to:"
    echo "1. Run the SWE-bench prediction generation first"
    echo "2. Or use a different RUN_ID that has existing predictions"
    exit 1
else
    echo "✓ Predictions file found: $PREDICTIONS_PATH"
    echo "File size: $(du -h "$PREDICTIONS_PATH" | cut -f1)"
    echo "Number of predictions: $(wc -l < "$PREDICTIONS_PATH")"
fi
echo

# Step 6: Test evaluation command (dry run)
echo "=== Step 6: Testing evaluation command (dry run) ==="
echo "This would run the following command:"
echo "$MICROMAMBA_PATH run -n swebench_hal python -m swebench.harness.run_evaluation \\"
echo "  --dataset_name princeton-nlp/SWE-bench_Lite \\"
echo "  --predictions_path \"$PREDICTIONS_PATH\" \\"
echo "  --max_workers $MAX_WORKERS \\"
echo "  --run_id $RUN_ID \\"
echo "  --timeout $TIMEOUT \\"
echo "  --verbose"
echo

echo "=== Test Summary ==="
echo "✓ SWE-bench source setup: OK"
echo "✓ Micromamba installation: OK"  
echo "✓ Python environment creation: OK"
echo "✓ SWE-bench package installation: OK"
if [ -f "$PREDICTIONS_PATH" ]; then
    echo "✓ Predictions file: OK"
    echo
    echo "🎉 All checks passed! The workflow should run successfully."
    echo
    echo "To run the actual evaluation, execute:"
    echo "$MICROMAMBA_PATH run -n swebench_hal python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Lite --predictions_path \"$PREDICTIONS_PATH\" --max_workers $MAX_WORKERS --run_id $RUN_ID --timeout $TIMEOUT --verbose"
else
    echo "✗ Predictions file: MISSING"
    echo
    echo "⚠️  The workflow will fail due to missing predictions file."
    echo "Generate predictions first or use a different RUN_ID."
fi
