from generated.servers.github import list_issues
from generated.servers.google_workspace import send_gmail_message

issues_result = await list_issues(
    owner="pydantic",
    repo="pydantic-ai",
    state="OPEN",
    …)

issues = issues_result.get('issues', [])
…
email_result = await send_gmail_message(
    user_google_email="eleonore@datalayer.io",
    to="eleonore@datalayer.io",
    subject="Bug Issues Report: pydantic/pydantic-ai (20 Most Recent)",
    body=email_body,
    body_format="plain"
)
