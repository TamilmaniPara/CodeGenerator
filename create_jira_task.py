```python
import json
import os
import sys
import urllib.request
import urllib.error
import base64


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def jira_request(method, url, username, token, payload=None):
    credentials = f"{username}:{token}"
    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")

            if response_body:
                return json.loads(response_body)

            return {}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")

        raise RuntimeError(
            f"Jira API failed.\n"
            f"HTTP Status: {e.code}\n"
            f"Response: {error_body}"
        )

    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Unable to connect to Jira: {e}"
        )


def build_description(task):
    metadata = task.get("metadata", {})
    data_elements = task.get("data_elements", [])
    analysis_notes = task.get("analysis_notes", [])

    lines = []

    lines.append("h2. Review Metadata")
    lines.append("")
    lines.append("|| Key || Value ||")

    for key, value in metadata.items():
        value = str(value).replace("|", "\\|")
        lines.append(f"| {key} | {value} |")

    lines.append("")
    lines.append("h2. Data Elements")
    lines.append("")

    headers = [
        "Source ID",
        "Source Name",
        "Database Name",
        "Schema Name",
        "Table/View Name",
        "Column Name",
        "Column Description",
        "Input Type",
        "Code Location",
    ]

    lines.append("|| " + " || ".join(headers) + " ||")

    for element in data_elements:

        code_locations = element.get("code_locations", [])

        if isinstance(code_locations, list):
            code_location = "<br>".join(
                str(x) for x in code_locations
            )
        else:
            code_location = str(code_locations)

        values = [
            element.get("source_id", ""),
            element.get("source_name", ""),
            element.get("database_name", ""),
            element.get("schema_name", ""),
            element.get("table_name", ""),
            element.get("column_name", ""),
            element.get("column_description", ""),
            element.get("input_type", ""),
            code_location,
        ]

        values = [
            str(value).replace("|", "\\|")
            for value in values
        ]

        lines.append("| " + " | ".join(values) + " |")

    if analysis_notes:
        lines.append("")
        lines.append("h2. Analysis Notes")
        lines.append("")

        for note in analysis_notes:
            lines.append(f"* {note}")

    return "\n".join(lines)


def get_epic(jira_url, epic_key, username, token):
    url = f"{jira_url}/rest/api/2/issue/{epic_key}"

    return jira_request(
        "GET",
        url,
        username,
        token
    )


def create_issue(
    jira_url,
    project_key,
    epic_key,
    summary,
    description,
    labels,
    assignee,
    reporter,
    username,
    token
):

    fields = {
        "project": {
            "key": project_key
        },
        "summary": summary,
        "description": description,
        "issuetype": {
            "name": "Task"
        },
        "labels": labels,
    }

    # Parent Epic handling.
    #
    # Jira Cloud/team-managed Jira may use different parent fields.
    # For classic Jira Epic relationships, "parent" may not be
    # supported for Task creation. See notes below.
    fields["parent"] = {
        "key": epic_key
    }

    if assignee:
        fields["assignee"] = {
            "name": assignee
        }

    if reporter:
        fields["reporter"] = {
            "name": reporter
        }

    payload = {
        "fields": fields
    }

    url = f"{jira_url}/rest/api/2/issue"

    return jira_request(
        "POST",
        url,
        username,
        token,
        payload
    )


def main():

    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "python jira/create_jira_task.py "
            "jira/generated_jira_task.json"
        )
        sys.exit(1)

    input_file = sys.argv[1]

    task = load_config(input_file)

    jira_url = os.environ.get("JIRA_URL")
    jira_username = os.environ.get("JIRA_USERNAME")
    jira_token = os.environ.get("JIRA_TOKEN")

    if not jira_url:
        raise RuntimeError("JIRA_URL environment variable is missing.")

    if not jira_username:
        raise RuntimeError(
            "JIRA_USERNAME environment variable is missing."
        )

    if not jira_token:
        raise RuntimeError(
            "JIRA_TOKEN environment variable is missing."
        )

    epic_key = task["epic_key"]
    summary = task["summary"]
    labels = task.get("labels", ["data-elements"])

    if not task.get("review_id"):
        raise RuntimeError("review_id is missing.")

    if not task.get("review_name"):
        raise RuntimeError("review_name is missing.")

    print(f"Epic: {epic_key}")
    print(f"Summary: {summary}")

    # Retrieve Epic information.
    epic = get_epic(
        jira_url,
        epic_key,
        jira_username,
        jira_token
    )

    epic_fields = epic.get("fields", {})

    project = epic_fields.get("project", {})
    project_key = project.get("key")

    if not project_key:
        raise RuntimeError(
            "Unable to determine project key from Epic."
        )

    epic_assignee = epic_fields.get("assignee")
    epic_reporter = epic_fields.get("reporter")

    assignee = None
    reporter = None

    if epic_assignee:
        assignee = (
            epic_assignee.get("name")
            or epic_assignee.get("accountId")
        )

    if epic_reporter:
        reporter = (
            epic_reporter.get("name")
            or epic_reporter.get("accountId")
        )

    description = build_description(task)

    print(
        f"Data elements: "
        f"{len(task.get('data_elements', []))}"
    )

    print("Creating Jira Task...")

    result = create_issue(
        jira_url=jira_url,
        project_key=project_key,
        epic_key=epic_key,
        summary=summary,
        description=description,
        labels=labels,
        assignee=assignee,
        reporter=reporter,
        username=jira_username,
        token=jira_token,
    )

    issue_key = result.get("key")

    if not issue_key:
        raise RuntimeError(
            f"Jira creation completed without issue key: {result}"
        )

    issue_url = (
        jira_url.rstrip("/")
        + "/browse/"
        + issue_key
    )

    print("")
    print("====================================")
    print("JIRA TASK CREATED SUCCESSFULLY")
    print("====================================")
    print(f"Task Key : {issue_key}")
    print(f"Task URL : {issue_url}")
    print(f"Summary  : {summary}")
    print("====================================")


if __name__ == "__main__":
    main()
```
