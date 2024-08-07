import os 
import json
import requests

class git_handler:

    def __init__(self, access_token):

        # Github API details
        GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
        GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
        BRANCH_NAME = "main"

        self.github_api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/code-scanning/alerts"
        self.access_token = access_token

    def get_alerts(self):
        # Set up headers for the Github API request
        github_headers = {
        "Authorization": f"token {self.access_token}",
        "Accept": "application/vnd.github.v3+json"
        }

        try:
            response = requests.get(self.github_api_url, headers=github_headers)
            response.raise_for_status()        # Check for HTTP errors

            all_alerts = response.json()

            alerts = [alert for alert in all_alerts if alert["state"] == "open"]

            # Write alerts to a JSON file
            file_path = "alerts.json"
            with open(file_path, "w") as json_file:
                json.dump(alerts, json_file, indent = 4)
            
            return(alerts)
        except requests.exceptions.RequestException as e:
            return []
