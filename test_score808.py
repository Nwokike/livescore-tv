import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from services.score808 import Score808Scraper

async def manual_test():
    scraper = Score808Scraper()

    # Step 1: Go to homepage, see what's there
    print("=" * 60)
    print("STEP 1: Fetch score808.tv homepage")
    print("=" * 60)
    client = scraper._get_client()
    resp = await client.get("https://score808.tv")
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('content-type', 'unknown')}")
    print(f"Content length: {len(resp.text)}")

    # Save HTML for inspection
    with open("homepage.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved homepage.html")

    # Step 2: Parse homepage - what links are available?
    print("\n" + "=" * 60)
    print("STEP 2: Parse homepage links")
    print("=" * 60)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "lxml")

    # Find all match links
    match_links = []
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        if text and len(text) > 3:
            match_links.append({"href": href, "text": text})

    print(f"Found {len(match_links)} links with text")
    for i, m in enumerate(match_links[:20]):
        print(f"  [{i}] {m['text'][:60]} -> {m['href']}")

    # Step 3: Pick a match and follow it
    print("\n" + "=" * 60)
    print("STEP 3: Follow a match link")
    print("=" * 60)

    # Try to find a real match link (not /livestream.html)
    target = None
    for m in match_links:
        href = m["href"]
        text = m["text"]
        if href != "/livestream.html" and "livestream" not in href and "contact" not in href and "about" not in href:
            target = m
            break

    if not target:
        print("No specific match link found, trying /2026worldcup.html")
        target = {"href": "/2026worldcup.html", "text": "World Cup"}

    match_url = f"https://score808.tv{target['href']}" if target['href'].startswith("/") else target['href']
    print(f"Following: {target['text'][:50]} -> {match_url}")

    resp2 = await client.get(match_url)
    print(f"Status: {resp2.status_code}")
    print(f"Content length: {len(resp2.text)}")

    with open("match_page.html", "w", encoding="utf-8") as f:
        f.write(resp2.text)
    print("Saved match_page.html")

    # Step 4: Parse match page for streams
    print("\n" + "=" * 60)
    print("STEP 4: Parse match page for stream links")
    print("=" * 60)
    soup2 = BeautifulSoup(resp2.text, "lxml")

    # Find all links
    links = soup2.find_all("a", href=True)
    print(f"Found {len(links)} links on match page")
    for i, link in enumerate(links):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        print(f"  [{i}] text='{text[:40]}' href='{href}'")

    # Find iframes
    iframes = soup2.find_all("iframe", src=True)
    print(f"\nFound {len(iframes)} iframes")
    for i, iframe in enumerate(iframes):
        src = iframe.get("src", "")
        title = iframe.get("title", "")
        print(f"  [{i}] title='{title}' src='{src}'")

    # Step 5: Try to find actual stream URLs in the HTML
    print("\n" + "=" * 60)
    print("STEP 5: Search for stream URLs in HTML")
    print("=" * 60)
    import re

    # Look for m3u8
    m3u8_urls = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', resp2.text)
    print(f"Found {len(m3u8_urls)} m3u8 URLs:")
    for u in m3u8_urls[:10]:
        print(f"  {u}")

    # Look for iframe/embed URLs
    embed_urls = re.findall(r'https?://[^\s"\'<>]+embed[^\s"\'<>]*', resp2.text)
    print(f"\nFound {len(embed_urls)} embed URLs:")
    for u in embed_urls[:10]:
        print(f"  {u}")

    # Look for any video/stream URLs
    video_urls = re.findall(r'https?://[^\s"\'<>]+(?:stream|play|watch|video|m3u8|mp4)[^\s"\'<>]*', resp2.text)
    print(f"\nFound {len(video_urls)} video/stream URLs:")
    for u in video_urls[:10]:
        print(f"  {u}")

    # Step 6: Try the scraper methods
    print("\n" + "=" * 60)
    print("STEP 6: Test scraper methods end-to-end")
    print("=" * 60)

    # Try find_match_page_by_id with a known ID
    channels = await scraper.get_streams_from_match_page(match_url)
    print(f"\nget_streams_from_match_page found {len(channels)} channels:")
    for i, ch in enumerate(channels):
        print(f"  [{i}] name='{ch.name}' quality='{ch.quality}' url='{ch.url}'")

    if channels:
        ch = channels[0]
        print(f"\nResolving: {ch.url}")
        resolved = await scraper.resolve_stream_url(ch.url)
        print(f"Resolved: {resolved}")

    await scraper.close()

    print("\n" + "=" * 60)
    print("MANUAL TEST COMPLETE")
    print("=" * 60)

asyncio.run(manual_test())
