# GitHub Automator MCP Server

An MCP server for letting Claude work with GitHub issues and pull requests through the official Python MCP SDK.

The server is named `github-manager` and exposes tools for listing issues, commenting on issues, adding labels, reading PR diffs, merging PRs, and closing PRs.


## Tools

| Tool | Purpose |
| --- | --- |
| `list_issues` | Lists repository issues by `open`, `closed`, or `all` state. Pull requests are filtered out. |
| `add_comment` | Adds a comment to a GitHub issue. |
| `add_label` | Adds one or more labels to an issue or pull request. |
| `analyze_pr_diff` | Fetches the raw diff for a pull request so Claude can review it. |
| `accept_pr` | Merges a pull request with the requested merge method. |
| `decline_pr` | Closes a pull request without merging it. |

## Requirements

- Python 3.13 or newer
- A GitHub personal access token
- `uv` recommended, or `pip` as a fallback

The token must be available as `GITHUB_TOKEN`.

For read-only issue listing and PR diff review, a fine-grained token with repository read access is enough. For comments, labels, merging, or closing PRs, give the token the matching write permissions for the target repositories.

## Setup

From this folder:

```powershell
cd "C:\Users\DELL\OneDrive\Documents\PBL\GitHub & PR Automator\github-automator"
uv sync
```

Or with pip:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your token for the current terminal session:

```powershell
$env:GITHUB_TOKEN = "github_pat_your_token_here"
```

You can also keep a local `.env` file:

```env
GITHUB_TOKEN=github_pat_your_token_here
```

Do not commit real tokens.

## Run Locally

Use the MCP Inspector while developing and Run it as a stdio MCP server:

```powershell
npx -y @modelcontextprotocol/inspector 
```

## Add To Claude Desktop

The MCP Python SDK can install FastMCP servers into Claude Desktop:

```powershell
uv run mcp install github-manager.py --name "GitHub Manager" -v GITHUB_TOKEN=github_pat_your_token_here
```

If you already have a `.env` file:

```powershell
uv run mcp install github-manager.py --name "GitHub Manager" -f .env
```

Restart Claude Desktop after installing the server.

You can also add it manually to `claude_desktop_config.json`:

Use absolute paths for manual configuration. This avoids Claude Desktop starting from a different working directory and failing to find `uv.exe` or `github-manager.py`.

```json
{
  "mcpServers": {
    "github-manager": {
      "command": "C:\\Users\\DELL\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\uv.exe",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "C:\\Users\\DELL\\OneDrive\\Documents\\PBL\\GitHub & PR Automator\\github-automator\\github-manager.py"
      ],
      "env": {
        "GITHUB_TOKEN": "github_pat_your_token_here"
      }
    }
  }
}
```

Replace the `command` value with the absolute path to your own `uv.exe`, and replace the final argument with the absolute path to your own `github-manager.py`.

On Windows, Claude Desktop normally reads this file from:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

## Add To Claude Code

From the `github-automator` folder:

```powershell
claude mcp add --transport stdio --env GITHUB_TOKEN=github_pat_your_token_here github-manager -- uv run mcp run github-manager.py:mcp
```

Then check the connection inside Claude Code:

```text
/mcp
```

Useful management commands:

```powershell
claude mcp list
claude mcp get github-manager
claude mcp remove github-manager
```

## Example Prompts

```text
List open issues in owner/repo and summarize what needs attention.
```

```text
Fetch PR #12's diff in owner/repo and review it for bugs.
```

```text
Add the labels bug and priority-high to issue #7 in owner/repo.
```

```text
Comment on issue #4 in owner/repo saying that the fix is being investigated.
```

## Notes

- `accept_pr` performs a real merge. Use it only when you are ready to merge the pull request.
- `decline_pr` closes a pull request. It does not delete branches.
- `state` for `list_issues` should be `open`, `closed`, or `all`.
- `merge_method` for `accept_pr` should be `merge`, `squash`, or `rebase`.
- The server reads `GITHUB_TOKEN` from the process environment.

## References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Code MCP setup](https://code.claude.com/docs/en/mcp)
