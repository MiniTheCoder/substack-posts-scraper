# Substack Newsletter & Author Leads Scraper

[![Run on Apify](https://apify.com/actor-badge?actor=fastdata_lab/substack-posts-scraper)](https://apify.com/fastdata_lab/substack-posts-scraper)

Extracts newsletter post archives, author bylines, engagement metrics, and podcast episodes from any Substack publication without running a headless browser.

[**Run directly on Apify Store**](https://apify.com/fastdata_lab/substack-posts-scraper) — zero setup required.

## What it does

This Actor queries Substack's public API endpoints (`/api/v1/posts`) for one or more target publications. It retrieves post archives, author profiles, word counts, reaction/comment numbers, and direct audio files for podcast episodes.

Because it connects directly via HTTP streams rather than spinning up a browser automation engine (Puppeteer or Playwright), runs finish in 2–5 seconds and consume minimal compute resources.

## Extracted data fields

For every post retrieved, the actor outputs:

- `id`: Unique numeric post identifier
- `title`: Post headline
- `subtitle`: Subtitle / deck
- `url`: Canonical post URL
- `slug`: URL slug
- `postDate`: ISO publication timestamp
- `audience`: Access level (`everyone` or `only_paid`)
- `isPaid`: Boolean flag (true if subscriber paywalled)
- `reactions`: Like / reaction count
- `comments`: Total comment count
- `restacks`: Total restacks / shares
- `wordCount`: Total word count
- `description`: Excerpt or meta description
- `coverImageUrl`: Banner or header image URL
- `type`: Content format (`newsletter`, `podcast`, etc.)
- `podcastUrl`: Direct audio file URL (if an episode)
- `podcastDuration`: Audio duration in seconds
- `publicationId`: Numeric publication ID
- `publicationUrl`: Base publication URL
- `authorName`: Primary author display name
- `authorHandle`: Substack profile handle
- `authorBio`: Author biography
- `authorPhotoUrl`: Author avatar image URL
- `authorPublicationUrl`: Author's primary personal publication URL
- `scrapedAt`: ISO extraction timestamp

## Input parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `publications` | array | `["lenny", "pragmaticengineer"]` | List of Substack subdomains (`lenny`), full URLs (`https://newsletter.pragmaticengineer.com`), or custom domains (`sinocism.com`) |
| `maxPostsPerPublication` | integer | `30` | Maximum number of posts to retrieve per publication |
| `sort` | string | `"new"` | Sort order: `new` (newest first), `top` (most popular), or `search` |
| `audienceFilter` | string | `"all"` | Filter by access level: `all`, `free_only`, or `paid_only` |

## Example output

```json
{
  "id": 219482066,
  "title": "How to tell if a startup has a moat",
  "subtitle": "A framework for assessing whether the company you're considering joining is built to last",
  "url": "https://www.lennysnewsletter.com/p/how-to-tell-if-a-startup-has-a-moat",
  "slug": "how-to-tell-if-a-startup-has-a-moat",
  "postDate": "2026-10-13T12:45:41.160Z",
  "audience": "only_paid",
  "isPaid": true,
  "reactions": 360,
  "comments": 2,
  "restacks": 20,
  "wordCount": 4153,
  "description": "A framework for assessing whether the company you're considering joining is built to last",
  "coverImageUrl": "https://substackcdn.com/image/fetch/.../fb5a8d5c-1e31-45f5-b9f8-93426e87a971_1456x970.png",
  "type": "newsletter",
  "podcastUrl": null,
  "podcastDuration": null,
  "publicationId": 10845,
  "publicationUrl": "https://lenny.substack.com",
  "authorName": "Dan Hockenmaier",
  "authorHandle": "danhock",
  "authorBio": "Strategy, growth, and marketplaces. Always trying to separate signal from noise.",
  "authorPhotoUrl": "https://substackcdn.com/image/fetch/.../7e1bdeea-74f6-48f7-8d3f-d42dc03bbc08_1080x1080.png",
  "authorPublicationUrl": "https://www.danhock.co",
  "scrapedAt": "2026-10-24T13:05:13.937987+00:00"
}
```

## Limitations

- Only extracts posts published publicly on publication web feeds.
- Private subscriber-only body text behind paywalls is not extracted; paywalled posts contain post metadata, word counts, and excerpts.
