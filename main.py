import os 
from git_handler import git_handler
from jira_handler import jira_handler
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

# Get necessary enivonment variables
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
EMAIL = os.getenv("EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")


def main():
    try:
        # Initialize Git Handler
        git = git_handler(GITHUB_ACCESS_TOKEN)
        alert = git.get_alerts()

        # Initialize Jira Handler
        jira = jira_handler(EMAIL, JIRA_API_TOKEN, alert)
        jira.create_alert()
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()