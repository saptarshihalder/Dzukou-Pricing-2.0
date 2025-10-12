"""Sample data seeder for testing the Price Optimizer AI system."""

from datetime import datetime, UTC
import asyncio
from sqlalchemy import select
from api.db import get_session, init_db
from api.models import Product, ScrapingRun, ScrapedProduct


async def seed_sample_data():
    """Seed the database with sample products and scraping data for testing."""
    
    # Initialize database first
    from api import models
    await init_db(models)
    
    async with get_session() as session:
        # Check if we already have products
        existing_products = await session.execute(select(Product).limit(1))
        if existing_products.scalar_one_or_none():
            print("Sample data already exists, skipping seeding.")
            return
        
        # Create sample products
        sample_products = [
            Product(
                id="ECO-SUN-001",
                name="Bamboo Sunglasses Classic",
                category="Sunglasses",
                brand="EcoVision",
                unit_cost=45.00,
                current_price=89.99,
                currency="EUR"
            ),
            Product(
                id="ECO-BOT-002",
                name="Recycled Steel Water Bottle",
                category="Bottles",
                brand="HydroGreen",
                unit_cost=12.50,
                current_price=24.99,
                currency="EUR"
            ),
            Product(
                id="ECO-NOTE-003",
                name="Cork Notebook Set",
                category="Notebooks",
                brand="NaturePaper",
                unit_cost=8.00,
                current_price=19.99,
                currency="EUR"
            ),
            Product(
                id="ECO-BAG-004",
                name="Organic Cotton Tote Bag",
                category="Bags",
                brand="EcoCarry",
                unit_cost=7.50,
                current_price=15.99,
                currency="EUR"
            ),
            Product(
                id="ECO-CUP-005",
                name="Bamboo Coffee Cup",
                category="Drinkware",
                brand="EcoSip",
                unit_cost=6.00,
                current_price=18.99,
                currency="EUR"
            ),
            Product(
                id="ECO-SHIRT-006",
                name="Organic Cotton T-Shirt",
                category="Apparel",
                brand="GreenThread",
                unit_cost=15.00,
                current_price=29.99,
                currency="EUR"
            )
        ]
        
        for product in sample_products:
            session.add(product)
        
        # Create a sample completed scraping run
        scraping_run = ScrapingRun(
            id="sample_run_001",
            status="completed",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            target_products=["sunglasses", "water bottle", "notebook", "tote bag", "coffee cup"],
            stores_total=5,
            stores_completed=5,
            products_found=25,
            errors=[]
        )
        session.add(scraping_run)
        
        # Create sample scraped products with competitor pricing
        sample_scraped_data = [
            # Sunglasses competitors
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="Made Trade",
                product_url="https://www.madetrade.com/products/bamboo-sunglasses",
                title="Bamboo Sunglasses - Classic Frame",
                price=95.00,
                currency="EUR",
                brand="EcoVision",
                search_term="sunglasses",
                matched_catalog_id="ECO-SUN-001",
                similarity_score=0.85,
                match_reason="title overlap=0.75, brand match +0.10"
            ),
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="EarthHero",
                product_url="https://earthhero.com/products/eco-sunglasses",
                title="Sustainable Bamboo Sunglasses",
                price=78.50,
                currency="EUR",
                search_term="sunglasses",
                matched_catalog_id="ECO-SUN-001",
                similarity_score=0.72,
                match_reason="title overlap=0.72"
            ),
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="GOODEE",
                product_url="https://www.goodeeworld.com/products/designer-sunglasses",
                title="Designer Eco Sunglasses",
                price=125.00,
                currency="EUR",
                search_term="sunglasses",
                matched_catalog_id="ECO-SUN-001",
                similarity_score=0.68,
                match_reason="title overlap=0.68"
            ),
            
            # Water bottle competitors
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="Made Trade",
                product_url="https://www.madetrade.com/products/steel-bottle",
                title="Recycled Steel Water Bottle 500ml",
                price=28.99,
                currency="EUR",
                brand="HydroGreen",
                search_term="water bottle",
                matched_catalog_id="ECO-BOT-002",
                similarity_score=0.88,
                match_reason="title overlap=0.78, brand match +0.10"
            ),
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="Package Free Shop",
                product_url="https://packagefreeshop.com/products/steel-bottle",
                title="Stainless Steel Water Bottle",
                price=32.50,
                currency="EUR",
                search_term="water bottle",
                matched_catalog_id="ECO-BOT-002",
                similarity_score=0.75,
                match_reason="title overlap=0.75"
            ),
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="EcoRoots",
                product_url="https://ecoroots.us/products/water-bottle",
                title="Eco-Friendly Steel Bottle",
                price=26.00,
                currency="EUR",
                search_term="water bottle",
                matched_catalog_id="ECO-BOT-002",
                similarity_score=0.71,
                match_reason="title overlap=0.71"
            ),
            
            # Notebook competitors
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="GOODEE",
                product_url="https://www.goodeeworld.com/products/cork-notebook",
                title="Cork Notebook A5 Lined",
                price=24.50,
                currency="EUR",
                brand="NaturePaper",
                search_term="notebook",
                matched_catalog_id="ECO-NOTE-003",
                similarity_score=0.83,
                match_reason="title overlap=0.73, brand match +0.10"
            ),
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="Wild Minimalist",
                product_url="https://wildminimalist.com/products/sustainable-notebook",
                title="Sustainable Cork Journal",
                price=22.99,
                currency="EUR",
                search_term="notebook",
                matched_catalog_id="ECO-NOTE-003",
                similarity_score=0.69,
                match_reason="title overlap=0.69"
            ),
            
            # Tote bag competitors
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="The Citizenry",
                product_url="https://www.thecitizenry.com/products/cotton-tote",
                title="Organic Cotton Tote Bag",
                price=18.50,
                currency="EUR",
                search_term="tote bag",
                matched_catalog_id="ECO-BAG-004",
                similarity_score=0.92,
                match_reason="title overlap=0.92"
            ),
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="Package Free Shop",
                product_url="https://packagefreeshop.com/products/organic-tote",
                title="Eco-Friendly Cotton Tote",
                price=21.00,
                currency="EUR",
                search_term="tote bag",
                matched_catalog_id="ECO-BAG-004",
                similarity_score=0.78,
                match_reason="title overlap=0.78"
            ),
            
            # Coffee cup competitors
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="Zero Waste Store",
                product_url="https://zerowaste.store/products/bamboo-cup",
                title="Bamboo Coffee Cup with Lid",
                price=22.99,
                currency="EUR",
                search_term="coffee cup",
                matched_catalog_id="ECO-CUP-005",
                similarity_score=0.81,
                match_reason="title overlap=0.81"
            ),
            ScrapedProduct(
                run_id="sample_run_001",
                store_name="EarthHero",
                product_url="https://earthhero.com/products/reusable-cup",
                title="Reusable Bamboo Cup",
                price=16.50,
                currency="EUR",
                search_term="coffee cup",
                matched_catalog_id="ECO-CUP-005",
                similarity_score=0.74,
                match_reason="title overlap=0.74"
            )
        ]
        
        for scraped_product in sample_scraped_data:
            session.add(scraped_product)
        
        await session.commit()
        print("✅ Sample data seeded successfully!")
        print(f"   - {len(sample_products)} products added")
        print(f"   - 1 completed scraping run added")
        print(f"   - {len(sample_scraped_data)} competitor price points added")


if __name__ == "__main__":
    asyncio.run(seed_sample_data())