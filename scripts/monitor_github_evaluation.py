#!/usr/bin/env python3
"""
Monitor GitHub Actions SWE-bench evaluation progress
"""

import requests
import time
import json
import sys
from datetime import datetime

def get_workflow_runs(repo_owner, repo_name, token=None):
    """Get recent workflow runs for the repository"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching workflow runs: {response.status_code}")
        return None

def monitor_evaluation(repo_owner, repo_name, workflow_name="SWE-bench Evaluation", token=None):
    """Monitor the SWE-bench evaluation workflow"""
    print(f"Monitoring {workflow_name} in {repo_owner}/{repo_name}")
    print("=" * 60)
    
    while True:
        runs_data = get_workflow_runs(repo_owner, repo_name, token)
        if not runs_data:
            time.sleep(30)
            continue
        
        # Find the most recent SWE-bench evaluation run
        swe_bench_runs = [
            run for run in runs_data['workflow_runs'] 
            if workflow_name.lower() in run['name'].lower()
        ]
        
        if not swe_bench_runs:
            print("No SWE-bench evaluation runs found")
            time.sleep(30)
            continue
        
        latest_run = swe_bench_runs[0]
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Latest Run Status:")
        print(f"  Run ID: {latest_run['id']}")
        print(f"  Status: {latest_run['status']}")
        print(f"  Conclusion: {latest_run['conclusion']}")
        print(f"  Started: {latest_run['created_at']}")
        print(f"  URL: {latest_run['html_url']}")
        
        if latest_run['status'] == 'completed':
            print(f"\n🎉 Evaluation completed with conclusion: {latest_run['conclusion']}")
            
            # Get artifacts
            artifacts_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{latest_run['id']}/artifacts"
            headers = {}
            if token:
                headers['Authorization'] = f'token {token}'
            
            artifacts_response = requests.get(artifacts_url, headers=headers)
            if artifacts_response.status_code == 200:
                artifacts = artifacts_response.json()
                print(f"\n📁 Available artifacts ({artifacts['total_count']}):")
                for artifact in artifacts['artifacts']:
                    print(f"  - {artifact['name']} ({artifact['size_in_bytes']} bytes)")
                    print(f"    Download: {artifact['archive_download_url']}")
            
            break
        
        elif latest_run['status'] == 'in_progress':
            print("  ⏳ Evaluation in progress...")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python monitor_github_evaluation.py <repo_owner> <repo_name> [github_token]")
        print("Example: python monitor_github_evaluation.py benediktstroebl hal-harness")
        sys.exit(1)
    
    repo_owner = sys.argv[1]
    repo_name = sys.argv[2]
    token = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        monitor_evaluation(repo_owner, repo_name, token=token)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
