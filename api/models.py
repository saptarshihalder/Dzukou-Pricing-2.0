from __future__ import annotations

import uuid
from datetime import datetime, UTC
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import JSON, TIMESTAMP, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    scraped_products: Mapped[list["ScrapedProduct"]] = relationship(back_populates="matched_product")
    recommendations: Mapped[list["PriceRecommendation"]] = relationship(back_populates="product")


class ScrapingStatusEnum(str, PyEnum):  # type: ignore[misc]
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class ScrapingRun(Base):
    __tablename__ = "scraping_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String, nullable=False, default=ScrapingStatusEnum.PENDING.value)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    target_products: Mapped[list[str]] = mapped_column(JSON, default=list)
    stores_total: Mapped[int] = mapped_column(Integer, default=0)
    stores_completed: Mapped[int] = mapped_column(Integer, default=0)
    products_found: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[dict]] = mapped_column(JSON, default=list)

    scraped_products: Mapped[list["ScrapedProduct"]] = relationship(back_populates="run")


class ScrapedProduct(Base):
    __tablename__ = "scraped_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("scraping_runs.id"), index=True)
    store_name: Mapped[str] = mapped_column(String, index=True)
    product_url: Mapped[str] = mapped_column(Text)
    product_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    brand: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    search_term: Mapped[str] = mapped_column(String)
    matched_catalog_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("products.id"), nullable=True)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC), index=True)

    run: Mapped[ScrapingRun] = relationship(back_populates="scraped_products")
    matched_product: Mapped[Optional[Product]] = relationship(back_populates="scraped_products")


class PriceRecommendation(Base):
    __tablename__ = "price_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String, ForeignKey("products.id"), index=True)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    expected_profit_change: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    scenarios: Mapped[dict] = mapped_column(JSON, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    constraint_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))

    product: Mapped[Product] = relationship(back_populates="recommendations")
