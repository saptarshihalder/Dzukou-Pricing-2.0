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


def psych_round(price: float, category: str = "general", brand_positioning: str = "competitive") -> float:
    """
    AGGRESSIVE psychological pricing with maximum behavioral impact.
    
    Implements multiple psychological pricing strategies based on:
    - Price anchoring and reference points
    - Left-digit bias (charm pricing)
    - Category-specific consumer expectations
    - Brand positioning psychology
    """
    if price <= 0:
        return 0.0
    
    # MUCH MORE AGGRESSIVE category-specific psychological pricing rules
    category_rules = {
        "luxury": {"endings": [0.00], "threshold": 80, "adjustment": 1.05},  # Round numbers + 5% premium
        "premium": {"endings": [0.95, 0.99], "threshold": 40, "adjustment": 1.03},  # Charm + 3% premium
        "value": {"endings": [0.99, 0.89, 0.79], "threshold": 15, "adjustment": 0.97},  # Aggressive charm - 3%
        "tech": {"endings": [0.99, 0.95], "threshold": 25, "adjustment": 1.02},  # Tech premium + 2%
        "fashion": {"endings": [0.00, 0.95], "threshold": 35, "adjustment": 1.08},  # Fashion premium + 8%
        "food": {"endings": [0.99, 0.95, 0.89], "threshold": 12, "adjustment": 0.95},  # Food value - 5%
        "default": {"endings": [0.95, 0.99], "threshold": 20, "adjustment": 1.0}
    }
    
    # Map product categories to psychological categories
    category_mapping = {
        "sunglasses": "fashion",    # Fashion gets 8% premium
        "bottles": "premium",       # Premium gets 3% premium
        "notebooks": "value",       # Value gets 3% discount
        "mugs": "value",           # Value gets 3% discount
        "stands": "tech",          # Tech gets 2% premium
        "lunchboxes": "value",     # Value gets 3% discount
        "stoles": "luxury",        # Luxury gets 5% premium + round numbers
        "cushions": "premium",     # Premium gets 3% premium
        "towels": "value"          # Value gets 3% discount
    }
    
    psych_category = category_mapping.get(category.lower(), "default")
    
    # Adjust based on brand positioning (MORE AGGRESSIVE)
    if brand_positioning == "luxury":
        psych_category = "luxury"
    elif brand_positioning == "premium":
        psych_category = "premium"
    elif brand_positioning == "value":
        psych_category = "value"
    
    rules = category_rules.get(psych_category, category_rules["default"])
    
    # Apply category-specific price adjustment FIRST
    adjusted_price = price * rules["adjustment"]
    
    # Then apply psychological pricing rules
    if adjusted_price < 10:
        # For low prices, use VERY aggressive charm pricing
        return apply_aggressive_charm_pricing(adjusted_price, [0.99, 0.89, 0.79])
    elif adjusted_price < rules["threshold"]:
        # Medium prices - use category-specific endings with aggressive tactics
        return apply_aggressive_charm_pricing(adjusted_price, rules["endings"])
    elif adjusted_price < 100:
        # Higher prices - more aggressive psychological tactics
        if psych_category == "luxury":
            return apply_aggressive_prestige_pricing(adjusted_price)
        else:
            return apply_aggressive_charm_pricing(adjusted_price, rules["endings"])
    else:
        # Very high prices - luxury vs charm with big differences
        if psych_category == "luxury":
            return apply_aggressive_prestige_pricing(adjusted_price)
        else:
            return apply_aggressive_charm_pricing(adjusted_price, [0.95, 0.99])


def apply_charm_pricing(price: float, endings: list[float]) -> float:
    """Apply charm pricing with left-digit bias optimization"""
    int_part = int(price)
    decimal_part = price - int_part
    
    # Find the best ending that doesn't exceed the original price significantly
    best_ending = endings[0]  # Default to first ending
    
    for ending in endings:
        candidate_price = int_part + ending
        
        # If the candidate is close to original price, use it
        if candidate_price <= price * 1.02:  # Allow 2% increase for psychological benefit
            best_ending = ending
            break
        
        # If we need to go down a dollar, check if it's worth it
        lower_candidate = (int_part - 1) + ending
        if lower_candidate > 0 and lower_candidate >= price * 0.95:  # Don't go below 95% of original
            return lower_candidate
    
    return int_part + best_ending


def apply_prestige_pricing(price: float) -> float:
    """Apply prestige pricing for luxury items (round numbers)"""
    # Round to nearest 5 or 10 for prestige effect
    if price < 50:
        return round(price / 5) * 5
    elif price < 200:
        return round(price / 10) * 10
    else:
        return round(price / 25) * 25


def apply_aggressive_charm_pricing(price: float, endings: list[float]) -> float:
    """Apply VERY aggressive charm pricing with maximum psychological impact"""
    int_part = int(price)
    
    # For aggressive charm pricing, we're willing to make bigger adjustments
    best_price = price
    best_score = 0
    
    for ending in endings:
        # Try current dollar amount
        candidate = int_part + ending
        score = calculate_charm_score(price, candidate, ending)
        
        if score > best_score:
            best_price = candidate
            best_score = score
        
        # Try going up a dollar for better psychological impact
        if ending in [0.99, 0.95]:
            upper_candidate = (int_part + 1) + ending
            upper_score = calculate_charm_score(price, upper_candidate, ending)
            
            # Allow up to 15% increase for strong psychological benefit
            if upper_candidate <= price * 1.15 and upper_score > best_score:
                best_price = upper_candidate
                best_score = upper_score
        
        # Try going down a dollar for left-digit bias
        if int_part > 1:
            lower_candidate = (int_part - 1) + ending
            lower_score = calculate_charm_score(price, lower_candidate, ending)
            
            # Prefer lower prices if they create left-digit bias
            if lower_candidate >= price * 0.85 and lower_score > best_score * 0.8:
                best_price = lower_candidate
                best_score = lower_score
    
    return best_price


def apply_aggressive_prestige_pricing(price: float) -> float:
    """Apply VERY aggressive prestige pricing for maximum luxury perception"""
    # For luxury items, round to psychologically powerful numbers
    if price < 25:
        # Round to nearest 5, but prefer 20, 25, 30
        return round(price / 5) * 5
    elif price < 50:
        # Round to nearest 10, prefer 30, 40, 50
        base = round(price / 10) * 10
        # Add 10% luxury premium
        return base * 1.1
    elif price < 100:
        # Round to nearest 10, add luxury premium
        base = round(price / 10) * 10
        return base * 1.08  # 8% luxury premium
    elif price < 200:
        # Round to nearest 25, add premium
        base = round(price / 25) * 25
        return base * 1.05  # 5% luxury premium
    else:
        # Round to nearest 50 for very high prices
        base = round(price / 50) * 50
        return base * 1.03  # 3% luxury premium


def calculate_charm_score(original_price: float, candidate_price: float, ending: float) -> float:
    """Calculate psychological effectiveness score for charm pricing"""
    score = 0
    
    # Base score for charm endings
    if ending == 0.99:
        score += 20  # Highest charm effect
    elif ending == 0.95:
        score += 18  # High charm effect
    elif ending == 0.89:
        score += 15  # Medium charm effect
    elif ending == 0.79:
        score += 12  # Lower charm effect
    elif ending == 0.00:
        score += 8   # Prestige effect
    
    # Left-digit bias bonus (HUGE impact)
    original_left = int(str(int(original_price))[0])
    candidate_left = int(str(int(candidate_price))[0])
    if candidate_left < original_left:
        score += 30  # Massive bonus for left-digit reduction
    
    # Price change penalty/bonus
    price_change_percent = (candidate_price - original_price) / original_price * 100
    if -5 <= price_change_percent <= 10:
        score += 10  # Sweet spot for price changes
    elif price_change_percent > 15:
        score -= 15  # Penalty for large increases
    elif price_change_percent < -15:
        score -= 10  # Penalty for large decreases
    
    # Psychological price points bonus
    if candidate_price in [9.99, 19.99, 29.99, 39.99, 49.99, 59.99, 69.99, 79.99, 89.99, 99.99]:
        score += 15  # Bonus for powerful psychological price points
    
    return score


def calculate_psychological_impact(original_price: float, psych_price: float, category: str) -> dict:
    """
    Calculate the psychological impact and behavioral factors of the pricing change.
    
    Returns analysis of consumer behavior implications.
    """
    price_change = psych_price - original_price
    price_change_percent = (price_change / original_price * 100) if original_price > 0 else 0
    
    # Analyze left-digit bias impact
    original_left_digit = int(str(int(original_price))[0])
    psych_left_digit = int(str(int(psych_price))[0])
    left_digit_change = psych_left_digit != original_left_digit
    
    # Analyze price ending psychology
    original_ending = round((original_price % 1) * 100)
    psych_ending = round((psych_price % 1) * 100)
    
    # Determine psychological effects with MUCH MORE DRAMATIC scoring
    effects = []
    behavioral_score = 0
    
    if psych_ending in [95, 99]:
        effects.append("charm_pricing")
        behavioral_score += 25  # MUCH stronger positive effect
    
    if psych_ending in [89, 79]:
        effects.append("aggressive_charm_pricing")
        behavioral_score += 30  # Even stronger for aggressive charm
    
    if psych_ending == 0:
        effects.append("prestige_pricing")
        behavioral_score += 20  # Stronger positive effect for luxury
    
    if left_digit_change and price_change < 0:
        effects.append("left_digit_bias_positive")
        behavioral_score += 40  # MASSIVE effect for left-digit bias
    elif left_digit_change and price_change > 0:
        effects.append("left_digit_bias_negative")
        behavioral_score -= 25  # Strong negative effect
    
    # Reference point analysis with more dramatic scoring
    if abs(price_change_percent) < 2:
        effects.append("minimal_change")
        behavioral_score += 5
    elif 2 <= abs(price_change_percent) <= 8:
        effects.append("optimal_change")
        behavioral_score += 15  # Sweet spot for price changes
    elif price_change_percent > 15:
        effects.append("significant_increase")
        behavioral_score -= 30  # Much stronger penalty
    elif price_change_percent < -15:
        effects.append("significant_decrease")
        behavioral_score -= 20  # Penalty for big decreases
    
    # Psychological price points bonus
    if psych_price in [9.99, 19.99, 29.99, 39.99, 49.99, 59.99, 69.99, 79.99, 89.99, 99.99]:
        effects.append("psychological_price_point")
        behavioral_score += 20  # Big bonus for powerful price points
    
    # Category-specific behavioral factors
    category_factors = {
        "sunglasses": {"price_sensitivity": "medium", "brand_importance": "high"},
        "bottles": {"price_sensitivity": "low", "brand_importance": "medium"},
        "notebooks": {"price_sensitivity": "high", "brand_importance": "low"},
        "mugs": {"price_sensitivity": "medium", "brand_importance": "low"},
        "stands": {"price_sensitivity": "medium", "brand_importance": "medium"},
        "lunchboxes": {"price_sensitivity": "high", "brand_importance": "low"},
        "stoles": {"price_sensitivity": "low", "brand_importance": "high"},
        "cushions": {"price_sensitivity": "medium", "brand_importance": "medium"},
        "towels": {"price_sensitivity": "high", "brand_importance": "low"}
    }
    
    category_info = category_factors.get(category.lower(), {
        "price_sensitivity": "medium", 
        "brand_importance": "medium"
    })
    
    # Adjust behavioral score based on category
    if category_info["price_sensitivity"] == "high" and price_change > 0:
        behavioral_score -= 10
    elif category_info["price_sensitivity"] == "low" and price_change > 0:
        behavioral_score += 5
    
    return {
        "price_change": round(price_change, 2),
        "price_change_percent": round(price_change_percent, 2),
        "left_digit_changed": left_digit_change,
        "original_ending": original_ending,
        "psych_ending": psych_ending,
        "psychological_effects": effects,
        "behavioral_score": behavioral_score,
        "category_factors": category_info,
        "consumer_perception": get_consumer_perception(behavioral_score),
        "recommendation_strength": get_recommendation_strength(behavioral_score)
    }


def get_consumer_perception(behavioral_score: int) -> str:
    """Convert behavioral score to consumer perception description with more dramatic thresholds"""
    if behavioral_score >= 40:
        return "extremely_positive"
    elif behavioral_score >= 25:
        return "highly_positive"
    elif behavioral_score >= 15:
        return "positive"
    elif behavioral_score >= 5:
        return "slightly_positive"
    elif behavioral_score >= -5:
        return "neutral"
    elif behavioral_score >= -15:
        return "slightly_negative"
    elif behavioral_score >= -25:
        return "negative"
    else:
        return "extremely_negative"


def get_recommendation_strength(behavioral_score: int) -> str:
    """Convert behavioral score to recommendation strength with more dramatic thresholds"""
    if behavioral_score >= 35:
        return "extremely_strong"
    elif behavioral_score >= 20:
        return "strong"
    elif behavioral_score >= 10:
        return "moderate"
    elif behavioral_score >= 0:
        return "weak"
    elif behavioral_score >= -15:
        return "not_recommended"
    else:
        return "strongly_discouraged"


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
    try:
        from .llm import llm_service, PricingContext
    except ImportError:
        # Handle case when running as standalone script
        llm_service = None
        PricingContext = None
    
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
    if use_llm and llm_service and llm_service.is_available():
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
        
    # Enhanced psychological pricing with behavioral analysis
    if constraints.psychological_pricing:
        brand_positioning = "competitive"
        if llm_insight and llm_insight.brand_positioning:
            brand_positioning = llm_insight.brand_positioning
        
        rec_price = psych_round(target, category, brand_positioning)
        
        # Calculate psychological impact analysis
        psych_analysis = calculate_psychological_impact(current_price, rec_price, category)
        
        # If psychological impact is negative, try alternative pricing
        if psych_analysis["behavioral_score"] < -5:
            # Try without psychological pricing
            alternative_price = round(target, 2)
            alt_analysis = calculate_psychological_impact(current_price, alternative_price, category)
            
            if alt_analysis["behavioral_score"] > psych_analysis["behavioral_score"]:
                rec_price = alternative_price
                psych_analysis = alt_analysis
                flags.append("psychological_pricing_bypassed")
            else:
                flags.append("psychological_pricing_negative_impact")
        else:
            flags.append("psychological_pricing_applied")
    else:
        rec_price = round(target, 2)
        psych_analysis = None

    def margin(price: float) -> float:
        return 0.0 if price <= 0 else (price - unit_cost) / price * 100.0

    # Enhanced scenario analysis with LLM insights and psychological pricing
    if llm_insight and llm_insight.demand_elasticity:
        # Use elasticity for better scenario modeling
        elasticity = llm_insight.demand_elasticity
        cons_factor = 0.95 if elasticity < -1.0 else 0.97  # More conservative for elastic demand
        aggr_factor = 1.08 if elasticity > 0.5 else 1.05   # More aggressive for inelastic demand
    else:
        # Fallback to simple factors
        cons_factor = 0.97
        aggr_factor = 1.05
    
    # Apply psychological pricing to scenarios if enabled
    brand_positioning = "competitive"
    if llm_insight and llm_insight.brand_positioning:
        brand_positioning = llm_insight.brand_positioning
    
    if constraints.psychological_pricing:
        cons_price = psych_round(rec_price * cons_factor, category, brand_positioning)
        aggr_price = psych_round(rec_price * aggr_factor, category, brand_positioning)
    else:
        cons_price = round(rec_price * cons_factor, 2)
        aggr_price = round(rec_price * aggr_factor, 2)
    
    # Calculate psychological analysis for each scenario
    scenarios = {
        "conservative": {
            "price": cons_price, 
            "expected_margin": round(margin(cons_price), 2),
            "psychological_analysis": calculate_psychological_impact(current_price, cons_price, category) if constraints.psychological_pricing else None
        },
        "recommended": {
            "price": rec_price, 
            "expected_margin": round(margin(rec_price), 2),
            "psychological_analysis": psych_analysis
        },
        "aggressive": {
            "price": aggr_price, 
            "expected_margin": round(margin(aggr_price), 2),
            "psychological_analysis": calculate_psychological_impact(current_price, aggr_price, category) if constraints.psychological_pricing else None
        },
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
        "psychological_analysis": psych_analysis,
        "psychological_pricing_enabled": constraints.psychological_pricing,
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
