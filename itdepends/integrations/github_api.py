import requests

import os
from datetime import datetime, timezone
from ..utils import diff_in_months

class GitHubClient:
    def __init__(self, token=None, timeout=10):
        self.session = create_github_session(token)
        self.session.timeout = timeout
        self.base_url = "https://api.github.com/repos/"
        
    def do_safe_request(self, url):
        try:
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json(), None
            
            return None, response.status_code
            
        except requests.exceptions.Timeout:
            return None, "timeout"
        
    def verify_repo_existance(self, repo_name):
        url = self.base_url + repo_name
        
        response = self.session.get(url)
        
        return response.status_code == 200
    
    def verify_inactivity(self, repo_name, max_months=6):
        url = self.base_url + repo_name
        
        data, error = self.do_safe_request(url)
        
        pushed_at_str = data.get("pushed_at")
        
        if not pushed_at_str: # New repo
            return True
        
        today = datetime.now(timezone.utc)
        last_push_data = datetime.strptime(pushed_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        
        diff = diff_in_months(last_push_data, today)
        
        if (diff > max_months): return True
        
        return False
    
    def verify_archived(self, repo_name):
        url = self.base_url + repo_name
        
        data, error = self.do_safe_request(url)
        
        is_archived = data.get("archived", False)
        
        return is_archived
        
def create_github_session(token=None):
    session = requests.Session()
    
    final_token = token if token else os.environ.get("GITHUB_TOKEN")
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28" 
    }
    
    if final_token:
        headers["Authorization"] = f"token {final_token}"
        # Print que mostra que token é utilizado

    session.headers.update(headers)
    return session
