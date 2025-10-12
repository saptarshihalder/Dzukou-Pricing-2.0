from __future__ import annotations

import logging
from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional

logger = logging.getLogger(__name__)


@dataclass
class Constraints:
    min_margin_percent: float = 40.0
    max_price_increase_percent: float = 20.0
    psychological_pricing: bool = True
    strategy: str = "competitive"  # value|competitive|premium


def psych_round(price: float) -> float:
    if price <= 0:
        return 0.0
    # round to .95
    int_part = int(price)
    cents = 0.95
    if price - int_part < 0.95:
        return int_part - 1 + 0.95 if int_part >= 1 else 0.95
    return int_part + 0.95


def pick_target_percentile(prices: list[float], strategy: str) -> float:
    if not prices:
        return 0.5
    sorted_prices = sorted(prices)
    if strategy == "value":
        idx = max(0, int(0.25 * (len(sorted_prices) - 1)))
    elif strategy == "premium":
        idx = min(len(sorted_prices) - 1, int(0.75 * (len(sorted_prices) - 1)))
    else:
        idx = int(0.5 * (len(sorted_prices) - 1))
    return sorted_prices[idx]


async def calc_recommendation(
    unit_cost: float,
    current_price: float,
    competitor_prices: Iterable[float],
    constraints: Constraints,
    product_name: str = "Unknown Product",
    category: str = "general",
    brand: str = "Unknown Brand",
    use_llm: bool = True,
) -> dict:
    from .llm import llm_service, PricingContext
    
    comp = [p for p in competitor_prices if p and p > 0]
    flags: list[str] = []
    llm_insight = None
    
    # Determine market position
    if comp:
        comp_median = sorted(comp)[len(comp) // 2] if comp else current_price
        if current_price < comp_median * 0.9:
            market_position = "below"
        elif current_price > comp_median * 1.1:
            market_position = "above"
        else:
            market_position = "competitive"
    else:
        market_position = "unknown"
    
    # Get LLM insights if available and requested
    if use_llm and llm_service.is_available():
        try:
            context = PricingContext(
                product_name=product_name,
                category=category,
                brand=brand,
                current_price=current_price,
                unit_cost=unit_cost,
                competitor_prices=comp,
                market_position=market_position
            )
            llm_insight = await llm_service.get_market_insight(context)
            if llm_insight:
                logger.info(f"LLM insight for {product_name}: positioning={llm_insight.brand_positioning}, elasticity={llm_insight.demand_elasticity}")
        except Exception as e:
            logger.error(f"LLM insight failed for {product_name}: {e}")
    
    # Calculate base target price
    if not comp:
        # fallback: maintain price with min margin enforcement
        target = max(current_price, unit_cost * (1 + constraints.min_margin_percent / 100.0))
    else:
        market_min = min(comp)
        market_max = max(comp)
        spread = (market_max - market_min) or (market_min * 0.2)
        lower = market_min - 0.2 * market_min
        upper = market_max + 0.2 * market_max
        
        # Use LLM positioning if available, otherwise use constraints
        strategy = constraints.strategy
        if llm_insight and llm_insight.confidence > 0.6:
            if llm_insight.brand_positioning == "luxury":
                strategy = "premium"
                flags.append("llm_luxury_positioning")
            elif llm_insight.brand_positioning == "premium":
                strategy = "premium"
                flags.append("llm_premium_positioning")
            elif llm_insight.brand_positioning == "value":
                strategy = "value"
                flags.append("llm_value_positioning")
        
        base = pick_target_percentile(comp, strategy)
        target = min(max(base, lower), upper)
        
        # Apply LLM elasticity adjustment
        if llm_insight and llm_insight.confidence > 0.5:
            # If demand is elastic (negative elasticity), be more conservative with increases
            if llm_insight.demand_elasticity < -1.0 and target > current_price:
                elasticity_factor = 0.7  # Reduce price increase for elastic demand
                target = current_price + (target - current_price) * elasticity_factor
                flags.append("llm_elasticity_adjustment")
            # If demand is inelastic (positive elasticity), can be more aggressive
            elif llm_insight.demand_elasticity > 0.5 and target < current_price * 1.1:
                elasticity_factor = 1.2  # Allow higher prices for inelastic demand
                target = min(target * elasticity_factor, upper)
                flags.append("llm_inelastic_boost")
        
        # Apply seasonal factor
        if llm_insight and llm_insight.seasonal_factor != 1.0:
            target *= llm_insight.seasonal_factor
            if llm_insight.seasonal_factor > 1.0:
                flags.append("llm_seasonal_boost")
            else:
                flags.append("llm_seasonal_discount")
        
        # enforce min margin
        min_price = unit_cost * (1 + constraints.min_margin_percent / 100.0)
        if target < min_price:
            flags.append("raised_to_min_margin")
        target = max(target, min_price)
        
    # limit max increase
    max_allowed = current_price * (1 + constraints.max_price_increase_percent / 100.0)
    if target > max_allowed:
        target = max_allowed
        flags.append("capped_by_max_increase")
        
    # psychological pricing
    rec_price = psych_round(target) if constraints.psychological_pricing else round(target, 2)

    def margin(price: float) -> float:
        return 0.0 if price <= 0 else (price - unit_cost) / price * 100.0

    # Enhanced scenario analysis with LLM insights
    if llm_insight and llm_insight.demand_elasticity:
        # Use elasticity for better scenario modeling
        elasticity = llm_insight.demand_elasticity
        cons_factor = 0.98 if elasticity < -1.0 else 0.97  # More conservative for elastic demand
        aggr_factor = 1.05 if elasticity > 0.5 else 1.03   # More aggressive for inelastic demand
    else:
        # Fallback to simple factors
        cons_factor = 0.98
        aggr_factor = 1.03
    
    cons_price = rec_price * cons_factor
    aggr_price = rec_price * aggr_factor
    
    scenarios = {
        "conservative": {"price": round(cons_price, 2), "expected_margin": round(margin(cons_price), 2)},
        "recommended": {"price": round(rec_price, 2), "expected_margin": round(margin(rec_price), 2)},
        "aggressive": {"price": round(aggr_price, 2), "expected_margin": round(margin(aggr_price), 2)},
    }

    price_change_percent = 0.0 if current_price == 0 else (rec_price - current_price) / current_price * 100.0
    expected_profit_change = (rec_price - unit_cost) - (current_price - unit_cost)
    
    # confidence: more competitors => more confidence; penalize heavy constraints
    confidence = min(1.0, 0.4 + 0.1 * len(comp))
    if "capped_by_max_increase" in flags:
        confidence -= 0.1
    
    # Boost confidence with LLM insights
    if llm_insight:
        confidence = min(1.0, confidence + 0.2 * llm_insight.confidence)
        if llm_insight.confidence > 0.8:
            flags.append("high_llm_confidence")
    
    confidence = round(max(0.0, confidence), 2)

    # risk heuristic
    risk = "low" if confidence >= 0.7 else ("medium" if confidence >= 0.4 else "high")

    # Build enhanced rationale with structured format
    rationale_parts = [
        f"Used {len(comp)} competitor prices",
        f"aimed for {constraints.strategy} positioning",
        f"enforced min margin {constraints.min_margin_percent}% and max increase {constraints.max_price_increase_percent}%"
    ]
    
    llm_rationale_parts = []
    if llm_insight:
        llm_rationale_parts.extend([
            f"LLM analysis: {llm_insight.brand_positioning} positioning",
            f"demand elasticity {llm_insight.demand_elasticity:.1f}",
            f"market saturation {llm_insight.market_saturation}"
        ])
        if llm_insight.seasonal_factor != 1.0:
            llm_rationale_parts.append(f"seasonal factor {llm_insight.seasonal_factor:.1f}")
        if llm_insight.reasoning:
            llm_rationale_parts.append(f"Reasoning: {llm_insight.reasoning}")
    
    # Create structured rationale for better frontend display
    rationale_sections = {
        "competitive_analysis": "; ".join(rationale_parts),
        "llm_insights": "; ".join(llm_rationale_parts) if llm_rationale_parts else None
    }
    
    # Keep backward compatibility with simple string format
    rationale = "; ".join(rationale_parts + llm_rationale_parts)

    result = {
        "recommended_price": round(rec_price, 2),
        "price_change_percent": round(price_change_percent, 2),
        "expected_profit_change": round(expected_profit_change, 2),
        "risk_level": risk,
        "confidence_score": confidence,
        "scenarios": scenarios,
        "rationale": rationale,
        "rationale_sections": rationale_sections,
        "constraint_flags": flags,
    }
    
    # Add LLM insights to response if available
    if llm_insight:
        result["llm_insights"] = {
            "demand_elasticity": llm_insight.demand_elasticity,
            "brand_positioning": llm_insight.brand_positioning,
            "market_saturation": llm_insight.market_saturation,
            "seasonal_factor": llm_insight.seasonal_factor,
            "confidence": llm_insight.confidence,
            "reasoning": llm_insight.reasoning
        }
    
    return result
