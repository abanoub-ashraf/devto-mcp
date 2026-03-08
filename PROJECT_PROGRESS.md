# Project Progress Tracker

## Purpose

This file is the handoff log for future work on this Dev.to MCP server. It explains what was changed during the current reset-and-rebuild pass, what the current project shape is, and what remains unfinished.

## What Was Done In This Reset

### Repository reset

- removed the inherited `.git` directory
- removed prior git history from the local folder
- initialized a fresh local git repository

### Security cleanup

- ran a leak sweep before preparing the repo for a new remote
- found no obvious live API keys or tokens
- found `firebase-debug.log`, which contained personal email metadata and should not be published
- removed `firebase-debug.log`
- updated `.gitignore` to keep local logs and `.omx/` out of version control

### Versioning

- bumped the package version in `pyproject.toml` from `0.1.0` to `1.0.0`

### Documentation

- replaced the minimal README with a larger, operational README covering:
  - setup
  - MCP config
  - tool list
  - draft workflow
  - troubleshooting
  - development notes
  - limitations
  - roadmap

### API and MCP surface already present in code

The current `server.py` includes:

- article listing and detail tools
- custom search helpers
- tag-combo matching
- listings reading
- video article reading
- draft creation and update
- authenticated "my articles" helpers
- unpublish support

## Verified State

The following checks passed during this session:

```bash
uv run python -m py_compile server.py
uv run python -c "import server; print('server import ok')"
```

The MCP was also reported by the user as working in the client before the repo reset request.

## Known Product Limitations

- no documented native scheduling endpoint
- no documented public delete-draft endpoint
- search helpers are client-side keyword filters over fetched article sets
- multi-tag strict intersection is also enforced client-side

## Files That Matter Most

- `server.py`
- `README.md`
- `pyproject.toml`
- `.env.example`
- `.gitignore`

## Suggested Next Steps

### Immediate

- create the new remote repository
- push the fresh local history
- create and push the `v1.0.0` tag

### Nice to have

- add a `publish_article(article_id)` wrapper for cleaner publish UX
- add lightweight automated tests for formatters and helper behavior
- validate category inputs for listings
- consider splitting `server.py` if the tool surface keeps growing

## Remote Publishing Checklist

- confirm whether the new GitHub repo should be public or private
- create the remote repository
- add the remote to local git
- push the branch
- create tag `v1.0.0`
- push the tag

## Notes For Future You

- if you see `firebase-debug.log` again, do not commit it
- if write tools fail, check the MCP client env injection first
- if search feels weak, remember that it is intentionally constrained by the public API surface
- if you are tempted to add a lot more tools, stop and ask whether they are actually used or if you are just collecting endpoints like cursed Pokemon cards
