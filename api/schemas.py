from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ProductIn(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    unit_cost: float
    current_price: float
    currency: str


class ProductOut(ProductIn):
    pass


class ScrapedProductOut(BaseModel):
    run_id: str
    store_name: str
    product_url: str
    product_id: Optional[str] = None
    title: str
    price: float
    currency: str
    brand: Optional[str] = None
    material: Optional[str] = None
    size: Optional[str] = None
    search_term: str
    matched_catalog_id: Optional[str] = None
    similarity_score: Optional[float] = None
    match_reason: Optional[str] = None
    created_at: datetime


class StartScrapingRequest(BaseModel):
    target_products: list[str] = Field(default_factory=list, description="Product ids or search terms")
    stores: Optional[list[str]] = None
    
    # Support legacy field name
    @property
    def targets(self) -> list[str]:
        return self.target_products


class StartScrapingResponse(BaseModel):
    run_id: str


class ScrapingProgress(BaseModel):
    status: Literal["pending", "running", "completed", "failed"]
    stores_total: int
    stores_completed: int
    products_found: int


class PriceConstraints(BaseModel):
    min_margin_percent: float = 40.0
    max_price_increase_percent: float = 20.0
    psychological_pricing: bool = True
    strategy: Literal["value", "competitive", "premium"] = "competitive"


class LLMInsights(BaseModel):
    """LLM-generated market insights for pricing decisions."""
    demand_elasticity: float = Field(..., description="Demand elasticity (-2.0 to 2.0, negative = elastic)")
    brand_positioning: Literal["value", "competitive", "premium", "luxury"] = Field(..., description="Recommended brand positioning")
    market_saturation: Literal["low", "medium", "high"] = Field(..., description="Market saturation level")
    seasonal_factor: float = Field(..., description="Seasonal pricing factor (0.5 to 2.0, 1.0 = neutral)")
    confidence: float = Field(..., description="LLM confidence score (0.0 to 1.0)")
    reasoning: str = Field(..., description="LLM reasoning for the recommendations")


class PriceRecommendation(BaseModel):
    product_id: str
    current_price: float
    recommended_price: float
    price_change_percent: float
    expected_profit_change: float
    risk_level: Literal["low", "medium", "high"]
    confidence_score: float
    scenarios: dict[str, dict[str, float]]
    rationale: str
    rationale_sections: Optional[dict[str, Optional[str]]] = Field(None, description="Structured rationale sections")
    constraint_flags: list[str] = Field(default_factory=list)
    llm_insights: Optional[LLMInsights] = Field(None, description="LLM-generated market insights if available")


class OptimizeSingleRequest(BaseModel):
    product_id: str
    constraints: PriceConstraints = Field(default_factory=PriceConstraints)


class OptimizeBatchRequest(BaseModel):
    product_ids: Optional[list[str]] = None
    constraints: PriceConstraints = Field(default_factory=PriceConstraints)


class OptimizeBatchResponse(BaseModel):
    recommendations: list[PriceRecommendation]
