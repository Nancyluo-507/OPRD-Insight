import re

SEMANTIC_DICT = {
    "nickel": ["nickel", "ni", "nickel-based", "ni-based"],
    "mof": ["mof", "mofs", "metal organic framework", "metal-organic framework"],
    "co2": ["co2", "co₂", "carbon dioxide", "co2 reduction", "carbon dioxide reduction", "co2rr", "co2rr"],
    "her": ["her", "hydrogen evolution reaction"],
    "oer": ["oer", "oxygen evolution reaction"],
    "orr": ["orr", "oxygen reduction reaction"],
}

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def expand_keyword(keyword: str):
    keyword = normalize(keyword)
    if keyword in SEMANTIC_DICT:
        return SEMANTIC_DICT[keyword]
    return [keyword]

def expand_query(query: str):
    result = []
    words = normalize(query).split()
    for word in words:
        result.extend(expand_keyword(word))
    return list(dict.fromkeys(result))

# ==========================================================
# Word-level matching (not substring)
# ==========================================================

def word_in_text(word: str, text: str) -> bool:
    """Check if word/phrase appears as a whole word in text."""
    pattern = re.escape(word) + (r"\b" if re.match(r"^[a-z0-9]+$", word) else "")
    if len(word.split()) > 1:
        pattern = re.escape(word)
    return bool(re.search(pattern, text))

def stem_match(word: str, text: str) -> bool:
    """Stem-based match: 'catalyst' matches 'catalysis', 'catalytic'."""
    if len(word) <= 4:
        return False
    stem = word[:4]
    return bool(re.search(r'(?<![a-z])' + re.escape(stem) + r'[a-z]{0,6}(?![a-z])', text))

# ==========================================================
# Keyword matching with partial scores
# ==========================================================

def match_keyword(keyword: str, text: str) -> float:
    """
    Match a single keyword against text, return score 0.0~1.0.
    1.0 = exact whole-word match
    0.7 = stem match (catalyst ~ catalytic)
    0.0 = no match
    """
    if word_in_text(keyword, text):
        return 1.0
    if len(keyword.split()) == 1 and stem_match(keyword, text):
        return 0.7
    return 0.0

# ==========================================================
# Field-weighted semantic matching
# ==========================================================

_SUB_WORDS = {"a", "an", "the", "of", "in", "for", "and", "or", "to", "with", "on", "at", "by", "from", "as", "is", "are", "was", "were"}

def _count_content_words(text: str) -> int:
    words = normalize(text).split()
    return sum(1 for w in words if w not in _SUB_WORDS)

def semantic_match(query: str, text: str):
    """Return list of matched keywords (for backward compatibility)."""
    text_norm = normalize(text)
    matched = []
    keywords = expand_query(query)
    for keyword in keywords:
        if match_keyword(keyword, text_norm) >= 0.7:
            matched.append(keyword)
    return matched

# ==========================================================
# Main matching function used by job_worker
# ==========================================================

def _expand_grouped(keywords_text: str) -> tuple:
    """
    Expand keywords while tracking original groupings.
    Returns (original_keywords_list, grouped_expanded: list of lists)
    """
    original = normalize(keywords_text).split()
    grouped = []
    for word in original:
        expanded = expand_keyword(word)
        grouped.append(expanded)
    return original, grouped


def match_topic(keywords_text: str, title: str, abstract: str = "") -> tuple:
    """
    Improved topic matching with weighted field scoring.
    
    Scoring:
    - Each original keyword contributes max 1.0 across its expanded synonyms
    - Title: 60%, Abstract: 40%
    - Score is 0~100
    
    Returns:
        (matched_keywords_list, combined_score)
    """
    original_keywords, grouped_expanded = _expand_grouped(keywords_text)
    if not original_keywords:
        return [], 0.0

    title_norm = normalize(title)
    abstract_norm = normalize(abstract) if abstract else ""
    n = len(original_keywords)

    def _score_field(text_norm):
        """Score one field: return (matched_list, total_score)."""
        field_matched = []
        field_score = 0.0
        for group in grouped_expanded:
            best = 0.0
            best_kw = None
            for kw in group:
                s = match_keyword(kw, text_norm)
                if s > best:
                    best = s
                    best_kw = kw
            if best >= 0.7 and best_kw:
                field_matched.append(best_kw)
            field_score += best
        return field_matched, field_score / max(n, 1)

    title_matched, title_pct = _score_field(title_norm)
    abstract_matched, abstract_pct = _score_field(abstract_norm) if abstract_norm else ([], 0.0)

    combined_score = title_pct * 60 + abstract_pct * 40
    if combined_score <= 0:
        return [], 0.0

    all_matched = list(dict.fromkeys(title_matched + abstract_matched))
    return all_matched, round(combined_score, 1)


# ==========================================================
# Enhanced matching with embedding signal
# ==========================================================

def match_topic_enhanced(keywords_text: str, title: str, abstract: str = "") -> tuple:
    """
    Enhanced matching: keyword match + embedding semantic signal.
    
    Returns:
        (matched_keywords_list, combined_score)
    
    Score = keyword_match * 0.7 + embedding_similarity * 0.3
    """
    kw_list, kw_score = match_topic(keywords_text, title, abstract)
    
    try:
        from services.core.embedding_match import embedding_score
        emb_score = embedding_score(keywords_text, title, abstract)
        # Normalize embedding score (0~100) to 0~1 scale and combine
        combined = kw_score * 0.7 + emb_score * 0.3
        return kw_list, round(combined, 1)
    except ImportError:
        return kw_list, kw_score


if __name__ == "__main__":
    # Test cases
    tests = [
        ("nickel mof co2", "Nickel single atom catalyst derived from metal organic framework exhibits excellent CO2 reduction", 
         "We report a Ni-based MOF catalyst for electrochemical CO2 reduction reaction with high faradaic efficiency."),
        ("nickel mof co2", "Feminist studies on Catalyst Lead Editing in Modern Literature",
         "This paper reviews gender perspectives in contemporary literary criticism."),
        ("nickel mof co2", "Machine learning for protein structure prediction", ""),
        ("her oer", "Hydrogen evolution reaction on platinum surfaces",
         "The oxygen evolution reaction kinetics were studied using DFT calculations."),
        ("cross-coupling", "Palladium-catalyzed cross-coupling reaction for biaryl synthesis",
         "Suzuki-Miyaura coupling enables efficient construction of carbon-carbon bonds."),
        ("enzyme biocatalysis", "Enzymatic synthesis of chiral pharmaceutical intermediates",
         "Biocatalytic routes offer green alternatives for asymmetric synthesis."),
    ]

    for keywords, title, abstract in tests:
        kw, score = match_topic(keywords, title, abstract)
        kw_e, score_e = match_topic_enhanced(keywords, title, abstract)
        print(f"Keywords: {keywords}")
        print(f"Title: {title[:60]}...")
        print(f"  Basic match:     score={score}, kw={kw}")
        print(f"  Enhanced match:  score={score_e}, kw={kw_e}")
        print()
