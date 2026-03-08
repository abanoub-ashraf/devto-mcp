# Dev.to MCP Server

> v1.0.0
>
> Read, research, draft, and publish Dev.to content via MCP and the Forem API.

[![Version](https://img.shields.io/badge/version-1.0.0-black.svg)](https://github.com/abanoub-ashraf/devto-mcp/releases/tag/v1.0.0)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

## Fresh setup for reading, researching, drafting, and publishing Dev.to content through MCP

This repository contains a Python MCP server for Dev.to / Forem. It is built for local use with MCP clients such as Claude Desktop and Cursor, and it focuses on the workflows that are actually useful day to day:

- read trending and latest articles
- filter content by tag combinations
- search articles with local keyword matching
- inspect comments, tags, listings, and video posts
- create drafts
- update drafts
- publish drafts by updating `published=true`

The server uses the Forem v1 API contract via the v1 `Accept` header and the public Dev.to API base URL.

## Quick pitch

If you want an MCP that can help you scout Dev.to trends, mine tags and comments for ideas, keep drafts flowing, and publish from the same chat surface, this is the repo. No weird framework cosplay, just a focused Python MCP server that does the job.

## What This MCP Does

This MCP gives your AI client direct access to Dev.to content and authoring workflows. It is useful for:

- content research
- indie hacking idea validation
- cross-posting from YouTube, notes, or newsletters
- drafting Dev.to posts without leaving your MCP client
- reading comments and adjacent content for product or content ideas

## Current Capabilities

### Read tools

- `get_latest_articles()`
- `get_top_articles()`
- `get_trending_articles(tag=None, top=7, page=1, per_page=10)`
- `list_articles(page=1, per_page=30, tag=None, tags=None, tags_exclude=None, username=None, state=None, top=None)`
- `get_articles_by_tag(tag)`
- `get_article_by_id(id)`
- `get_article(article_id=None, username=None, slug=None)`
- `get_article_details(article_id)`
- `get_articles_by_username(username)`
- `get_user_articles(username, page=1, per_page=30, state=None)`
- `get_article_comments(article_id)`
- `get_tags(page=1, per_page=10)`
- `get_listings(page=1, per_page=30, category=None)`
- `get_video_articles(page=1, per_page=24)`
- `get_user_info(username)`

### Search helpers

- `search_articles(query, page=1)`
- `search_articles_advanced(query, page=1, per_page=30, tag=None, tags=None, top=None)`
- `search_by_tag_combo(tags, page=1, per_page=30, top=None)`

### Write tools

- `create_article(title, body_markdown, tags, published)`
- `update_article(article_id, title=None, body_markdown=None, tags=None, published=None)`
- `get_my_articles(page=1, per_page=30)`
- `get_my_published_articles(page=1, per_page=30)`
- `get_my_unpublished_articles(page=1, per_page=30)`
- `get_my_all_articles(page=1, per_page=30)`
- `unpublish_article(article_id, note=None)`

## Important Limitations

- There is no documented native scheduling endpoint in the public Dev.to API.
- There is no documented draft deletion endpoint in the public Dev.to API.
- `search_articles` and `search_articles_advanced` do keyword matching client-side after fetching article lists.
- `search_by_tag_combo` performs true tag intersection client-side because the public API tag filters are broader than strict intersection.
- `get_listings` uses the listings endpoint with the v1 `Accept` header, following Forem's compatibility guidance.

## Requirements

- macOS, Linux, or another environment that can run Python 3.11+
- `uv`
- a Dev.to API key for authenticated operations
- an MCP client such as Claude Desktop or Cursor

## Project Structure

```text
devto-mcp/
├── .env.example
├── .gitignore
├── Demo.png
├── LICENSE
├── PROJECT_PROGRESS.md
├── README.md
├── pyproject.toml
├── server.py
└── uv.lock
```

## Install `uv`

If you do not have `uv`, install it first.

### macOS

```bash
brew install uv
```

### Cross-platform option

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, verify:

```bash
uv --version
```

## Get a Dev.to API Key

Open:

```text
https://dev.to/settings/extensions
```

Create or copy your API key, then keep it out of git. Use MCP client environment config, not hardcoded values in source files.

## Local Setup

Clone the repo and enter it:

```bash
git clone <YOUR_NEW_REPO_URL>
cd devto-mcp
```

Optional local env file for your own shell usage:

```bash
cp .env.example .env
```

Then edit `.env` and replace the placeholder with your real key if you plan to run ad hoc shell tests. Your MCP client can also inject the environment variable directly, which is usually cleaner.

## Connection Block

Use this MCP config block:

```json
{
  "mcpServers": {
    "devto": {
      "command": "<PATH_TO_UV>",
      "args": [
        "--directory",
        "<PATH_TO_REPO>",
        "run",
        "server.py"
      ],
      "env": {
        "DEV_TO_API_KEY": "YOUR_DEVTO_API_KEY"
      }
    }
  }
}
```

Replace:

- `YOUR_DEVTO_API_KEY` with your real Dev.to API key
- `<PATH_TO_UV>` with the output of `which uv`
- `<PATH_TO_REPO>` with the absolute path to this repository

## Where To Put The MCP Config

### Claude Desktop

Save the config in:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Cursor

Save the config in:

```text
~/.cursor/mcp.json
```

After editing the config, fully restart the MCP client.

## First Verification

Run these commands from the project root:

```bash
uv run python -m py_compile server.py
uv run python -c "import server; print('server import ok')"
```

If both pass, the local code is structurally healthy.

## Smoke Test Prompts

After restarting your MCP client, try:

- `Show me the latest Dev.to articles`
- `Get trending Dev.to articles for swift from the last 7 days`
- `Search Dev.to articles for SwiftUI performance`
- `Find Dev.to articles tagged swift and architecture`
- `Show me Dev.to video articles`
- `Get Dev.to listings for jobs`

## Draft Workflow

The safest write path is draft-first.

### Create a draft

Example prompt:

```text
Create a Dev.to draft titled "MCP test draft" with body "# Test\n\nThis is a draft created from my MCP." and tags "test,mcp" and published false
```

### Verify drafts

Example prompt:

```text
Show my unpublished Dev.to articles
```

### Update a draft

Example prompt:

```text
Update article 123456 and change the title to "MCP draft updated"
```

### Publish a draft

The publish flow is done through update, not a separate publish endpoint:

```text
Update article 123456 and set published true
```

## Search Workflows

### General keyword search

Use:

```text
Search Dev.to articles for Swift concurrency
```

This maps to `search_articles`.

### Filtered keyword search

Use:

```text
Use search_articles_advanced to find posts about app marketing with tag indie and top 30 days
```

### True multi-tag intersection

Use:

```text
Use search_by_tag_combo with tags swift,architecture
```

This performs a true tag intersection on the client side after fetching the article set.

## Tool Notes

### `search_articles`

This is a lightweight keyword matcher over fetched article lists.

### `search_articles_advanced`

This combines keyword matching with article filters such as:

- `tag`
- `tags`
- `top`
- `page`
- `per_page`

### `search_by_tag_combo`

This is the stricter tool for "must contain all tags" scenarios.

### `get_listings`

This returns Dev.to listings such as jobs, collabs, products, and similar categories when available.

### `get_video_articles`

This returns published Dev.to video articles for reading workflows.

## Authenticated Endpoints

These operations require `DEV_TO_API_KEY`:

- `create_article`
- `update_article`
- `get_my_articles`
- `get_my_published_articles`
- `get_my_unpublished_articles`
- `get_my_all_articles`
- `unpublish_article`
- `get_user_info`

If auth fails, check the key in your MCP config first. Nine times out of ten the bug is not deep, it is just a missing or stale environment value wearing a fake mustache.

## Troubleshooting

### MCP client does not show the server

- confirm the config file is in the correct client path
- confirm the `command` path points to your real `uv`
- confirm the `args` path points to the real repo directory
- fully restart the client

### Read tools work but write tools fail

- confirm `DEV_TO_API_KEY` is present
- confirm the key is valid in Dev.to settings
- confirm the client restarted after config changes

### Draft publish flow fails

- verify the article ID is correct
- verify the post belongs to the authenticated account
- retry with `get_my_unpublished_articles` to inspect current state

### Search feels incomplete

That is expected for the custom keyword helpers because the public API does not expose a full dedicated article search endpoint in the documented flow used here.

## Development

### Run ad hoc local checks

```bash
uv run python -m py_compile server.py
uv run python -c "import server; print('server import ok')"
```

### Main implementation file

- `server.py` contains the MCP tool registrations, API client helpers, and response formatters.

### Dependency file

- `pyproject.toml` defines the Python dependencies and package metadata.

## Security Notes

- never commit real API keys
- prefer MCP client env injection over hardcoding credentials
- avoid committing local logs
- treat debug logs as potentially sensitive even when they do not contain tokens

This repository was specifically cleaned to avoid carrying forward an old `.git` history and a local debug log with personal email metadata.

## Roadmap

Potential future improvements:

- add a dedicated `publish_article(article_id)` convenience tool
- add richer formatting for comments and article bodies
- add direct single-video lookup if needed
- add automated tests around formatter behavior
- add typed validation around input ranges and categories

## License

MIT. See `LICENSE`.
