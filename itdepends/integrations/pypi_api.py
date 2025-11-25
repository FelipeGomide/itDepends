import requests
import re

class PyPiClient():
    def __init__(self, timeout=10):
        self.session = create_session()
        self.session.timeout = timeout
        self.base_url = "https://pypi.org/pypi/"
        
    def do_safe_request(self, url):
        try:
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json(), None
            
            return None, response.status_code
            
        except requests.exceptions.Timeout:
            return None, "timeout"
        
    def verify_development_status(self, package_name):
        url = self.base_url + package_name + "/json"
        
        data, error = self.do_safe_request(url)
        
        if error:
            return False, error

        classifiers = data.get("info", {}).get("classifiers", [])

        if not classifiers:
            return False, "no_classifiers_available"
        
        status_regex = re.compile(r"Development Status :: (\d - [A-Za-z/]+)")
        
        status_number = None
        for classifier in classifiers:
            match = status_regex.search(classifier)
            if match:
                status_number = match.group(1)
                break    
            
        return True, status_number
    
    def get_github_repo_name(self, package_name):
        url = self.base_url + package_name + "/json"
        
        data, error = self.do_safe_request(url)
        
        if error:
            return False, error

        info = data.get("info", {})
        
        project_urls = info.get("project_urls", {})
        
        if not project_urls:
            return False, "There was no urls linked to the project"

        package_github = []
        
        for section in project_urls:
            url = project_urls.get(section, None)
            
            if "github.com" in url:
                package_github.append(url)

        if len(package_github) == 0:
            return False, f"Couldn't find file with name '{package_name}'."
        
        for val in package_github:
            match = re.search(r"github\.com/([^/]+)/([^/]+)", val)
            
            if match:
                owner = match.group(1)
                repo = match.group(2).split(".")[0]
                return True, owner + "/" + repo
            
        return False, f"URLs found, but couldn't parse owner/repo."
        
def create_session():
    session = requests.Session()
    
    headers = {
        "User-Agent": "PyPiClient-itDepends",
        "Accept": "application/json"
    }

    session.headers.update(headers)
    return session
