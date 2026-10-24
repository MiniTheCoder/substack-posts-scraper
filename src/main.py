import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from apify import Actor

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

def normalize_substack_url(input_str: str) -> str:
    s = input_str.strip()
    if not s:
        return ""
    if not s.startswith('http://') and not s.startswith('https://'):
        if '.' in s:
            s = f"https://{s}"
        else:
            s = f"https://{s}.substack.com"
            
    parsed = urlparse(s)
    if parsed.netloc.endswith('substack.com') and parsed.path.startswith('/@'):
        handle = parsed.path.lstrip('/@').split('/')[0]
        return f"https://{handle}.substack.com"
        
    return f"{parsed.scheme}://{parsed.netloc}"

def parse_post(item: Dict[str, Any], pub_origin: str) -> Dict[str, Any]:
    bylines = item.get("publishedBylines") or []
    primary_author = bylines[0] if bylines else {}
    
    audience = item.get("audience") or "everyone"
    is_paid = (audience == "only_paid")
    
    return {
        "id": item.get("id"),
        "title": item.get("title") or "",
        "subtitle": item.get("subtitle") or "",
        "url": item.get("canonical_url") or "",
        "slug": item.get("slug") or "",
        "postDate": item.get("post_date") or "",
        "audience": audience,
        "isPaid": is_paid,
        "reactions": item.get("reaction_count") or 0,
        "comments": item.get("comment_count") or 0,
        "restacks": item.get("restacks") or 0,
        "wordCount": item.get("wordcount") or 0,
        "description": item.get("description") or "",
        "coverImageUrl": item.get("cover_image") or None,
        "type": item.get("type") or "newsletter",
        "podcastUrl": item.get("podcast_url") or None,
        "podcastDuration": item.get("podcast_duration") or None,
        "publicationId": item.get("publication_id"),
        "publicationUrl": pub_origin,
        "authorName": primary_author.get("name") or None,
        "authorHandle": primary_author.get("handle") or None,
        "authorBio": primary_author.get("bio") or None,
        "authorPhotoUrl": primary_author.get("photo_url") or None,
        "authorPublicationUrl": primary_author.get("primaryPublicationUrl") or None,
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
    }

async def scrape_publication(
    client: httpx.AsyncClient,
    pub_input: str,
    max_posts: int,
    sort: str,
    audience_filter: str,
) -> List[Dict[str, Any]]:
    pub_origin = normalize_substack_url(pub_input)
    if not pub_origin:
        return []
    
    Actor.log.info(f"Scraping publication: {pub_origin} (target: up to {max_posts} posts, sort: {sort})")
    
    collected: List[Dict[str, Any]] = []
    offset = 0
    batch_size = 50
    
    while len(collected) < max_posts:
        limit = min(batch_size, max_posts - len(collected))
        api_url = f"{pub_origin}/api/v1/posts?sort={sort}&limit={limit}&offset={offset}"
        
        try:
            resp = await client.get(api_url, timeout=12.0)
            if resp.status_code == 404:
                Actor.log.warning(f"Publication not found or has no public API: {pub_origin} (HTTP 404)")
                break
            if resp.status_code != 200:
                Actor.log.warning(f"Failed to fetch posts from {pub_origin}: HTTP {resp.status_code}")
                break
                
            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                Actor.log.info(f"Reached end of posts for {pub_origin} at offset {offset}")
                break
                
            for item in data:
                parsed = parse_post(item, pub_origin)
                
                # Apply audience filter if specified
                if audience_filter == "free_only" and parsed["isPaid"]:
                    continue
                if audience_filter == "paid_only" and not parsed["isPaid"]:
                    continue
                    
                collected.append(parsed)
                if len(collected) >= max_posts:
                    break
                    
            offset += len(data)
            
            # If fewer items than requested were returned, we hit the end
            if len(data) < limit:
                break
                
        except Exception as e:
            Actor.log.error(f"Error scraping {pub_origin} at offset {offset}: {e}")
            break
            
    Actor.log.info(f"Finished {pub_origin}: extracted {len(collected)} posts")
    return collected

async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        
        raw_pubs = actor_input.get("publications") or ["lenny", "pragmaticengineer"]
        if isinstance(raw_pubs, str):
            raw_pubs = [p.strip() for p in raw_pubs.split("\n") if p.strip()]
            
        max_posts = int(actor_input.get("maxPostsPerPublication", 30))
        sort = actor_input.get("sort", "new")
        if sort not in ["new", "top", "search"]:
            sort = "new"
            
        audience_filter = actor_input.get("audienceFilter", "all")
        if audience_filter not in ["all", "free_only", "paid_only"]:
            audience_filter = "all"
            
        Actor.log.info(f"Starting Substack Scraper for {len(raw_pubs)} publications...")
        
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
        async with httpx.AsyncClient(headers=HEADERS, limits=limits, follow_redirects=True) as client:
            tasks = [
                scrape_publication(client, pub, max_posts, sort, audience_filter)
                for pub in raw_pubs
            ]
            results_nested = await asyncio.gather(*tasks)
            
        all_results = [item for sublist in results_nested for item in sublist]
        
        if all_results:
            await Actor.push_data(all_results)
            Actor.log.info(f"Successfully saved {len(all_results)} total posts to dataset.")
        else:
            Actor.log.warning("No posts extracted matching the input criteria.")

if __name__ == "__main__":
    asyncio.run(main())
