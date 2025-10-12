from __future__ import annotations

import asyncio
import logging
import random
import re
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from typing import Any, Iterable, Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .matching import match_scraped_to_catalog
from .ml_matching import ml_match_scraped_to_catalog
from .models import Product, ScrapedProduct, ScrapingRun
from .settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


SHOPIFY_HINT_RE = re.compile(r"/products/|\.myshopify\.com|/collections/|shopify")


STORES: list[tuple[str, str]] = [
    ("Made Trade", "https://www.madetrade.com"),
    ("EarthHero", "https://earthhero.com"),
    ("GOODEE", "https://www.goodeeworld.com"),
    ("Package Free Shop", "https://packagefreeshop.com"),
    ("The Citizenry", "https://www.thecitizenry.com"),
    ("Ten Thousand Villages", "https://www.tenthousandvillages.com"),
    ("NOVICA", "https://www.novica.com"),
    ("The Little Market", "https://thelittlemarket.com"),
    ("DoneGood", "https://donegood.co"),
    ("Folksy", "https://folksy.com"),
    ("IndieCart", "https://indiecart.com"),
    ("Zero Waste Store", "https://zerowaste.store"),
    ("EcoRoots", "https://ecoroots.us"),
    ("Wild Minimalist", "https://wildminimalist.com"),
]


def psych_headers() -> dict[str, str]:
    uas = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/127.0",
    ]
    return {"User-Agent": random.choice(uas), "Accept-Language": "en-US,en;q=0.9"}


@dataclass
class RateLimiter:
    min_delay: float = 1.5
    _last: Optional[datetime] = None
    _lock: asyncio.Lock = asyncio.Lock()

    async def wait(self):
        async with self._lock:
            now = datetime.now(UTC)
            if self._last is None:
                self._last = now
                return
            elapsed = (now - self._last).total_seconds()
            delay = self.min_delay + random.uniform(0, 0.5)
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before next request")
                await asyncio.sleep(wait_time)
            self._last = datetime.now(UTC)





@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
async def fetch_text(client: httpx.AsyncClient, url: str) -> str:
    logger.debug(f"Fetching URL: {url}")
    r = await client.get(url, headers=psych_headers(), timeout=25)
    if r.status_code in (403, 429):
        logger.warning(f"Got {r.status_code} from {url}, will retry")
        # trigger retry
        r.raise_for_status()
    r.raise_for_status()
    logger.debug(f"Successfully fetched {url} ({len(r.text)} bytes)")
    return r.text


async def detect_shopify(client: httpx.AsyncClient, base_url: str) -> bool:
    try:
        html = await fetch_text(client, base_url)
        is_shopify = bool(SHOPIFY_HINT_RE.search(html) or SHOPIFY_HINT_RE.search(base_url))
        if is_shopify:
            logger.info(f"Detected Shopify store: {base_url}")
        return is_shopify
    except Exception as e:
        logger.debug(f"Failed to detect Shopify for {base_url}: {e}")
        return False


def is_relevant_to_search(product_title: str, search_term: str) -> bool:
    """Check if product title is relevant to the search term"""
    title_lower = product_title.lower()
    term_lower = search_term.lower()
    
    # Extract key words from search term (skip common words)
    stop_words = {"the", "a", "an", "and", "or", "with", "for", "of", "in"}
    term_words = {w for w in term_lower.split() if w not in stop_words and len(w) > 2}
    
    # If any key word from search term appears in title, it's potentially relevant
    if any(word in title_lower for word in term_words):
        return True
    
    # Check for category synonyms
    category_matches = {
        "sunglass": ["sunglass", "eyewear", "shades", "glasses"],
        "bottle": ["bottle", "flask", "thermos", "canteen"],
        "notebook": ["notebook", "journal", "diary"],
        "mug": ["mug", "cup"],
        "towel": ["towel"],
        "lunchbox": ["lunchbox", "lunch box", "bento"],
        "shawl": ["shawl", "stole", "scarf", "wrap"],
        "cushion": ["cushion", "pillow"],
        "phone stand": ["stand", "holder", "dock"],
    }
    
    for key, synonyms in category_matches.items():
        if key in term_lower:
            if any(syn in title_lower for syn in synonyms):
                return True
    
    return False


def expand_search_terms(term: str) -> list[str]:
    """Generate synonym variations to improve product discovery"""
    t = term.lower()
    terms = {t}
    
    # Enhanced synonym expansion patterns
    if "wooden" in t or "wood" in t:
        terms.update({t.replace("wooden", "wood"), t.replace("wooden", "bamboo"), t.replace("wood", "bamboo")})
    if "sunglass" in t:
        terms.update({t.replace("sunglasses", "shades"), t.replace("sunglass", "eyewear"), t.replace("sunglass", "glasses")})
    if "thermos" in t or "bottle" in t:
        terms.update({t.replace("thermos", "insulated"), t.replace("thermos", "bottle"), t + " flask", "water bottle", "insulated bottle"})
    if "mug" in t:
        terms.update({"coffee mug", "tea mug", "mug"})
    if "phone stand" in t:
        terms.update({t.replace("phone stand", "phone holder"), t.replace("phone stand", "mobile stand"), "mobile holder", "cell phone stand"})
    if "lunchbox" in t or "lunch box" in t:
        terms.update({"lunch box", "bento box", "lunchbox", "tiffin"})
    if "silk" in t and ("stole" in t or "shawl" in t):
        terms.update({t.replace("stole", "scarf"), t.replace("stole", "shawl"), t.replace("stole", "wrap")})
    if "shawl" in t or "scarf" in t:
        terms.update({t.replace("shawl", "scarf"), t.replace("scarf", "shawl"), t.replace("shawl", "stole"), t.replace("scarf", "wrap")})
    if "notebook" in t:
        terms.update({"journal", "notebook", "diary", "sketchbook"})
    if "cushion" in t:
        terms.update({t.replace("cushion", "pillow"), "cushion cover", "pillow cover", "pillowcase"})
    if "coaster" in t:
        terms.update({"coaster", "placemat", "table mat"})
    if "towel" in t:
        terms.update({"towel", "hand towel", "bath towel", "tea towel"})
    
    return list(terms)


async def scrape_shopify_predictive(client: httpx.AsyncClient, base_url: str, term: str) -> list[dict[str, Any]]:
    logger.info(f"Trying Shopify predictive search for '{term}' on {base_url}")
    # Try multiple endpoint patterns with proper parameter encoding
    from urllib.parse import quote_plus
    q = quote_plus(term)
    endpoints = [
        f"{base_url.rstrip('/')}/search/suggest.json?q={q}&resources[type]=product&resources[limit]=20",
        f"{base_url.rstrip('/')}/search/suggest.json?q={q}&resources[type]=product",
        f"{base_url.rstrip('/')}/search/suggestions?q={q}&resources[type]=product",
        f"{base_url.rstrip('/')}/search?q={q}&type=product",
        f"{base_url.rstrip('/')}/collections/all?q={q}",
        f"{base_url.rstrip('/')}/products.json?limit=20",  # Fallback to recent products
    ]
    for url in endpoints:
        with suppress(Exception):
            logger.debug(f"Trying Shopify endpoint: {url}")
            r = await client.get(url, headers=psych_headers(), timeout=20)
            if r.status_code != 200:
                logger.debug(f"Shopify endpoint returned {r.status_code}")
                continue
            data = r.json()
            # Shopify predictive can be under resources -> results -> products or under products[]
            candidates: list[dict[str, Any]] = []
            if isinstance(data, dict):
                # Newer format: resources.results.products
                if "resources" in data and isinstance(data["resources"], dict):
                    resources = data["resources"]
                    # Check for results sub-object
                    if "results" in resources and isinstance(resources["results"], dict):
                        results = resources["results"]
                        if "products" in results and isinstance(results["products"], list):
                            candidates.extend(results["products"])
                    # Direct products array in resources
                    if "products" in resources and isinstance(resources["products"], list):
                        candidates.extend(resources["products"])
                # Older format: direct products array
                if "products" in data and isinstance(data["products"], list):
                    candidates.extend(data["products"])
            results: list[dict[str, Any]] = []
            for it in candidates:
                # Heuristics for common fields
                title = it.get("title") or it.get("name")
                price = it.get("price") or it.get("price_min") or (it.get("variants", [{}])[0].get("price") if isinstance(it.get("variants"), list) else None)
                
                # Better URL extraction
                url_field = it.get("url") or it.get("url_with_domain") or it.get("handle")
                if url_field:
                    if url_field.startswith("http"):
                        url = url_field
                    elif url_field.startswith("/"):
                        url = base_url.rstrip("/") + url_field
                    else:
                        url = base_url.rstrip("/") + f"/products/{url_field}"
                else:
                    url = base_url
                
                currency = it.get("currency") or it.get("priceCurrency") or "USD"
                
                # IMPORTANT: Only add if relevant to search term
                if title and price and is_relevant_to_search(title, term):
                    try:
                        # Handle price as string or number, possibly in cents
                        price_val = float(price)
                        # If price seems too high (likely in cents), divide by 100
                        if price_val > 1000:
                            price_val = price_val / 100
                        results.append({
                            "title": title,
                            "price": price_val,
                            "currency": currency,
                            "product_url": url,
                        })
                    except Exception:
                        continue
            if results:
                logger.info(f"Shopify predictive search found {len(results)} products for '{term}' on {base_url}")
                # Log sample results for debugging
                if results:
                    logger.debug(f"Sample Shopify results: {[r['title'][:50] for r in results[:3]]}")
                return results
    logger.debug(f"Shopify predictive search found no results for '{term}' on {base_url}")
    return []


async def scrape_html_search(client: httpx.AsyncClient, base_url: str, term: str) -> list[dict[str, Any]]:
    logger.info(f"Scraping HTML search for '{term}' on {base_url}")
    # Prefer JSON-LD structured data
    from urllib.parse import quote_plus

    # Try multiple search URL patterns
    search_paths = [
        f"/search?q={quote_plus(term)}",
        f"/search?query={quote_plus(term)}",
        f"/search?s={quote_plus(term)}",
        f"/catalogsearch/result/?q={quote_plus(term)}",
        f"/collections/all?q={quote_plus(term)}",
    ]
    
    html = None
    used_path = None
    for path in search_paths:
        try:
            url = f"{base_url.rstrip('/')}{path}"
            html = await fetch_text(client, url)
            used_path = path
            break
        except Exception:
            continue
    
    if not html:
        logger.warning(f"Could not fetch search results for '{term}' on {base_url}")
        return []
    
    logger.debug(f"Using search path {used_path} for {base_url}")
    soup = BeautifulSoup(html, "lxml")
    results: list[dict[str, Any]] = []
    
    # Extract from JSON-LD structured data first (most reliable)
    # BUT filter to ensure products match the search term
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(tag.string or "{}")
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") in ("Product", "ItemList"):
            if data.get("@type") == "ItemList" and isinstance(data.get("itemListElement"), list):
                for it in data["itemListElement"]:
                    it = it.get("item") if isinstance(it, dict) else it
                    if not isinstance(it, dict):
                        continue
                    name = it.get("name") or it.get("title")
                    offer = it.get("offers") or {}
                    price = (offer or {}).get("price")
                    currency = (offer or {}).get("priceCurrency") or "USD"
                    url = it.get("url") or base_url
                    
                    # IMPORTANT: Filter out products not relevant to search term
                    if name and price and is_relevant_to_search(name, term):
                        with suppress(Exception):
                            results.append({
                                "title": name,
                                "price": float(price),
                                "currency": currency,
                                "product_url": url if url.startswith("http") else f"{base_url.rstrip('/')}{url}",
                            })
            elif data.get("@type") == "Product":
                name = data.get("name")
                offer = data.get("offers") or {}
                price = (offer or {}).get("price")
                currency = (offer or {}).get("priceCurrency") or "USD"
                url = data.get("url") or base_url
                
                # IMPORTANT: Filter out products not relevant to search term
                if name and price and is_relevant_to_search(name, term):
                    with suppress(Exception):
                        results.append({
                            "title": name,
                            "price": float(price),
                            "currency": currency,
                            "product_url": url if url.startswith("http") else f"{base_url.rstrip('/')}{url}",
                        })
    
    # If JSON-LD didn't yield enough results, extract product URLs and parse individual pages
    if len(results) < 5:
        product_urls = set()
        url_patterns = [
            r'href=["\']([^"\']*/(products?|items?|product|item|shop)/[^"\']*)["\']',
            r'href=["\']([^"\']*/collections/[^"\']*/products/[^"\']*)["\']',
            r'<a[^>]*href=["\']([^"\']*/(product|item)[^"\']*)["\']',
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                u = match if isinstance(match, str) else match[0]
                if u.startswith('/'):
                    full = f"{base_url.rstrip('/')}{u}"
                elif u.startswith('http'):
                    full = u
                else:
                    continue
                
                # Skip non-product URLs
                low = full.lower()
                if any(skip in low for skip in ['cart', 'account', 'login', 'checkout', 'blog', 'about', 'contact', 'policy', 'terms', 'privacy']):
                    continue
                if any(ext in low for ext in ['.jpg', '.png', '.gif', '.svg', '.css', '.js', '.pdf', '.ico']):
                    continue
                
                product_urls.add(full)
        
        logger.debug(f"Extracted {len(product_urls)} product URLs from HTML for potential scraping")
    
    # Try parsing prices directly from search results HTML
    if len(results) < 3:
        price_patterns = [
            r'€\s*([\d\.,]+)',
            r'£\s*([\d\.,]+)',
            r'\$\s*([\d\.,]+)',
            r'₹\s*([\d\.,]+)',
            r'INR\s*([\d\.,]+)',
            r'Rs\.?\s*([\d\.,]+)',
            r'USD\s*([\d\.,]+)',
            r'EUR\s*([\d\.,]+)',
            r'GBP\s*([\d\.,]+)',
        ]
        
        # Look for product cards/items in HTML
        product_cards = soup.select('.product-card, .product-item, .product, [data-product], .grid-product, .product-grid-item')
        
        for card in product_cards[:20]:  # Limit to first 20 cards
            title_elem = card.select_one('h2, h3, .product-title, .product-name, [itemprop="name"]')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            card_html = str(card)
            
            # Try to extract price from card
            price_val = None
            for pattern in price_patterns:
                match = re.search(pattern, card_html, re.IGNORECASE)
                if match:
                    try:
                        price_text = match.group(1).replace(',', '').strip()
                        price_val = float(price_text)
                        break
                    except Exception:
                        continue
            
            # Extract URL
            link_elem = card.select_one('a[href]')
            product_url = base_url
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('http'):
                    product_url = href
                elif href.startswith('/'):
                    product_url = f"{base_url.rstrip('/')}{href}"
            
            # IMPORTANT: Only add if relevant to search term
            if title and price_val and price_val > 0 and is_relevant_to_search(title, term):
                results.append({
                    "title": title,
                    "price": price_val,
                    "currency": "USD",  # Default, could be refined
                    "product_url": product_url,
                })
    
    logger.info(f"HTML search found {len(results)} products for '{term}' on {base_url}")
    # Log sample results for debugging
    if results:
        logger.debug(f"Sample HTML results for '{term}': {[r['title'][:50] for r in results[:3]]}")
    return results


async def scrape_store_search(client: httpx.AsyncClient, base_url: str, term: str) -> list[dict[str, Any]]:
    # Detect Shopify and try predictive first
    if await detect_shopify(client, base_url):
        res = await scrape_shopify_predictive(client, base_url, term)
        if res:
            return res
    # Fallback to HTML search + JSON-LD parser
    return await scrape_html_search(client, base_url, term)


async def run_scraping_run(run_id: str, target_products: list[str], stores: Optional[list[str]] = None) -> None:
    logger.info(f"Starting scraping run {run_id} for {len(target_products)} products: {target_products}")
    
    # Validate we have target products
    if not target_products:
        logger.error(f"No target products provided for run {run_id}. Aborting.")
        async with get_session() as s:
            run = (await s.execute(select(ScrapingRun).where(ScrapingRun.id == run_id))).scalar_one()
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            run.errors = [{"error": "No target products provided"}]
            await s.commit()
        return
    
    limiter_by_store: dict[str, RateLimiter] = {}
    async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
        # load catalog for matching
        async with get_session() as s:
            rows = (await s.execute(select(Product.id, Product.name, Product.brand, Product.category))).all()
            catalog = [(pid, name, brand, category) for pid, name, brand, category in rows]
        logger.info(f"Loaded {len(catalog)} catalog products for matching")

        to_scrape = [(name, url) for name, url in STORES if (not stores or name in stores)]
        stores_total = len(to_scrape)
        logger.info(f"Will scrape {stores_total} stores: {[name for name, _ in to_scrape]}")
        
        # update run stores_total
        async with get_session() as s:
            run = (await s.execute(select(ScrapingRun).where(ScrapingRun.id == run_id))).scalar_one()
            run.stores_total = stores_total
            await s.commit()

        async def scrape_one_store(store_name: str, base_url: str):
            logger.info(f"[{store_name}] Starting scrape")
            limiter = limiter_by_store.setdefault(store_name, RateLimiter())
            products_found_local = 0
            errors_local: list[dict[str, Any]] = []
            try:
                for idx, term in enumerate(target_products, 1):
                    logger.info(f"[{store_name}] Searching for '{term}' ({idx}/{len(target_products)})")
                    
                    # Try original term and expansions - try more variations for better coverage
                    search_terms = expand_search_terms(term)
                    all_results = []
                    seen_urls = set()  # Deduplicate by URL within this term
                    
                    for search_idx, search_term in enumerate(search_terms[:5], 1):  # Try up to 5 variations
                        await limiter.wait()
                        try:
                            logger.debug(f"[{store_name}] Trying variation '{search_term}' ({search_idx}/{min(5, len(search_terms))})")
                            results = await scrape_store_search(client, base_url, search_term)
                            if results:
                                logger.info(f"[{store_name}] Found {len(results)} results for '{search_term}'")
                                # Deduplicate by URL
                                for r in results:
                                    url = r.get("product_url", "")
                                    if url and url not in seen_urls:
                                        seen_urls.add(url)
                                        all_results.append(r)
                                # Continue to next variation to get more diverse results
                                if len(all_results) >= 15:  # Stop if we have enough
                                    break
                        except Exception as e:
                            logger.debug(f"[{store_name}] Error with term '{search_term}': {str(e)}")
                            continue
                    
                    if not all_results:
                        logger.warning(f"[{store_name}] No results for any variation of '{term}'")
                        errors_local.append({"store": store_name, "term": term, "error": "No results found"})
                        continue
                    
                    results = all_results
                    # Filter out test/demo products and persist
                    async with get_session() as s:
                        matched_count = 0
                        saved_count = 0
                        
                        for item in results[:20]:  # cap per term per store to avoid floods
                            title = item.get("title") or ""
                            
                            # Skip obvious test/demo products
                            title_lower = title.lower()
                            if any(x in title_lower for x in ["test", "sample", "demo", "lorem", "ipsum", "dummy", "placeholder", "coming soon"]):
                                logger.debug(f"[{store_name}] Skipping test/demo product: {title}")
                                continue
                            
                            # Must have a price
                            if not item.get("price"):
                                logger.debug(f"[{store_name}] Skipping product without price: {title}")
                                continue
                            
                            # Double-check relevance (in case scraper didn't filter properly)
                            if not is_relevant_to_search(title, term):
                                logger.debug(f"[{store_name}] Skipping irrelevant product for '{term}': {title}")
                                continue
                            
                            # Check settings for ML matching preference
                            from .settings import get_settings
                            settings = get_settings()
                            
                            if settings.USE_ML_MATCHING:
                                # Use ML matching for better accuracy
                                try:
                                    mr = await ml_match_scraped_to_catalog(title, None, catalog)
                                    # Convert MLMatchResult to MatchResult format for compatibility
                                    from .matching import MatchResult
                                    match_result = MatchResult(
                                        product_id=mr.product_id,
                                        score=mr.score,
                                        reason=mr.reason
                                    )
                                    threshold = 0.40  # ML threshold
                                except Exception as e:
                                    logger.warning(f"[{store_name}] ML matching failed for '{title}', using fallback: {e}")
                                    # Fallback to original matching
                                    match_result = match_scraped_to_catalog(title, None, catalog)
                                    threshold = 0.35  # Token matching threshold
                            else:
                                # Use traditional token-based matching
                                match_result = match_scraped_to_catalog(title, None, catalog)
                                threshold = 0.35  # Token matching threshold
                            
                            if match_result.product_id and match_result.score >= threshold:
                                matched_count += 1
                                method = "ML" if settings.USE_ML_MATCHING else "Token"
                                logger.debug(f"[{store_name}] {method} matched '{title}' to catalog product {match_result.product_id} (score: {match_result.score:.3f})")
                            else:
                                logger.debug(f"[{store_name}] No match for '{title}' (best score: {match_result.score:.3f})")
                            
                            sp = ScrapedProduct(
                                run_id=run_id,
                                store_name=store_name,
                                product_url=item.get("product_url") or base_url,
                                product_id=None,
                                title=item.get("title") or "",
                                price=float(item.get("price") or 0),
                                currency=item.get("currency") or "USD",
                                brand=None,
                                material=None,
                                size=None,
                                search_term=term,
                                matched_catalog_id=match_result.product_id,
                                similarity_score=match_result.score,
                                match_reason=match_result.reason,
                            )
                            s.add(sp)
                            saved_count += 1
                        
                        # update counters for this batch
                        products_found_local += saved_count
                        method = "ML" if get_settings().USE_ML_MATCHING else "Token"
                        logger.info(f"[{store_name}] Saved {saved_count}/{len(results[:20])} products for '{term}' ({matched_count} matched to catalog, {method} matching)")
                        
                        run = (await s.execute(select(ScrapingRun).where(ScrapingRun.id == run_id))).scalar_one()
                        run.products_found += saved_count
                        if errors_local:
                            run.errors.extend(errors_local)
                            errors_local.clear()
                        await s.commit()
            finally:
                # mark store done
                logger.info(f"[{store_name}] Completed scraping. Found {products_found_local} total products with {len(errors_local)} errors")
                async with get_session() as s:
                    run = (await s.execute(select(ScrapingRun).where(ScrapingRun.id == run_id))).scalar_one()
                    run.stores_completed += 1
                    logger.info(f"Progress: {run.stores_completed}/{run.stores_total} stores completed, {run.products_found} total products found")
                    if run.stores_completed >= run.stores_total:
                        run.status = "completed"
                        run.completed_at = datetime.now(UTC)
                        logger.info(f"Scraping run {run_id} completed successfully!")
                    await s.commit()

        # run with limited concurrency
        sem = asyncio.Semaphore(3)

        async def worker(name: str, url: str):
            async with sem:
                try:
                    await scrape_one_store(name, url)
                except Exception as e:
                    logger.error(f"[{name}] Fatal error during scraping: {str(e)}", exc_info=True)
                    # Mark store as completed even on error to avoid hanging
                    async with get_session() as s:
                        run = (await s.execute(select(ScrapingRun).where(ScrapingRun.id == run_id))).scalar_one()
                        run.stores_completed += 1
                        run.errors.append({"store": name, "error": f"Fatal error: {str(e)}"})
                        if run.stores_completed >= run.stores_total:
                            run.status = "completed"
                            run.completed_at = datetime.now(UTC)
                        await s.commit()

        logger.info(f"Starting concurrent scraping with max 3 parallel stores")
        await asyncio.gather(*[worker(n, u) for n, u in to_scrape])
        logger.info(f"Scraping run {run_id} finished")

