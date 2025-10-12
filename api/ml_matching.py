from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logger = logging.getLogger(__name__)

# Global model instance (loaded once)
_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or load the sentence transformer model"""
    global _model
    if _model is None:
        from .settings import get_settings
        settings = get_settings()
        
        if not settings.USE_ML_MATCHING:
            raise RuntimeError("ML matching is disabled in settings")
        
        logger.info(f"Loading sentence transformer model: {settings.ML_MODEL_NAME}")
        try:
            # Use configurable model name
            _model = SentenceTransformer(settings.ML_MODEL_NAME)
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
    return _model


def preprocess_text(text: str) -> str:
    """Preprocess text for better embedding quality"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove brand/model numbers that might confuse matching
    # Keep core product descriptive words
    text = re.sub(r'\b[A-Z]{2,}\d+[A-Z]*\b', '', text)  # Remove codes like SG0001, BT0005
    text = re.sub(r'\d{3,}ml\b', 'bottle', text)  # Replace specific volumes with generic term
    text = re.sub(r'\d+\s*ml\b', '', text)  # Remove ml measurements
    text = re.sub(r'\d+\s*cm\b', '', text)  # Remove cm measurements
    
    # Normalize common product terms
    replacements = {
        'incl.': 'including',
        'w/': 'with',
        '&': 'and',
        'stainless steel': 'steel',
        'eco-friendly': 'eco friendly',
        'organic cotton': 'cotton organic',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove extra whitespace and punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


@dataclass
class MLMatchResult:
    product_id: Optional[str]
    score: float
    reason: str
    semantic_score: float
    category_bonus: float
    material_bonus: float
    brand_bonus: float


def extract_features(text: str) -> dict:
    """Extract features from product text"""
    text_lower = text.lower()
    
    # Category features
    categories = {
        'sunglasses': any(word in text_lower for word in ['sunglass', 'eyewear', 'shades', 'glasses']),
        'bottle': any(word in text_lower for word in ['bottle', 'flask', 'thermos', 'canteen', 'tumbler']),
        'notebook': any(word in text_lower for word in ['notebook', 'journal', 'diary', 'notepad']),
        'mug': any(word in text_lower for word in ['mug', 'cup']),
        'towel': 'towel' in text_lower,
        'lunchbox': any(word in text_lower for word in ['lunchbox', 'lunch box', 'bento']),
        'stole': any(word in text_lower for word in ['stole', 'shawl', 'scarf', 'wrap']),
        'cushion': any(word in text_lower for word in ['cushion', 'pillow']),
        'stand': any(word in text_lower for word in ['stand', 'holder', 'dock']),
    }
    
    # Material features
    materials = {
        'wood': any(word in text_lower for word in ['wood', 'wooden', 'bamboo', 'teak']),
        'metal': any(word in text_lower for word in ['metal', 'steel', 'aluminum', 'copper']),
        'fabric': any(word in text_lower for word in ['cotton', 'silk', 'fabric', 'textile']),
        'plastic': any(word in text_lower for word in ['plastic', 'polymer']),
        'glass': 'glass' in text_lower,
        'ceramic': any(word in text_lower for word in ['ceramic', 'porcelain']),
        'cork': 'cork' in text_lower,
    }
    
    return {
        'categories': [cat for cat, present in categories.items() if present],
        'materials': [mat for mat, present in materials.items() if present],
        'has_size': bool(re.search(r'\d+\s*(ml|cm|l|inch|oz)', text_lower)),
        'has_color': bool(re.search(r'\b(red|blue|green|black|white|brown|gray|yellow|pink|purple|orange)\b', text_lower)),
    }


async def ml_match_scraped_to_catalog(
    scraped_title: str,
    scraped_brand: Optional[str],
    catalog: List[Tuple[str, str, str, str]]
) -> MLMatchResult:
    """
    Match scraped item to catalog using ML embeddings and feature engineering.
    
    Args:
        scraped_title: Title of the scraped product
        scraped_brand: Brand of the scraped product (optional)
        catalog: List of tuples (id, name, brand, category)
    
    Returns:
        MLMatchResult with the best match
    """
    if not catalog:
        return MLMatchResult(
            product_id=None,
            score=0.0,
            reason="No catalog items to match against",
            semantic_score=0.0,
            category_bonus=0.0,
            material_bonus=0.0,
            brand_bonus=0.0
        )
    
    try:
        model = get_embedding_model()
    except Exception as e:
        logger.error(f"ML matching failed, falling back to basic matching: {e}")
        # Fall back to simple token matching if ML fails
        return _fallback_match(scraped_title, scraped_brand, catalog)
    
    # Preprocess scraped title
    processed_scraped = preprocess_text(scraped_title)
    scraped_features = extract_features(scraped_title)
    
    # Prepare catalog texts and features
    catalog_texts = []
    catalog_features = []
    catalog_items = []
    
    for pid, name, brand, category in catalog:
        # Combine name and category for better context
        full_text = f"{name} {category}".strip()
        processed_text = preprocess_text(full_text)
        catalog_texts.append(processed_text)
        catalog_features.append(extract_features(f"{name} {category}"))
        catalog_items.append((pid, name, brand, category))
    
    # Generate embeddings
    try:
        # Encode all texts at once for efficiency
        all_texts = [processed_scraped] + catalog_texts
        embeddings = model.encode(all_texts, convert_to_tensor=False)
        
        scraped_embedding = embeddings[0:1]  # First embedding
        catalog_embeddings = embeddings[1:]  # Rest of embeddings
        
        # Calculate semantic similarities
        similarities = cosine_similarity(scraped_embedding, catalog_embeddings)[0]
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return _fallback_match(scraped_title, scraped_brand, catalog)
    
    # Find best match with feature bonuses
    best_match = None
    best_score = 0.0
    best_details = {}
    
    for i, ((pid, name, brand, category), similarity) in enumerate(zip(catalog_items, similarities)):
        catalog_feat = catalog_features[i]
        
        # Base semantic similarity score
        semantic_score = float(similarity)
        
        # Category matching bonus
        category_bonus = 0.0
        if any(cat in catalog_feat['categories'] for cat in scraped_features['categories']):
            category_bonus = 0.25
        
        # Material matching bonus
        material_bonus = 0.0
        if any(mat in catalog_feat['materials'] for mat in scraped_features['materials']):
            material_bonus = 0.15
        
        # Brand matching bonus
        brand_bonus = 0.0
        if scraped_brand and brand and scraped_brand.lower().strip() == brand.lower().strip():
            brand_bonus = 0.20
        
        # Final score
        final_score = semantic_score + category_bonus + material_bonus + brand_bonus
        final_score = min(1.0, final_score)  # Cap at 1.0
        
        if final_score > best_score:
            best_score = final_score
            best_match = pid
            best_details = {
                'semantic_score': semantic_score,
                'category_bonus': category_bonus,
                'material_bonus': material_bonus,
                'brand_bonus': brand_bonus,
                'name': name
            }
    
    # Build reason string
    reason_parts = [f"semantic={best_details.get('semantic_score', 0):.3f}"]
    if best_details.get('category_bonus', 0) > 0:
        reason_parts.append(f"category_match +{best_details['category_bonus']:.2f}")
    if best_details.get('material_bonus', 0) > 0:
        reason_parts.append(f"material_match +{best_details['material_bonus']:.2f}")
    if best_details.get('brand_bonus', 0) > 0:
        reason_parts.append(f"brand_match +{best_details['brand_bonus']:.2f}")
    
    reason = ", ".join(reason_parts)
    
    # Return match if score is above threshold
    threshold = 0.40  # Lower threshold due to ML confidence
    if best_score >= threshold:
        return MLMatchResult(
            product_id=best_match,
            score=best_score,
            reason=f"ML: {reason} → {best_details.get('name', 'unknown')}",
            semantic_score=best_details.get('semantic_score', 0),
            category_bonus=best_details.get('category_bonus', 0),
            material_bonus=best_details.get('material_bonus', 0),
            brand_bonus=best_details.get('brand_bonus', 0)
        )
    
    return MLMatchResult(
        product_id=None,
        score=best_score,
        reason=f"ML: {reason}, score {best_score:.3f} below threshold {threshold}",
        semantic_score=best_details.get('semantic_score', 0),
        category_bonus=best_details.get('category_bonus', 0),
        material_bonus=best_details.get('material_bonus', 0),
        brand_bonus=best_details.get('brand_bonus', 0)
    )


def _fallback_match(scraped_title: str, scraped_brand: Optional[str], catalog: List[Tuple[str, str, str, str]]) -> MLMatchResult:
    """Fallback to simple token matching if ML fails"""
    from .matching import match_scraped_to_catalog, MatchResult
    
    # Use the existing token-based matcher as fallback
    result = match_scraped_to_catalog(scraped_title, scraped_brand, catalog)
    
    return MLMatchResult(
        product_id=result.product_id,
        score=result.score,
        reason=f"Fallback: {result.reason}",
        semantic_score=0.0,
        category_bonus=0.0,
        material_bonus=0.0,
        brand_bonus=0.0
    )