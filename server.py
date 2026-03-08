import os

import httpx
from mcp.server.fastmcp import FastMCP

# Create a Dev.to MCP server
mcp = FastMCP("Dev.to MCP Server")

# Constants
BASE_URL = os.getenv("DEV_TO_BASE_URL", "https://dev.to/api").rstrip("/")
API_ACCEPT = "application/vnd.forem.api-v1+json"

# Helper functions
def build_headers(require_auth: bool = False, include_json: bool = False) -> dict[str, str]:
    """Build standard Forem API headers."""
    headers = {"accept": API_ACCEPT}
    if include_json:
        headers["content-type"] = "application/json"

    if require_auth:
        api_key = os.getenv("DEV_TO_API_KEY")
        if not api_key:
            raise ValueError("DEV_TO_API_KEY is required for this operation.")
        headers["api-key"] = api_key

    return headers


async def request_api(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
    require_auth: bool = False,
) -> dict | list | None:
    """Make a request to the Dev.to/Forem API."""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}{path}"
        response = await client.request(
            method,
            url,
            params=params,
            json=json,
            headers=build_headers(require_auth=require_auth, include_json=json is not None),
            timeout=10.0,
        )
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()


async def fetch_from_api(path: str, params: dict | None = None, require_auth: bool = False) -> dict | list:
    """Helper function to fetch data from Dev.to API."""
    return await request_api("GET", path, params=params, require_auth=require_auth)

# Resources

@mcp.tool()
async def get_latest_articles() -> str:
    """Get the latest articles from Dev.to"""
    articles = await fetch_from_api("/articles/latest")
    return format_articles(articles[:10])  # Limiting to 10 for readability
    
@mcp.tool()
async def get_top_articles() -> str:
    """Get the top articles from Dev.to"""
    articles = await fetch_from_api("/articles")
    return format_articles(articles[:10])  # Limiting to 10 for readability


@mcp.tool()
async def list_articles(
    page: int = 1,
    per_page: int = 30,
    tag: str | None = None,
    tags: str | None = None,
    tags_exclude: str | None = None,
    username: str | None = None,
    state: str | None = None,
    top: int | None = None,
) -> str:
    """
    List articles using the official Forem article filters.

    Args:
        page: Pagination page number
        per_page: Number of items to return
        tag: Single tag filter
        tags: Comma-separated tag filter
        tags_exclude: Comma-separated excluded tag filter
        username: Username or organization filter
        state: Article state filter (fresh, rising, all)
        top: Return top articles from the last N days
    """
    params = {
        "page": page,
        "per_page": per_page,
        "tag": tag,
        "tags": tags,
        "tags_exclude": tags_exclude,
        "username": username,
        "state": state,
        "top": top,
    }
    filtered_params = {key: value for key, value in params.items() if value is not None}
    articles = await fetch_from_api("/articles", params=filtered_params)
    return format_articles(articles[: min(per_page, 30)])

@mcp.tool()
async def get_articles_by_tag(tag: str) -> str:
    """Get articles by tag from Dev.to"""
    articles = await fetch_from_api("/articles", params={"tag": tag})
    return format_articles(articles[:10])  # Limiting to 10 for readability

@mcp.tool()
async def get_article_by_id(id: str) -> str:
    """Get a specific article by ID from Dev.to"""
    article = await fetch_from_api(f"/articles/{id}")
    return format_article_details(article)

# Tools

@mcp.tool()
async def search_articles(query: str, page: int = 1) -> str:
    """
    Search for articles on Dev.to using keyword matching over the article feed.
    
    Args:
        query: Search term to find articles
        page: Page number for pagination (default: 1)
    """
    articles = await fetch_from_api("/articles", params={"page": page})
    
    filtered_articles = [
        article for article in articles 
        if query.lower() in article.get("title", "").lower() or 
           query.lower() in article.get("description", "").lower()
    ]
    
    return format_articles(filtered_articles[:10])


@mcp.tool()
async def search_articles_advanced(
    query: str,
    page: int = 1,
    per_page: int = 30,
    tag: str | None = None,
    tags: str | None = None,
    top: int | None = None,
) -> str:
    """
    Search articles by keyword with optional tag and popularity filters.

    Note:
        Forem does not expose a dedicated full-text article search endpoint in these docs,
        so keyword matching is applied client-side after fetching the filtered article list.
    """
    params = {
        "page": page,
        "per_page": per_page,
        "tag": tag,
        "tags": tags,
        "top": top,
    }
    filtered_params = {key: value for key, value in params.items() if value is not None}
    articles = await fetch_from_api("/articles", params=filtered_params)
    query_lower = query.lower()
    filtered_articles = [
        article
        for article in articles
        if query_lower in article.get("title", "").lower()
        or query_lower in article.get("description", "").lower()
    ]
    return format_articles(filtered_articles[: min(per_page, 30)])

@mcp.tool()
async def get_article_details(article_id: int) -> str:
    """
    Get detailed information about a specific article
    
    Args:
        article_id: The ID of the article to retrieve
    """
    article = await fetch_from_api(f"/articles/{article_id}")
    return format_article_details(article)


@mcp.tool()
async def get_article(article_id: int | None = None, username: str | None = None, slug: str | None = None) -> str:
    """
    Get a published article either by numeric ID or by username + slug path.

    Args:
        article_id: Numeric article ID
        username: Author or organization username
        slug: Article slug
    """
    if article_id is not None:
        article = await fetch_from_api(f"/articles/{article_id}")
        return format_article_details(article)

    if username and slug:
        article = await fetch_from_api(f"/articles/{username}/{slug}")
        return format_article_details(article)

    return "Provide either article_id, or both username and slug."


@mcp.tool()
async def get_trending_articles(tag: str | None = None, top: int = 7, page: int = 1, per_page: int = 10) -> str:
    """
    Get trending articles overall or within a tag over the last N days.

    Args:
        tag: Optional tag filter
        top: Lookback window in days
        page: Pagination page number
        per_page: Number of items to return
    """
    params = {"page": page, "per_page": per_page, "top": top}
    if tag:
        params["tag"] = tag
    articles = await fetch_from_api("/articles", params=params)
    return format_articles(articles[: min(per_page, 30)])

@mcp.tool()
async def get_articles_by_username(username: str) -> str:
    """
    Get articles written by a specific user
    
    Args:
        username: The username of the author
    """
    articles = await fetch_from_api("/articles", params={"username": username})
    return format_articles(articles[:10])


@mcp.tool()
async def get_user_articles(username: str, page: int = 1, per_page: int = 30, state: str | None = None) -> str:
    """
    Get articles by a specific user or organization.

    Args:
        username: Username or organization handle
        page: Pagination page number
        per_page: Number of items to return
        state: Optional state filter, such as "all"
    """
    params = {"username": username, "page": page, "per_page": per_page, "state": state}
    filtered_params = {key: value for key, value in params.items() if value is not None}
    articles = await fetch_from_api("/articles", params=filtered_params)
    return format_articles(articles[: min(per_page, 30)])


@mcp.tool()
async def get_my_articles(page: int = 1, per_page: int = 30) -> str:
    """
    Get the authenticated user's articles.

    Args:
        page: Pagination page number
        per_page: Number of items to return
    """
    articles = await fetch_from_api(
        "/articles/me",
        params={"page": page, "per_page": per_page},
        require_auth=True,
    )
    return format_articles(articles[: min(per_page, 30)])


@mcp.tool()
async def get_my_published_articles(page: int = 1, per_page: int = 30) -> str:
    """
    Get the authenticated user's published articles.

    Args:
        page: Pagination page number
        per_page: Number of items to return
    """
    articles = await fetch_from_api(
        "/articles/me/published",
        params={"page": page, "per_page": per_page},
        require_auth=True,
    )
    return format_articles(articles[: min(per_page, 30)])


@mcp.tool()
async def get_my_unpublished_articles(page: int = 1, per_page: int = 30) -> str:
    """
    Get the authenticated user's unpublished articles.

    Args:
        page: Pagination page number
        per_page: Number of items to return
    """
    articles = await fetch_from_api(
        "/articles/me/unpublished",
        params={"page": page, "per_page": per_page},
        require_auth=True,
    )
    return format_articles(articles[: min(per_page, 30)])


@mcp.tool()
async def get_my_all_articles(page: int = 1, per_page: int = 30) -> str:
    """
    Get all of the authenticated user's articles, including drafts.

    Args:
        page: Pagination page number
        per_page: Number of items to return
    """
    articles = await fetch_from_api(
        "/articles/me/all",
        params={"page": page, "per_page": per_page},
        require_auth=True,
    )
    return format_articles(articles[: min(per_page, 30)])


@mcp.tool()
async def search_by_tag_combo(tags: str, page: int = 1, per_page: int = 30, top: int | None = None) -> str:
    """
    Return articles that match all requested tags.

    Args:
        tags: Comma-separated tag list, for example "swift,architecture"
        page: Pagination page number
        per_page: Number of items to return
        top: Optional popularity window in days
    """
    requested_tags = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
    if not requested_tags:
        return "Provide at least one tag."

    params = {"page": page, "per_page": per_page, "tags": ",".join(requested_tags), "top": top}
    filtered_params = {key: value for key, value in params.items() if value is not None}
    articles = await fetch_from_api("/articles", params=filtered_params)

    matching_articles = []
    for article in articles:
        article_tags = article.get("tag_list") or article.get("tags") or ""
        if isinstance(article_tags, list):
            normalized_tags = {tag.strip().lower() for tag in article_tags if tag}
        else:
            normalized_tags = {tag.strip().lower() for tag in str(article_tags).split(",") if tag.strip()}

        if all(tag in normalized_tags for tag in requested_tags):
            matching_articles.append(article)

    return format_articles(matching_articles[: min(per_page, 30)])

@mcp.tool()
async def get_user_info(username: str) -> str:
    """
    Get information about a Dev.to user
    
    Args:
        username: The username of the user
    """
    try:
        user = await fetch_from_api(f"/users/{username}", require_auth=True)
        return format_user_profile(user)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"User {username} not found."
        raise e

@mcp.tool()
async def create_article(title: str, body_markdown: str, tags: str = "", published: bool = False) -> str:
    """
    Create and publish a new article on Dev.to
    
    Args:
        title: The title of the article
        body_markdown: The content of the article in markdown format
        tags: Comma-separated list of tags (e.g., "python,tutorial,webdev")
        published: Whether to publish immediately (True) or save as draft (False)
    """
    article_data = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "published": published,
            "tags": tags
        }
    }
    
    article = await request_api("POST", "/articles", json=article_data, require_auth=True)
    return f"Article created successfully with ID: {article.get('id')}\nURL: {article.get('url')}"

@mcp.tool()
async def update_article(article_id: int, title: str = None, body_markdown: str = None, 
                        tags: str = None, published: bool = None) -> str:
    """
    Update an existing article on Dev.to
    
    Args:
        article_id: The ID of the article to update
        title: New title for the article (optional)
        body_markdown: New content in markdown format (optional)
        tags: New comma-separated list of tags (optional)
        published: Change publish status (optional)
    """
    # Prepare update data with only the fields that are provided
    update_data = {"article": {}}
    if title is not None:
        update_data["article"]["title"] = title
    if body_markdown is not None:
        update_data["article"]["body_markdown"] = body_markdown
    if tags is not None:
        update_data["article"]["tags"] = tags
    if published is not None:
        update_data["article"]["published"] = published
    
    updated_article = await request_api(
        "PUT",
        f"/articles/{article_id}",
        json=update_data,
        require_auth=True,
    )
    return f"Article updated successfully\nURL: {updated_article.get('url')}"


@mcp.tool()
async def unpublish_article(article_id: int, note: str | None = None) -> str:
    """
    Unpublish an article by ID.

    Note:
        This endpoint requires the API key user to have admin or moderator access.

    Args:
        article_id: The article ID to unpublish
        note: Optional moderation note
    """
    params = {"note": note} if note else None
    await request_api(
        "PUT",
        f"/articles/{article_id}/unpublish",
        params=params,
        require_auth=True,
    )
    return f"Article {article_id} unpublished successfully."


@mcp.tool()
async def get_article_comments(article_id: int) -> str:
    """
    Get the threaded comments for an article.

    Args:
        article_id: Numeric article ID
    """
    comments = await fetch_from_api("/comments", params={"a_id": article_id})
    return format_comments(comments)


@mcp.tool()
async def get_tags(page: int = 1, per_page: int = 10) -> str:
    """
    Get popular tags ordered by popularity.

    Args:
        page: Pagination page number
        per_page: Number of items to return
    """
    tags = await fetch_from_api("/tags", params={"page": page, "per_page": per_page})
    return format_tags(tags)


@mcp.tool()
async def get_listings(page: int = 1, per_page: int = 30, category: str | None = None) -> str:
    """
    Get published Dev.to listings.

    Note:
        Forem's API docs state that all legacy endpoints remain available in v1 when
        called with the v1 Accept header. This MCP uses the v1 header for all requests.

    Args:
        page: Pagination page number
        per_page: Number of items to return
        category: Optional listing category such as cfp, collabs, education, jobs,
            mentorship, products, or misc
    """
    params = {"page": page, "per_page": per_page, "category": category}
    filtered_params = {key: value for key, value in params.items() if value is not None}
    listings = await fetch_from_api("/listings", params=filtered_params)
    return format_listings(listings[: min(per_page, 30)])


@mcp.tool()
async def get_video_articles(page: int = 1, per_page: int = 24) -> str:
    """
    Get published Dev.to video articles for reading.

    Args:
        page: Pagination page number
        per_page: Number of items to return
    """
    videos = await fetch_from_api("/videos", params={"page": page, "per_page": per_page})
    return format_video_articles(videos[: min(per_page, 24)])


# Helper formatting functions

def format_articles(articles: list) -> str:
    """Format a list of articles for display"""
    if not articles:
        return "No articles found."
    
    result = "# Dev.to Articles\n\n"
    for article in articles:
        title = article.get("title", "Untitled")
        author = article.get("user", {}).get("name", "Unknown Author")
        published_date = article.get("readable_publish_date", "Unknown date")
        article_id = article.get("id", "")
        tags = article.get("tags", "")
        
        result += f"## {title}\n"
        result += f"ID: {article_id}\n"
        result += f"Author: {author}\n"
        result += f"Published: {published_date}\n"
        result += f"Tags: {tags}\n"
        result += f"Description: {article.get('description', 'No description available.')}\n\n"
    
    return result

def format_article_details(article: dict) -> str:
    """Format a single article with full details"""
    if not article:
        return "Article not found."
    
    title = article.get("title", "Untitled")
    author = article.get("user", {}).get("name", "Unknown Author")
    published_date = article.get("readable_publish_date", "Unknown date")
    body = article.get("body_markdown", "No content available.")
    tags = article.get("tags", "")
    
    result = f"# {title}\n\n"
    result += f"Author: {author}\n"
    result += f"Published: {published_date}\n"
    result += f"Tags: {tags}\n\n"
    result += "## Content\n\n"
    result += body
    
    return result

def format_user_profile(user: dict) -> str:
    """Format a user profile for display"""
    if not user:
        return "User not found."
    
    username = user.get("username", "Unknown")
    name = user.get("name", "Unknown")
    bio = user.get("summary", "No bio available.")
    twitter = user.get("twitter_username", "")
    github = user.get("github_username", "")
    website = user.get("website_url", "")
    location = user.get("location", "")
    joined = user.get("joined_at", "")
    
    result = f"# {name} (@{username})\n\n"
    result += f"Bio: {bio}\n\n"
    
    result += "## Details\n"
    if location:
        result += f"Location: {location}\n"
    if joined:
        result += f"Member since: {joined}\n"
    
    result += "\n## Links\n"
    if twitter:
        result += f"Twitter: @{twitter}\n"
    if github:
        result += f"GitHub: {github}\n"
    if website:
        result += f"Website: {website}\n"
    
    return result


def format_comments(comments: list) -> str:
    """Format article comments and threaded reply counts."""
    if not comments:
        return "No comments found."

    result = "# Dev.to Comments\n\n"
    for comment in comments[:20]:
        author = comment.get("user", {}).get("name", "Unknown Author")
        username = comment.get("user", {}).get("username", "unknown")
        created_at = comment.get("created_at", "Unknown date")
        body_html = comment.get("body_html", "")
        snippet = body_html.replace("<p>", "").replace("</p>", " ").replace("\n", " ").strip()
        children = comment.get("children", [])

        result += f"## {author} (@{username})\n"
        result += f"Posted: {created_at}\n"
        result += f"Replies: {len(children)}\n"
        result += f"Comment: {snippet[:280] or 'No comment body available.'}\n\n"

    return result


def format_tags(tags: list) -> str:
    """Format tag results."""
    if not tags:
        return "No tags found."

    result = "# Dev.to Tags\n\n"
    for tag in tags:
        result += f"- {tag.get('name', 'unknown')} (id: {tag.get('id', 'n/a')})\n"
    return result


def format_listings(listings: list) -> str:
    """Format listing results."""
    if not listings:
        return "No listings found."

    result = "# Dev.to Listings\n\n"
    for listing in listings:
        title = listing.get("title", "Untitled")
        category = listing.get("category", "unknown")
        listing_id = listing.get("id", "")
        author = listing.get("user", {}).get("name", "Unknown Author")
        tags = ", ".join(listing.get("tags", [])) if isinstance(listing.get("tags"), list) else listing.get("tag_list", "")

        result += f"## {title}\n"
        result += f"ID: {listing_id}\n"
        result += f"Category: {category}\n"
        result += f"Author: {author}\n"
        result += f"Tags: {tags}\n"
        result += f"URL: {listing.get('url', 'No URL available.')}\n\n"

    return result


def format_video_articles(videos: list) -> str:
    """Format video article results."""
    if not videos:
        return "No video articles found."

    result = "# Dev.to Video Articles\n\n"
    for video in videos:
        title = video.get("title", "Untitled")
        user = video.get("user") or {}
        author = user.get("name") or user.get("username") or "Unknown Author"
        video_id = video.get("id", "")
        path = video.get("path") or video.get("url") or "No URL available."
        duration = video.get("video_duration_in_minutes", "Unknown")
        source_url = video.get("video_source_url", "")
        published_at = video.get("published_at", "Unknown date")

        result += f"## {title}\n"
        result += f"ID: {video_id}\n"
        result += f"Author: {author}\n"
        result += f"Published: {published_at}\n"
        result += f"Duration (min): {duration}\n"
        result += f"Path: {path}\n"
        if source_url:
            result += f"Video Source: {source_url}\n"
        result += "\n"

    return result


if __name__ == "__main__":
    print("Starting Dev.to MCP server...")
    mcp.run() 
