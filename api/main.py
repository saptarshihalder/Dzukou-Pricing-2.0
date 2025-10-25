from __future__ import annotations

import asyncio
import csv
import logging
import re
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session, init_db, shutdown_db
from .models import PriceRecommendation as PriceRecommendationModel
from .models import Product, ScrapedProduct, ScrapingRun


async def get_db_session():
    """Dependency for getting database session"""
    async with get_session() as session:
        yield session
from .optimizer import Constraints, calc_recommendation
from .schemas import (
    OptimizeBatchRequest,
    OptimizeBatchResponse,
    OptimizeSingleRequest,
    PriceConstraints,
    PriceRecommendation as PriceRecommendationSchema,
    ScrapedProductOut,
    ScrapingProgress,
    StartScrapingRequest,
    StartScrapingResponse,
)
from .settings import get_settings
from .scraping import run_scraping_run

# Setup logging
logger = logging.getLogger(__name__)

app = FastAPI(title="Price Optim AI API")
app.state.db_ready = False


# CORS
settings = get_settings()
cors_origins = [str(o) for o in settings.CORS_ORIGINS] + ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    # Init DB and create tables
    from . import models
    try:
        logger.info("Initializing database...")
        await init_db(models)
        app.state.db_ready = True
        logger.info("Database initialized successfully")
        
        # Seed catalog if empty from CSV
        csv_path = Path(__file__).parent / "Dzukou_Pricing_Overview_With_Names - Copy.csv"
        logger.info(f"Checking for CSV file at: {csv_path}")
        
        if csv_path.exists():
            logger.info("CSV file found, checking if catalog needs seeding...")
            async with get_session() as session:
                res = await session.execute(select(Product).limit(1))
                existing_product = res.scalar_one_or_none()
                
                if existing_product is None:
                    logger.info("Catalog is empty, seeding from CSV...")
                    products_added = await seed_catalog_from_csv(session, csv_path)
                    logger.info(f"Successfully seeded catalog with {products_added} products")
                else:
                    logger.info(f"Catalog already contains products (found: {existing_product.name}), skipping seed")
        else:
            logger.warning(f"CSV file not found at {csv_path}. Catalog will remain empty.")
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        # Defer DB setup; routes that need DB may fail until DB is available
        app.state.db_ready = False


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await shutdown_db()


async def seed_catalog_from_csv(session: AsyncSession, path: Path) -> int:
    """Seed catalog from CSV, inferring categories from product names.
    
    Returns the number of products successfully added.
    """
    
    def infer_category(name: str) -> str:
        """Infer product category from name"""
        name_lower = name.lower()
        if "sunglass" in name_lower or "eyewear" in name_lower:
            return "sunglasses"
        elif "bottle" in name_lower or "thermos" in name_lower or "flask" in name_lower:
            return "bottles"
        elif "notebook" in name_lower or "journal" in name_lower:
            return "notebooks"
        elif "mug" in name_lower or "cup" in name_lower:
            return "mugs"
        elif "stand" in name_lower or "holder" in name_lower:
            return "stands"
        elif "lunchbox" in name_lower or "lunch box" in name_lower:
            return "lunchboxes"
        elif "stole" in name_lower or "shawl" in name_lower or "scarf" in name_lower:
            return "stoles"
        elif "cushion" in name_lower or "pillow" in name_lower:
            return "cushions"
        elif "towel" in name_lower:
            return "towels"
        else:
            return "general"
    
    products_added = 0
    rows_processed = 0
    
    # Try different encodings for the CSV file
    encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1', 'cp1252']
    file_handle = None
    reader = None
    
    for encoding in encodings:
        try:
            file_handle = path.open("r", newline="", encoding=encoding)
            reader = csv.DictReader(file_handle)
            # Test if we can read the fieldnames to validate encoding
            fieldnames = reader.fieldnames
            logger.info(f"Successfully opened CSV with {encoding} encoding")
            logger.info(f"CSV columns found: {fieldnames}")
            break
        except (UnicodeDecodeError, UnicodeError) as e:
            logger.debug(f"Failed to open CSV with {encoding} encoding: {e}")
            if file_handle:
                file_handle.close()
                file_handle = None
            continue
    
    if not reader or not file_handle:
        raise ValueError(f"Could not read CSV file with any of the attempted encodings: {encodings}")
    
    try:
        for row in reader:
            rows_processed += 1
            try:
                # Extract product name (first priority)
                name = (row.get("Product Name") or row.get("name") or 
                       row.get("title") or row.get("Product") or "Unnamed").strip()
                
                # Extract product ID
                prod_id = (row.get("Product ID") or row.get("id") or 
                          row.get("product_id") or row.get("SKU") or "").strip()
                
                if not prod_id or not name:
                    logger.debug(f"Skipping row {rows_processed}: missing ID or name - ID: '{prod_id}', Name: '{name}'")
                    continue
                
                # Check for duplicate IDs
                existing = await session.execute(select(Product).where(Product.id == prod_id))
                if existing.scalar_one_or_none():
                    logger.debug(f"Skipping row {rows_processed}: product ID '{prod_id}' already exists")
                    continue
                
                # Infer category from product name
                category = infer_category(name)
                
                # Parse prices (remove currency symbols and whitespace)
                current_price_str = (row.get("Current Price") or row.get(" Current Price ") or 
                                    row.get("current_price") or row.get("price") or "0").strip()
                unit_cost_str = (row.get("Unit Cost") or row.get(" Unit Cost ") or 
                                row.get("unit_cost") or row.get("cost") or "0").strip()
                
                # Remove currency symbols (€, $, £) and other non-numeric chars except decimal point
                current_price = float(re.sub(r"[^\d.]", "", current_price_str.replace("€", "").replace("�", "")) or 0)
                unit_cost = float(re.sub(r"[^\d.]", "", unit_cost_str.replace("€", "").replace("�", "")) or 0)
                
                if current_price <= 0:
                    logger.debug(f"Skipping row {rows_processed}: invalid price '{current_price_str}' for product '{name}'")
                    continue
                
                prod = Product(
                    id=prod_id,
                    name=name,
                    category=category,
                    brand="Dzukou",  # Default brand from the spec
                    unit_cost=unit_cost,
                    current_price=current_price,
                    currency="EUR",  # From the CSV (€ symbol)
                )
                session.add(prod)
                products_added += 1
                logger.debug(f"Added product: {name} (ID: {prod_id}, Category: {category}, Price: €{current_price})")
                
            except Exception as e:
                logger.warning(f"Failed to parse row {rows_processed}: {row}. Error: {e}")
                continue
        
        try:
            await session.commit()
            logger.info(f"Successfully committed {products_added} products to database (processed {rows_processed} rows)")
        except Exception as e:
            logger.error(f"Failed to commit products to database: {e}")
            await session.rollback()
            raise
    
    finally:
        # Always close the file handle
        if file_handle:
            file_handle.close()
    
    return products_added


@app.get("/routes/health")
async def health() -> dict:
    return {
        "ok": True, 
        "db_ready": bool(getattr(app.state, "db_ready", False)),
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "healthy" if getattr(app.state, "db_ready", False) else "initializing"
    }


@app.post("/routes/admin/seed-catalog")
async def manual_seed_catalog(session: AsyncSession = Depends(get_db_session)):
    """Manually trigger catalog seeding from CSV"""
    csv_path = Path(__file__).parent / "Dzukou_Pricing_Overview_With_Names - Copy.csv"
    
    if not csv_path.exists():
        raise HTTPException(404, f"CSV file not found at {csv_path}")
    
    # Check current catalog status
    res = await session.execute(select(Product))
    existing_count = len(res.scalars().all())
    
    if existing_count > 0:
        raise HTTPException(400, f"Catalog already contains {existing_count} products. Clear catalog first if you want to re-seed.")
    
    try:
        products_added = await seed_catalog_from_csv(session, csv_path)
        return {
            "message": "Catalog seeded successfully",
            "products_added": products_added,
            "csv_path": str(csv_path)
        }
    except Exception as e:
        logger.error(f"Manual catalog seeding failed: {e}")
        raise HTTPException(500, f"Failed to seed catalog: {str(e)}")


@app.get("/routes/admin/catalog-status")
async def get_catalog_status(session: AsyncSession = Depends(get_db_session)):
    """Get current catalog status"""
    res = await session.execute(select(Product))
    products = res.scalars().all()
    
    # Group by category
    categories = {}
    for product in products:
        cat = product.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "id": product.id,
            "name": product.name,
            "price": product.current_price,
            "currency": product.currency
        })
    
    csv_path = Path(__file__).parent / "Dzukou_Pricing_Overview_With_Names - Copy.csv"
    
    return {
        "total_products": len(products),
        "categories": {cat: len(prods) for cat, prods in categories.items()},
        "category_details": categories,
        "csv_file_exists": csv_path.exists(),
        "csv_path": str(csv_path)
    }


@app.get("/routes/products")
async def get_products(session: AsyncSession = Depends(get_db_session)):
    """Get all products in catalog"""
    res = await session.execute(select(Product))
    products = res.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "brand": p.brand,
            "unit_cost": p.unit_cost,
            "current_price": p.current_price,
            "currency": p.currency,
            "margin": ((p.current_price - p.unit_cost) / p.current_price * 100) if p.current_price > 0 else 0
        }
        for p in products
    ]


@app.get("/routes/dashboard-stats")
async def get_dashboard_stats(session: AsyncSession = Depends(get_db_session)):
    """Get dashboard KPI statistics"""
    # Get product count
    product_count_res = await session.execute(select(Product.id))
    total_products = len(product_count_res.scalars().all())
    
    # Get average margin
    products_res = await session.execute(select(Product.current_price, Product.unit_cost))
    products_data = products_res.all()
    
    margins = []
    for price, cost in products_data:
        if price > 0:
            margin = (price - cost) / price * 100
            margins.append(margin)
    
    avg_margin = sum(margins) / len(margins) if margins else 0
    
    # Get latest scraping run
    latest_run_res = await session.execute(
        select(ScrapingRun)
        .where(ScrapingRun.status.in_(["completed", "stopped"]))
        .order_by(ScrapingRun.completed_at.desc())
        .limit(1)
    )
    latest_run = latest_run_res.scalar_one_or_none()
    
    # Calculate potential uplift and price change from recent recommendations
    from datetime import timedelta
    cutoff_time = datetime.now(UTC) - timedelta(hours=168)  # Last 7 days
    
    recent_recs_res = await session.execute(
        select(PriceRecommendationModel.expected_profit_change, PriceRecommendationModel.price_change_percent)
        .where(PriceRecommendationModel.created_at >= cutoff_time)
        .order_by(PriceRecommendationModel.created_at.desc())
        .limit(100)  # Limit to recent recommendations
    )
    recent_recommendations = recent_recs_res.all()
    
    # Calculate averages from actual recommendations
    if recent_recommendations:
        profit_changes = [rec.expected_profit_change for rec in recent_recommendations if rec.expected_profit_change > 0]
        price_changes = [abs(rec.price_change_percent) for rec in recent_recommendations]
        
        # Calculate potential uplift as percentage of total revenue
        total_current_revenue = sum(price * 1 for price, _ in products_data if price > 0)  # Assuming 1 unit per product
        total_profit_uplift = sum(profit_changes) if profit_changes else 0
        potential_uplift = (total_profit_uplift / total_current_revenue * 100) if total_current_revenue > 0 and total_profit_uplift > 0 else 0
        
        avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
    else:
        potential_uplift = 0
        avg_price_change = 0
    
    return {
        "total_products": total_products,
        "avg_margin": round(avg_margin, 1),
        "potential_uplift": round(potential_uplift, 1),
        "avg_price_change": round(avg_price_change, 1),
        "last_scrape_date": latest_run.completed_at.isoformat() if latest_run and latest_run.completed_at else None,
        "scraping_stats": {
            "stores_scraped": latest_run.stores_completed if latest_run else 0,
            "stores_total": latest_run.stores_total if latest_run else 0,
            "products_found": latest_run.products_found if latest_run else 0
        } if latest_run else None
    }


@app.get("/routes/competitive-analysis/categories")
async def get_category_analysis(session: AsyncSession = Depends(get_db_session)):
    """Get competitive analysis by category"""
    # Get latest completed or stopped run
    latest_run_res = await session.execute(
        select(ScrapingRun)
        .where(ScrapingRun.status.in_(["completed", "stopped"]))
        .order_by(ScrapingRun.completed_at.desc())
        .limit(1)
    )
    latest_run = latest_run_res.scalar_one_or_none()
    
    if not latest_run:
        return []
    
    # Get products with their categories and scraped competitor prices
    products_res = await session.execute(
        select(Product.category, Product.current_price, ScrapedProduct.price)
        .join(ScrapedProduct, Product.id == ScrapedProduct.matched_catalog_id)
        .where(ScrapedProduct.run_id == latest_run.id)
    )
    
    # Group by category
    category_data = {}
    for category, our_price, comp_price in products_res.all():
        if category not in category_data:
            category_data[category] = {
                "our_prices": [],
                "competitor_prices": []
            }
        category_data[category]["our_prices"].append(our_price)
        category_data[category]["competitor_prices"].append(comp_price)
    
    # Calculate statistics for each category
    result = []
    for category, data in category_data.items():
        our_avg = sum(data["our_prices"]) / len(data["our_prices"]) if data["our_prices"] else 0
        comp_prices = data["competitor_prices"]
        
        if comp_prices:
            comp_min = min(comp_prices)
            comp_max = max(comp_prices)
            comp_median = sorted(comp_prices)[len(comp_prices) // 2]
            
            # Determine market position
            if our_avg < comp_median * 0.9:
                position = "below"
            elif our_avg > comp_median * 1.1:
                position = "above"
            else:
                position = "competitive"
            
            # Calculate opportunity (simplified)
            opportunity = max(0, (comp_median - our_avg) / our_avg * 100) if our_avg > 0 else 0
        else:
            comp_min = comp_max = comp_median = 0
            position = "unknown"
            opportunity = 0
        
        result.append({
            "category": category,
            "our_avg_price": round(our_avg, 2),
            "competitor_min": round(comp_min, 2) if comp_min else 0,
            "competitor_max": round(comp_max, 2) if comp_max else 0,
            "competitor_median": round(comp_median, 2) if comp_median else 0,
            "market_position": position,
            "opportunity": round(opportunity, 1),
            "products": len(set(data["our_prices"])),
            "competitor_data_points": len(comp_prices)
        })
    
    return result


@app.get("/routes/competitive-analysis/stores")
async def get_store_analysis(session: AsyncSession = Depends(get_db_session)):
    """Get competitive analysis by store"""
    # Get latest completed or stopped run
    latest_run_res = await session.execute(
        select(ScrapingRun)
        .where(ScrapingRun.status.in_(["completed", "stopped"]))
        .order_by(ScrapingRun.completed_at.desc())
        .limit(1)
    )
    latest_run = latest_run_res.scalar_one_or_none()
    
    if not latest_run:
        return []
    
    # Get scraped products grouped by store
    stores_res = await session.execute(
        select(ScrapedProduct.store_name, ScrapedProduct.price, ScrapedProduct.matched_catalog_id)
        .where(ScrapedProduct.run_id == latest_run.id)
    )
    
    # Group by store
    store_data = {}
    for store_name, price, matched_id in stores_res.all():
        if store_name not in store_data:
            store_data[store_name] = {
                "prices": [],
                "matched_products": set(),
                "total_products": 0
            }
        store_data[store_name]["prices"].append(price)
        store_data[store_name]["total_products"] += 1
        if matched_id:
            store_data[store_name]["matched_products"].add(matched_id)
    
    # Calculate statistics for each store
    result = []
    for store_name, data in store_data.items():
        prices = data["prices"]
        avg_price = sum(prices) / len(prices) if prices else 0
        price_range = f"€{min(prices):.0f}-€{max(prices):.0f}" if prices else "€0-€0"
        
        # Determine positioning based on average price
        if avg_price > 80:
            positioning = "luxury"
        elif avg_price > 50:
            positioning = "premium"
        else:
            positioning = "value"
        
        overlap_count = len(data["matched_products"])
        overlap_percent = (overlap_count / data["total_products"] * 100) if data["total_products"] > 0 else 0
        
        result.append({
            "store": store_name,
            "avg_price": round(avg_price, 2),
            "price_range": price_range,
            "products": data["total_products"],
            "overlap": overlap_count,
            "overlap_percent": round(overlap_percent, 1),
            "positioning": positioning
        })
    
    return result
@app.get("/routes/latest-run")
async def get_latest_run(session: AsyncSession = Depends(get_db_session)):
    """Get the most recent scraping run (running or completed)"""
    res = await session.execute(
        select(ScrapingRun)
        .order_by(ScrapingRun.started_at.desc())
        .limit(1)
    )
    run = res.scalar_one_or_none()
    if not run:
        return None
    return {
        "id": run.id,
        "status": run.status,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "stores_total": run.stores_total,
        "stores_completed": run.stores_completed,
        "products_found": run.products_found,
    }


@app.post("/routes/start-scraping", response_model=StartScrapingResponse)
async def start_scraping(payload: StartScrapingRequest, background: BackgroundTasks, session: AsyncSession = Depends(get_db_session)):
    # If no target products specified, use default search terms from catalog categories
    target_products = payload.target_products
    if not target_products:
        # Default search terms covering main product categories
        target_products = [
            "sunglasses",
            "water bottle",
            "notebook",
            "coffee mug",
            "phone stand",
            "lunch box",
            "shawl",
            "cushion cover",
            "towel",
        ]
    
    run = ScrapingRun(
        status="running", started_at=datetime.now(UTC), target_products=target_products, stores_total=0, stores_completed=0
    )
    session.add(run)
    await session.flush()

    background.add_task(run_scraping_run, run.id, target_products, payload.stores)

    await session.commit()
    return StartScrapingResponse(run_id=run.id)


@app.post("/routes/stop-scraping/{run_id}")
async def stop_scraping(run_id: str, session: AsyncSession = Depends(get_db_session)):
    """Stop a running scraping operation"""
    try:
        res = await session.execute(select(ScrapingRun).where(ScrapingRun.id == run_id))
        run = res.scalar_one_or_none()
        if not run:
            raise HTTPException(404, f"Scraping run {run_id} not found")
        
        if run.status != "running":
            raise HTTPException(400, f"Cannot stop scraping run with status: {run.status}")
        
        # Update run status to stopped
        run.status = "stopped"  # Use "stopped" to indicate manually stopped
        run.completed_at = datetime.now(UTC)
        run.errors.append({"error": "Scraping stopped by user", "timestamp": datetime.now(UTC).isoformat()})
        
        await session.commit()
        
        logger.info(f"Scraping run {run_id} stopped by user")
        return {"message": "Scraping run stopped successfully", "run_id": run_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping scraping run {run_id}: {str(e)}")
        raise HTTPException(500, f"Error stopping scraping run: {str(e)}")


@app.get("/routes/scraping-progress/{run_id}", response_model=ScrapingProgress)
async def scraping_progress(run_id: str, session: AsyncSession = Depends(get_db_session)):
    try:
        res = await session.execute(select(ScrapingRun).where(ScrapingRun.id == run_id))
        run = res.scalar_one_or_none()
        if not run:
            raise HTTPException(404, f"Scraping run {run_id} not found")
        return ScrapingProgress(
            status=run.status,
            stores_total=run.stores_total,
            stores_completed=run.stores_completed,
            products_found=run.products_found,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error retrieving scraping progress: {str(e)}")


@app.get("/routes/scraping-results/{run_id}", response_model=list[ScrapedProductOut])
async def scraping_results(run_id: str, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(ScrapedProduct).where(ScrapedProduct.run_id == run_id))
    items = res.scalars().all()
    return [
        ScrapedProductOut(
            run_id=i.run_id,
            store_name=i.store_name,
            product_url=i.product_url,
            product_id=i.product_id,
            title=i.title,
            price=i.price,
            currency=i.currency,
            brand=i.brand,
            material=i.material,
            size=i.size,
            search_term=i.search_term,
            matched_catalog_id=i.matched_catalog_id,
            similarity_score=i.similarity_score,
            match_reason=i.match_reason,
            created_at=i.created_at,
        )
        for i in items
    ]


@app.post("/routes/admin/test-ml-matching")
async def test_ml_matching(session: AsyncSession = Depends(get_db_session)):
    """Test ML matching functionality"""
    from .ml_matching import ml_match_scraped_to_catalog
    
    # Get catalog for testing
    res = await session.execute(select(Product.id, Product.name, Product.brand, Product.category))
    catalog = [(pid, name, brand, category) for pid, name, brand, category in res.all()]
    
    if not catalog:
        raise HTTPException(400, "No catalog products found. Seed catalog first.")
    
    # Test cases
    test_cases = [
        "Bamboo Sunglasses with Case",
        "Organic Cotton Towel",
        "Stainless Steel Water Bottle",
        "Leather Journal Notebook",
        "Wooden Phone Stand Holder",
        "Insulated Coffee Mug"
    ]
    
    results = []
    for test_title in test_cases:
        try:
            match_result = await ml_match_scraped_to_catalog(test_title, None, catalog)
            results.append({
                "test_title": test_title,
                "matched_product_id": match_result.product_id,
                "score": round(match_result.score, 3),
                "semantic_score": round(match_result.semantic_score, 3),
                "category_bonus": match_result.category_bonus,
                "material_bonus": match_result.material_bonus,
                "reason": match_result.reason,
                "success": match_result.product_id is not None
            })
        except Exception as e:
            results.append({
                "test_title": test_title,
                "error": str(e),
                "success": False
            })
    
    success_count = sum(1 for r in results if r.get("success", False))
    
    return {
        "test_results": results,
        "summary": {
            "total_tests": len(test_cases),
            "successful_matches": success_count,
            "success_rate": f"{success_count/len(test_cases)*100:.1f}%",
            "catalog_size": len(catalog)
        }
    }


@app.get("/routes/runs/{run_id}/export.csv", response_class=PlainTextResponse)
async def export_run_csv(run_id: str, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(ScrapedProduct).where(ScrapedProduct.run_id == run_id))
    items = res.scalars().all()
    headers = [
        "run_id",
        "store_name",
        "product_url",
        "product_id",
        "title",
        "price",
        "currency",
        "brand",
        "material",
        "size",
        "search_term",
        "matched_catalog_id",
        "similarity_score",
        "match_reason",
        "created_at",
    ]
    from io import StringIO

    s = StringIO()
    w = csv.writer(s)
    w.writerow(headers)
    for i in items:
        w.writerow(
            [
                i.run_id,
                i.store_name,
                i.product_url,
                i.product_id or "",
                i.title,
                i.price,
                i.currency,
                i.brand or "",
                i.material or "",
                i.size or "",
                i.search_term,
                i.matched_catalog_id or "",
                i.similarity_score or "",
                i.match_reason or "",
                i.created_at.isoformat(),
            ]
        )
    return PlainTextResponse(content=s.getvalue(), media_type="text/csv")


@app.post("/routes/optimize-price", response_model=PriceRecommendationSchema)
async def optimize_price(payload: OptimizeSingleRequest, session: AsyncSession = Depends(get_db_session)):
    prod = (await session.execute(select(Product).where(Product.id == payload.product_id))).scalar_one_or_none()
    if not prod:
        raise HTTPException(404, "product not found")
    # get competitor prices from latest completed or stopped run
    last_run = (
        await session.execute(
            select(ScrapingRun).where(ScrapingRun.status.in_(["completed", "stopped"])).order_by(ScrapingRun.completed_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    comp_prices = []
    if last_run:
        res = await session.execute(
            select(ScrapedProduct.price).where(ScrapedProduct.matched_catalog_id == prod.id, ScrapedProduct.run_id == last_run.id)
        )
        comp_prices = [p for (p,) in res.all()]

    c = payload.constraints
    result = await calc_recommendation(
        unit_cost=prod.unit_cost,
        current_price=prod.current_price,
        competitor_prices=comp_prices,
        constraints=Constraints(
            min_margin_percent=c.min_margin_percent,
            max_price_increase_percent=c.max_price_increase_percent,
            psychological_pricing=c.psychological_pricing,
            strategy=c.strategy,
        ),
        product_name=prod.name,
        category=prod.category,
        brand=prod.brand,
        use_llm=True,
    )
    rec = PriceRecommendationModel(
        product_id=prod.id,
        current_price=prod.current_price,
        recommended_price=result["recommended_price"],
        price_change_percent=result["price_change_percent"],
        expected_profit_change=result["expected_profit_change"],
        risk_level=result["risk_level"],
        confidence_score=result["confidence_score"],
        scenarios=result["scenarios"],
        rationale=result["rationale"],
        constraint_flags=result["constraint_flags"],
        psychological_analysis=result.get("psychological_analysis"),
        psychological_pricing_enabled=result.get("psychological_pricing_enabled", False),
    )
    session.add(rec)
    await session.commit()
    return PriceRecommendationSchema(
        product_id=prod.id,
        current_price=prod.current_price,
        recommended_price=result["recommended_price"],
        price_change_percent=result["price_change_percent"],
        expected_profit_change=result["expected_profit_change"],
        risk_level=result["risk_level"],
        confidence_score=result["confidence_score"],
        scenarios=result["scenarios"],
        rationale=result["rationale"],
        rationale_sections=result.get("rationale_sections"),
        constraint_flags=result["constraint_flags"],
        psychological_analysis=result.get("psychological_analysis"),
        psychological_pricing_enabled=result.get("psychological_pricing_enabled", False),
        llm_insights=result.get("llm_insights"),
    )


@app.get("/routes/cached-recommendations")
async def get_cached_recommendations(session: AsyncSession = Depends(get_db_session), max_age_hours: int = 24):
    """Get cached recommendations that are still valid (within max_age_hours)"""
    from datetime import timedelta
    cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
    
    # Get recent recommendations
    res = await session.execute(
        select(PriceRecommendationModel)
        .where(PriceRecommendationModel.created_at >= cutoff_time)
        .order_by(PriceRecommendationModel.created_at.desc())
    )
    cached_recs = res.scalars().all()
    
    # Group by product_id and take the most recent for each product
    product_recs = {}
    for rec in cached_recs:
        if rec.product_id not in product_recs or rec.created_at > product_recs[rec.product_id].created_at:
            product_recs[rec.product_id] = rec
    
    # Convert to schema format
    recommendations = []
    for rec in product_recs.values():
        recommendations.append(PriceRecommendationSchema(
            product_id=rec.product_id,
            current_price=rec.current_price,
            recommended_price=rec.recommended_price,
            price_change_percent=rec.price_change_percent,
            expected_profit_change=rec.expected_profit_change,
            risk_level=rec.risk_level,
            confidence_score=rec.confidence_score,
            scenarios=rec.scenarios,
            rationale=rec.rationale,
            rationale_sections=None,  # Not stored in DB model
            constraint_flags=rec.constraint_flags,
        ))
    
    return {
        "recommendations": recommendations,
        "cache_info": {
            "cached_products": len(recommendations),
            "cache_age_hours": max_age_hours,
            "oldest_cache": min([r.created_at for r in product_recs.values()]).isoformat() if product_recs else None,
            "newest_cache": max([r.created_at for r in product_recs.values()]).isoformat() if product_recs else None,
        }
    }


@app.post("/routes/optimize-batch", response_model=OptimizeBatchResponse)
async def optimize_batch(payload: OptimizeBatchRequest, session: AsyncSession = Depends(get_db_session), use_cache: bool = True, cache_max_age_hours: int = 24):
    """Optimize batch pricing with caching support"""
    from datetime import timedelta
    
    if payload.product_ids:
        res = await session.execute(select(Product).where(Product.id.in_(payload.product_ids)))
    else:
        res = await session.execute(select(Product))
    products = res.scalars().all()
    
    # Check for cached recommendations if use_cache is True
    cached_recs = {}
    if use_cache:
        cutoff_time = datetime.now(UTC) - timedelta(hours=cache_max_age_hours)
        cache_res = await session.execute(
            select(PriceRecommendationModel)
            .where(
                PriceRecommendationModel.created_at >= cutoff_time,
                PriceRecommendationModel.product_id.in_([p.id for p in products])
            )
            .order_by(PriceRecommendationModel.created_at.desc())
        )
        all_cached = cache_res.scalars().all()
        
        # Get most recent cached recommendation per product
        for rec in all_cached:
            if rec.product_id not in cached_recs or rec.created_at > cached_recs[rec.product_id].created_at:
                cached_recs[rec.product_id] = rec
    
    # Get products that need fresh optimization
    products_to_optimize = [p for p in products if p.id not in cached_recs]
    
    logger.info(f"Using {len(cached_recs)} cached recommendations, optimizing {len(products_to_optimize)} products")
    
    # latest run for competitor data
    last_run = (
        await session.execute(
            select(ScrapingRun).where(ScrapingRun.status.in_(["completed", "stopped"])).order_by(ScrapingRun.completed_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    comp_by_prod: dict[str, list[float]] = {}
    if last_run:
        rows = (
            await session.execute(
                select(ScrapedProduct.matched_catalog_id, ScrapedProduct.price).where(ScrapedProduct.run_id == last_run.id)
            )
        ).all()
        for pid, price in rows:
            if pid:
                comp_by_prod.setdefault(pid, []).append(price)

    c = payload.constraints
    out: list[PriceRecommendationSchema] = []
    
    # Add cached recommendations
    for rec in cached_recs.values():
        out.append(
            PriceRecommendationSchema(
                product_id=rec.product_id,
                current_price=rec.current_price,
                recommended_price=rec.recommended_price,
                price_change_percent=rec.price_change_percent,
                expected_profit_change=rec.expected_profit_change,
                risk_level=rec.risk_level,
                confidence_score=rec.confidence_score,
                scenarios=rec.scenarios,
                rationale=rec.rationale,
                rationale_sections=None,  # Not stored in DB model
                constraint_flags=rec.constraint_flags,
            )
        )
    
    # Generate fresh recommendations for uncached products
    for p in products_to_optimize:
        comp_prices = comp_by_prod.get(p.id, [])
        result = await calc_recommendation(
            unit_cost=p.unit_cost,
            current_price=p.current_price,
            competitor_prices=comp_prices,
            constraints=Constraints(
                min_margin_percent=c.min_margin_percent,
                max_price_increase_percent=c.max_price_increase_percent,
                psychological_pricing=c.psychological_pricing,
                strategy=c.strategy,
            ),
            product_name=p.name,
            category=p.category,
            brand=p.brand,
            use_llm=True,
        )
        
        # Save to database for future caching
        rec_model = PriceRecommendationModel(
            product_id=p.id,
            current_price=p.current_price,
            recommended_price=result["recommended_price"],
            price_change_percent=result["price_change_percent"],
            expected_profit_change=result["expected_profit_change"],
            risk_level=result["risk_level"],
            confidence_score=result["confidence_score"],
            scenarios=result["scenarios"],
            rationale=result["rationale"],
            constraint_flags=result["constraint_flags"],
        )
        session.add(rec_model)
        
        out.append(
            PriceRecommendationSchema(
                product_id=p.id,
                current_price=p.current_price,
                recommended_price=result["recommended_price"],
                price_change_percent=result["price_change_percent"],
                expected_profit_change=result["expected_profit_change"],
                risk_level=result["risk_level"],
                confidence_score=result["confidence_score"],
                scenarios=result["scenarios"],
                rationale=result["rationale"],
                rationale_sections=result.get("rationale_sections"),
                constraint_flags=result["constraint_flags"],
            )
        )
    
    # Commit new recommendations to database
    if products_to_optimize:
        await session.commit()
    
    return OptimizeBatchResponse(recommendations=out)


# Uvicorn entry point for "fastapi run api.main:app"
__all__ = ["app"]

