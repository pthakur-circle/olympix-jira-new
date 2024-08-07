from jira import JIRA
import os 
import requests
import json
import datetime
from requests.auth import HTTPBasicAuth

class jira_handler:

    def __init__(self, email, jira_api_token, alerts):
        # Jira API details
        JIRA_SERVER = os.getenv("JIRA_SERVER")
        JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
        self.GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
        self.GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
        self.alerts = alerts

        jira_auth = (email, jira_api_token)

        self.jira = JIRA(server=JIRA_SERVER, basic_auth=jira_auth)

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.auth = HTTPBasicAuth(email, jira_api_token)


    def _create_alert_issue(self, alert):
        
        severity_to_priority = {
            "critical": "Highest",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            }
        priority = severity_to_priority[alert["rule"]["security_severity_level"]]
        url = "https://circlepay.atlassian.net/rest/api/3/issue"

        rule_id = alert["rule"]["id"]
        message_text = alert["most_recent_instance"]["message"]["text"]
        tool_name = alert["tool"]["name"]
        location = alert["most_recent_instance"]["location"]
        summary = f"{tool_name} [{self.GITHUB_REPO_NAME}]: {rule_id}"
        created = datetime.datetime.strptime(
                        alert["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                    ).strftime("%B %d, %Y %H:%M")
        updated = datetime.datetime.strptime(
                        alert["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                    ).strftime("%B %d, %Y %H:%M")

        description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Alert created on {created} (updated on {updated}) ",
                        },
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Discovered in: ",
                        },
                        {
                            "type": "text",
                            "text":  f"{self.GITHUB_REPO_OWNER}/{self.GITHUB_REPO_NAME}",
                            "marks": [{"type": "strong"}],
                        },
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Vulnerable code: ",
                        },
                        {
                            "type": "text",
                            "text": f'{alert["most_recent_instance"]["location"]["path"]}, lines {location["start_line"]}-{location["end_line"]}, column {location["start_column"]}-{location["start_column"]}  ',
                        },
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Description: ",
                            "marks": [{"type": "strong"}],
                        },
                        {
                            "type": "text",
                            "text": message_text,
                        },
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Link to Alert: ",
                            "marks": [{"type": "strong"}],
                        },
                        {
                            "type": "text",
                            "text": alert["html_url"],
                            "marks": [{"type": "link", "attrs": {"href": alert["html_url"]},}],
                        },
                    ],
                },
            ]
        }

        payload = {
            "fields": {
                "project": {
                    "key": "SEO"
                },
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Bug"},
                "priority": {"name": priority},
            }
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(payload),
                auth=self.auth,
            )
            response.raise_for_status()     # Check for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating issue in Jira: {e}")
            return None

        # issue_dict = {
        #     "project": {"id": 12881},
        #     "summary": f"{tool_name} Alert: {rule_id}",
        #     "description": description,
        #     "issuetype": {"name": "Bug"},
        #     "priority": {"name": severity_to_priority[alert["rule"]["security_severity_level"]]},
        # }
            

        # try:
        #     issue = self.jira.create_issue(fields=issue_dict)
        #     print(issue.fields)
        #     print("Alert posted to Jira.")
        # except Exception as e:
        #     print(f"Failed to post alert to Jira: {e}")

        #     if hasattr(e, 'response'):
        #         print("Response from Jira API:")
        #         print(e.response.text)


    def get_issue_by_alert_url(self, alert_url):
        url = "https://circlepay.atlassian.net/rest/api/3/search"
        jql_query = f'project=SEO AND description ~ "{alert_url}"'
        params = {"jql": jql_query}

        try:
            response = requests.request(
                "GET",
                url,
                headers=self.headers,
                auth=self.auth,
                params=params,
                timeout=60,
            )
            response.raise_for_status()        # Check for HTTP errors
            # if response.status_code != 200:
            #     error_msg = f"Error in get_issue_by_alert_url: {response.status_code}"
            #     print(error_msg)
            #     print(response.text)
            #     return None
            
            issues = json.loads(response.text)["issues"]
            theIssue = None
            issueCount = 0

            if issues is not None:
                for issue in issues:
                    if issue is not None:
                        issueCount += 1
                        description = (
                            issue["fields"]
                            .get("description", {"type": "", "content": []})
                            .get("content", [])
                        )
                        for block in description:
                            if block.get("type") == "paragraph":
                                for content in block.get("content", []):
                                    if content.get(
                                        "type"
                                    ) == "text" and alert_url in content.get(
                                        "text", ""
                                    ):
                                        if issueCount <= 1:
                                            theIssue = issue
                                        else:
                                            print(
                                                f"Key Err:{issueCount} JIRA tickets with the same GHAS link found"
                                            )
                                            break
            return theIssue
        except requests.exceptions.RequestException as e:
            print(f"Error fetchinng issue by alert URL from Jira: {e}")

    def create_alert(self):
        alerts_added = []
        for alert in self.alerts:

            oldIssueIfApplies = None

            oldIssueIfApplies = self.get_issue_by_alert_url(alert["html_url"])
            

            if oldIssueIfApplies is None:
                print(f"Creating issue: {alert['html_url']}")
                issue = self._create_alert_issue(alert)
                alerts_added.append(issue)
            
            else:
                print("Issue already exists!")

        return alerts_added
    

