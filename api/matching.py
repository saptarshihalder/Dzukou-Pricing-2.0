from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple


# Common synonyms and normalizations for product matching
CATEGORY_KEYWORDS = {
    "sunglasses": ["sunglass", "sunglasses", "eyewear", "shades", "glasses"],
    "bottle": ["bottle", "bottles", "flask", "thermos", "canteen", "container"],
    "notebook": ["notebook", "notebooks", "journal", "journals", "notepad", "notepads"],
    "mug": ["mug", "mugs", "cup", "cups"],
    "stand": ["stand", "holder", "dock"],
    "lunchbox": ["lunchbox", "lunch box", "bento", "food container"],
    "stole": ["stole", "stoles", "shawl", "shawls", "scarf", "scarves", "wrap"],
    "cushion": ["cushion", "cushions", "pillow", "pillows"],
    "towel": ["towel", "towels"],
}

# Material keywords
MATERIALS = ["wood", "wooden", "bamboo", "cork", "silk", "cotton", "metal", "plastic", "glass", "stainless"]


def normalize(text: str) -> list[str]:
    """Normalize text to lowercase tokens, removing special characters"""
    t = text.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    tokens = [tok for tok in t.split() if tok and len(tok) > 1]  # Filter out single-char tokens
    return tokens


def extract_category_keywords(tokens: list[str]) -> set[str]:
    """Extract category-related keywords from tokens"""
    found = set()
    for token in tokens:
        for category, keywords in CATEGORY_KEYWORDS.items():
            if token in keywords:
                found.add(category)
                found.update(keywords)
    return found


def extract_materials(tokens: list[str]) -> set[str]:
    """Extract material keywords from tokens"""
    return {tok for tok in tokens if tok in MATERIALS}


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    """Calculate Jaccard similarity between two sets"""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def token_overlap_score(a: list[str], b: list[str]) -> float:
    """Calculate a more forgiving overlap score"""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    
    # Count matching tokens
    matches = len(sa & sb)
    # Use the smaller set size as denominator for more lenient matching
    smaller_size = min(len(sa), len(sb))
    
    return matches / smaller_size if smaller_size > 0 else 0.0


@dataclass
class MatchResult:
    product_id: Optional[str]
    score: float
    reason: str


def match_scraped_to_catalog(
    scraped_title: str, 
    scraped_brand: Optional[str], 
    catalog: list[tuple[str, str, str, str]]
) -> MatchResult:
    """Match scraped item to catalog using improved fuzzy matching.

    catalog: list of tuples (id, name, brand, category)
    
    Matching strategy:
    1. Token overlap score (more forgiving than Jaccard)
    2. Category keyword matching
    3. Material keyword matching
    4. Brand matching bonus
    """
    s_toks = normalize(scraped_title)
    s_categories = extract_category_keywords(s_toks)
    s_materials = extract_materials(s_toks)
    
    best: Tuple[str, float, str] | None = None
    
    for pid, name, brand, category in catalog:
        n_toks = normalize(name)
        c_toks = normalize(category)
        
        # Base similarity using token overlap (more forgiving than Jaccard)
        token_score = token_overlap_score(s_toks, n_toks)
        
        # Category matching
        n_categories = extract_category_keywords(n_toks)
        n_categories.update(extract_category_keywords(c_toks))
        category_match = len(s_categories & n_categories) > 0 if s_categories and n_categories else False
        
        # Material matching
        n_materials = extract_materials(n_toks)
        material_match = len(s_materials & n_materials) > 0 if s_materials and n_materials else False
        
        # Build score
        score = token_score
        reason_bits = [f"token_overlap={token_score:.2f}"]
        
        # Category bonus (strong signal)
        if category_match:
            score += 0.25
            reason_bits.append(f"category_match +0.25")
        
        # Material bonus
        if material_match:
            score += 0.10
            reason_bits.append(f"material_match +0.10")
        
        # Brand bonus
        if scraped_brand and brand and scraped_brand.lower() == brand.lower():
            score += 0.15
            reason_bits.append("brand_match +0.15")
        
        # Cap at 1.0
        score = min(1.0, score)
        
        if best is None or score > best[1]:
            best = (pid, score, ", ".join(reason_bits))
    
    # Lower threshold to 0.35 to capture more matches with category/material signals
    if best and best[1] >= 0.35:
        return MatchResult(product_id=best[0], score=best[1], reason=best[2])
    
    return MatchResult(
        product_id=None, 
        score=best[1] if best else 0.0, 
        reason=(best[2] if best else "no candidates, score too low")
    )
