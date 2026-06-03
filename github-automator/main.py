import os
from typing import Literal

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("github-manager", json_response=True)

# Load a local .env only when present. Explicit env vars from Claude config win.
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(ENV_FILE):
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=ENV_FILE, override=False)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_URL = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}


# Initialize client
def get_client(extra_headers: dict | None = None):
    if not GITHUB_TOKEN:
        raise ValueError("Missing GITHUB_TOKEN. Set it in Claude's MCP config or in a local .env file.")

    headers = HEADERS.copy()
    if extra_headers:
        headers.update(extra_headers)

    return httpx.AsyncClient(base_url=GITHUB_URL, headers=headers)


# List out Issues
@mcp.tool()
async def list_issues(
    owner: str,
    repo: str,
    state: Literal["open", "closed", "all"] = "open",
    max_results: int = 50,
) -> str:
    """List repository issues by state. Pull requests are filtered out of the response."""
    if max_results < 1:
        return "Error: max_results must be at least 1."

    per_page = 20
    page = 1
    res = []
    try:
        async with get_client() as client:
            while len(res) < max_results:
                response = await client.get(
                    f"/repos/{owner}/{repo}/issues",
                    params={"state": state, "per_page": per_page, "page": page},
                )

                response.raise_for_status()

                page_data = response.json()

                if not page_data:
                    break

                for issue in page_data:
                    if "pull_request" not in issue:
                        res.append(
                            f"# Issue No: {issue['number']}, Description: {issue['title']}, State: {issue['state']}"
                        )

                    if len(res) >= max_results:
                        break

                if len(page_data) < per_page:
                    break

                page += 1

        return "\n".join(res) if res else "No Issues Found"
    except ValueError as exc:
        return f"Error: {exc}"
    except httpx.RequestError as exc:
        return f"An error occurred while requesting {exc.request.url!r}."
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return f"Error: Repository '{repo}' for the owner {owner} not found."
        if exc.response.status_code == 401:
            return "Error: Authentication failed. Your GITHUB_TOKEN is invalid or expired."
        return f"GitHub API Error ({exc.response.status_code}): {exc.response.text}"


# add comment to an issue
@mcp.tool()
async def add_comment(owner: str, repo: str, issue_no: int, comment: str) -> str:
    """Create a comment on a specific GitHub issue."""
    try:
        async with get_client() as client:
            response = await client.post(
                f"/repos/{owner}/{repo}/issues/{issue_no}/comments",
                json={"body": comment},
            )

            response.raise_for_status()

            return f"Successfully added comment to issue #{issue_no}."
    except ValueError as exc:
        return f"Error: {exc}"
    except httpx.HTTPStatusError as exc:
        return f"Failed to add comment: {exc.response.text}"
    except httpx.RequestError as exc:
        return f"An error occurred while requesting {exc.request.url!r}."


# add label
@mcp.tool()
async def add_label(owner: str, repo: str, issue_no: int, labels: list[str]) -> str:
    """Add labels to an issue or pull request."""
    if not labels:
        return "Error: labels must contain at least one label."

    try:
        async with get_client() as client:
            response = await client.post(
                f"/repos/{owner}/{repo}/issues/{issue_no}/labels",
                json={"labels": labels},
            )

            response.raise_for_status()

            return f"Successfully added labels to issue or pull request #{issue_no}."
    except ValueError as exc:
        return f"Error: {exc}"
    except httpx.HTTPStatusError as exc:
        return f"Failed to add label: {exc.response.text}"
    except httpx.RequestError as exc:
        return f"An error occurred while requesting {exc.request.url!r}."


# analyze the pr_diff
@mcp.tool()
async def analyze_pr_diff(owner: str, repo: str, pull_number: int) -> str:
    """Fetch the raw diff for a pull request so Claude can review the code changes."""
    diff_override = {"Accept": "application/vnd.github.diff"}

    try:
        async with get_client(extra_headers=diff_override) as client:
            response = await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}")
            response.raise_for_status()
            return response.text
    except ValueError as exc:
        return f"Error: {exc}"
    except httpx.HTTPStatusError as exc:
        return f"Failed to retrieve PR diff: {exc.response.text}"
    except httpx.RequestError as exc:
        return f"An error occurred while requesting {exc.request.url!r}."


# accept pull request
@mcp.tool()
async def accept_pr(
    owner: str,
    repo: str,
    pull_number: int,
    merge_method: Literal["merge", "squash", "rebase"] = "squash",
    commit_title: str | None = None,
    commit_message: str | None = None,
) -> str:
    """Merge a pull request using 'merge', 'squash', or 'rebase'. This permanently merges code into the base branch."""
    try:
        async with get_client() as client:
            pack = {"merge_method": merge_method}

            if commit_message and commit_title:
                pack.update(
                    {
                        "commit_title": commit_title,
                        "commit_message": commit_message,
                    }
                )

            response = await client.put(
                f"/repos/{owner}/{repo}/pulls/{pull_number}/merge",
                json=pack,
            )

            response.raise_for_status()

            return f"Successfully merged pull request #{pull_number} using '{merge_method}'."

    except ValueError as exc:
        return f"Error: {exc}"
    except httpx.HTTPStatusError as exc:
        return f"Failed to merge pull request: {exc.response.text}"
    except httpx.RequestError as exc:
        return f"An error occurred while requesting {exc.request.url!r}."


# decline pull request
@mcp.tool()
async def decline_pr(owner: str, repo: str, pull_number: int) -> str:
    """Close a pull request without merging it."""
    try:
        async with get_client() as client:
            response = await client.patch(
                f"/repos/{owner}/{repo}/pulls/{pull_number}",
                json={"state": "closed"},
            )

            response.raise_for_status()

            return f"Successfully closed pull request #{pull_number} without merging."

    except ValueError as exc:
        return f"Error: {exc}"
    except httpx.HTTPStatusError as exc:
        return f"Failed to close pull request: {exc.response.text}"
    except httpx.RequestError as exc:
        return f"An error occurred while requesting {exc.request.url!r}."
