import asyncio
import os
import types
import uuid

import pytest
from sqlalchemy import select

from api.db import init_db, get_session
from api import models
from api.scraping import run_scraping_run, scrape_store_search


pytestmark = pytest.mark.asyncio


async def setup_catalog():
    # Ensure tables
    await init_db(models)
    async with get_session() as s:
        # Clear tables for isolation (sqlite ok)
        for tbl in [models.ScrapedProduct, models.ScrapingRun, models.PriceRecommendation, models.Product]:
            await s.execute(models.Product.__table__.delete() if tbl is models.Product else tbl.__table__.delete())
        await s.commit()
        # Seed one product
        p = models.Product(
            id="SKU-1",
            name="Eco Bottle 500ml",
            category="bottle",
            brand="Acme",
            unit_cost=5.0,
            current_price=10.0,
            currency="USD",
        )
        s.add(p)
        await s.commit()


@pytest.fixture(autouse=True)
async def _setup_db():
    # Use sqlite fallback for tests
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_priceoptim.db"
    await setup_catalog()
    yield


@pytest.fixture(autouse=True)
def patch_scraper(monkeypatch):
    async def fake_scrape_store_search(client, base_url, term):
        return [
            {
                "title": f"Eco Bottle 500ml - {term}",
                "price": 9.99,
                "currency": "USD",
                "product_url": f"{base_url}/products/fake-{term}",
            }
        ]

    monkeypatch.setattr("api.scraping.scrape_store_search", fake_scrape_store_search)
    yield


async def test_run_scraping_creates_results():
    # create run
    async with get_session() as s:
        run = models.ScrapingRun(status="running", target_products=["bottle"], stores_total=0, stores_completed=0)
        s.add(run)
        await s.flush()
        run_id = run.id
        await s.commit()

    # execute scraper (monkeypatched to avoid network)
    await run_scraping_run(run_id, targets=["bottle"], stores=["Made Trade"])  # limit to one store for test

    # verify
    async with get_session() as s:
        r = (await s.execute(select(models.ScrapingRun).where(models.ScrapingRun.id == run_id))).scalar_one()
        assert r.status == "completed"
        assert r.products_found >= 1
        items = (await s.execute(select(models.ScrapedProduct).where(models.ScrapedProduct.run_id == run_id))).scalars().all()
        assert len(items) >= 1
        assert items[0].title.startswith("Eco Bottle 500ml")