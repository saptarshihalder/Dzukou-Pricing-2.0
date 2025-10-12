"""LLM integration for enhanced pricing insights using Ollama."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from ollama import AsyncClient, ResponseError
from tenacity import retry, stop_after_attempt, wait_exponential

from .settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MarketInsight:
    """Market insight from LLM analysis."""
    demand_elasticity: float  # -2.0 to 2.0, negative = elastic
    brand_positioning: str   # "value" | "competitive" | "premium" | "luxury"
    market_saturation: str   # "low" | "medium" | "high"
    seasonal_factor: float   # 0.5 to 2.0, 1.0 = neutral
    confidence: float        # 0.0 to 1.0
    reasoning: str


@dataclass
class PricingContext:
    """Context for LLM pricing analysis."""
    product_name: str
    category: str
    brand: str
    current_price: float
    unit_cost: float
    competitor_prices: list[float]
    market_position: str  # "below" | "competitive" | "above"


class OllamaLLMProvider:
    """Ollama integration for pricing insights."""
    
    def __init__(self, host: str, model: str):
        self.client = AsyncClient(host=host)
        self.model = model
    
    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def get_market_insight(self, context: PricingContext) -> Optional[MarketInsight]:
        """Get market insight from Ollama for pricing context."""
        try:
            prompt = self._build_prompt(context)
            
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ],
                options={
                    'temperature': 0.1,
                    'num_predict': 512,  # Limit tokens for JSON response
                }
            )
            
            logger.debug(f"Ollama response: {response}")
            
            content = response.message.content
            if not content:
                logger.error("Empty content received from Ollama")
                return None
                
            return self._parse_response(content)
                
        except ResponseError as e:
            logger.error(f"Ollama API error: {e.error}")
            if e.status_code == 404:
                logger.error(f"Model '{self.model}' not found. Please run: ollama pull {self.model}")
            return None
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}", exc_info=True)
            return None
    
    def _build_prompt(self, context: PricingContext) -> str:
        """Build prompt for Ollama."""
        comp_summary = ""
        if context.competitor_prices:
            comp_min = min(context.competitor_prices)
            comp_max = max(context.competitor_prices)
            comp_avg = sum(context.competitor_prices) / len(context.competitor_prices)
            comp_summary = f"Competitor prices: €{comp_min:.2f} - €{comp_max:.2f} (avg: €{comp_avg:.2f})"
        else:
            comp_summary = "No competitor pricing data available"
        
        margin = ((context.current_price - context.unit_cost) / context.current_price * 100) if context.current_price > 0 else 0
        
        return f"""You are a pricing analyst for sustainable/eco products. Analyze this product and provide insights in JSON format only.

Product: {context.product_name} ({context.category}, {context.brand})
Current Price: €{context.current_price:.2f}
Unit Cost: €{context.unit_cost:.2f}
Current Margin: {margin:.1f}%
Market Position: {context.market_position}
{comp_summary}

Respond with valid JSON only (no markdown, no explanations):
{{
  "demand_elasticity": -0.8,
  "brand_positioning": "premium",
  "market_saturation": "medium", 
  "seasonal_factor": 1.0,
  "confidence": 0.85,
  "reasoning": "Brief one sentence explanation"
}}

Constraints:
- demand_elasticity: number between -2.0 and 2.0 (negative = elastic, positive = inelastic)
- brand_positioning: one of "value", "competitive", "premium", "luxury"
- market_saturation: one of "low", "medium", "high"
- seasonal_factor: number between 0.5 and 2.0 (1.0 = neutral)
- confidence: number between 0.0 and 1.0
- reasoning: short explanation in one sentence"""

    def _parse_response(self, content: str) -> Optional[MarketInsight]:
        """Parse Ollama response into MarketInsight."""
        try:
            # Clean up response content - remove potential markdown formatting
            content = content.strip()
            
            # Handle potential markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            
            # Find JSON object if embedded in text
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                content = content[start:end]
            
            data = json.loads(content)
            
            # Validate and clamp values to expected ranges
            demand_elasticity = max(-2.0, min(2.0, float(data.get("demand_elasticity", 0.0))))
            seasonal_factor = max(0.5, min(2.0, float(data.get("seasonal_factor", 1.0))))
            confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
            
            brand_positioning = data.get("brand_positioning", "competitive")
            if brand_positioning not in ["value", "competitive", "premium", "luxury"]:
                brand_positioning = "competitive"
            
            market_saturation = data.get("market_saturation", "medium")
            if market_saturation not in ["low", "medium", "high"]:
                market_saturation = "medium"
            
            return MarketInsight(
                demand_elasticity=demand_elasticity,
                brand_positioning=brand_positioning,
                market_saturation=market_saturation,
                seasonal_factor=seasonal_factor,
                confidence=confidence,
                reasoning=data.get("reasoning", "No reasoning provided")
            )
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            logger.error(f"Response content: {content}")
            return None


class LLMService:
    """Main LLM service for pricing insights."""
    
    def __init__(self):
        settings = get_settings()
        self.provider = None
        try:
            self.provider = OllamaLLMProvider(settings.OLLAMA_HOST, settings.OLLAMA_MODEL)
            logger.info(f"LLM service initialized with Ollama provider (model: {settings.OLLAMA_MODEL})")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")
            logger.info("Falling back to deterministic pricing")
    
    async def get_market_insight(self, context: PricingContext) -> Optional[MarketInsight]:
        """Get market insight from available LLM provider."""
        if not self.provider:
            return None
        
        try:
            return await self.provider.get_market_insight(context)
        except Exception as e:
            logger.error(f"LLM service error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.provider is not None


# Global LLM service instance
llm_service = LLMService()