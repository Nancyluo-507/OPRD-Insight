"""
Embedding 语义匹配引擎

两层语义匹配：
1. 概念向量匹配（轻量，基于语义词典构建概念空间）
2. 可选：sentence-transformers 向量匹配（需安装）

概念向量方案：
- 从 SEMANTIC_DICT 构建 50+ 维的概念空间
- 查询和论文文本都映射到概念空间
- 计算余弦相似度
- 自动处理同义词、上下位关系
"""
import re
import numpy as np
from typing import List, Optional, Tuple


# ==========================================================
# 概念向量引擎
# ==========================================================

class ConceptVectorEngine:
    def __init__(self):
        self.concepts = []
        self.concept_terms = []
        from services.core.semantic_match import SEMANTIC_DICT
        self._dict = SEMANTIC_DICT
        self._build_concept_space()

    def _build_concept_space(self):
        """从语义词典构建概念空间"""
        for concept, terms in self._dict.items():
            # 每个概念是一组相关词
            all_terms = set()
            all_terms.add(concept)
            for t in terms:
                all_terms.add(t)
            self.concepts.append(concept)
            self.concept_terms.append(all_terms)

        # 添加一些跨概念关联
        self._add_cross_concepts()

    def _add_cross_concepts(self):
        """添加跨概念关联（如 catalyst 与 metal 同现）"""
        cross_pairs = [
            ("catalyst", "catalysis"),
            ("catalyst", "catalytic"),
            ("nickel", "cobalt"),
            ("mof", "porous"),
            ("co2", "carbon dioxide"),
            ("enzyme", "biocatalysis"),
            ("nmr", "mass spectrometry"),
            ("drug discovery", "screening"),
            ("graphene", "carbon nanotube"),
        ]
        existing = {c: i for i, c in enumerate(self.concepts)}

        # 将每个概念映射到其相关概念（用于软匹配）
        self.concept_relations = {i: [] for i in range(len(self.concepts))}
        for c1, c2 in cross_pairs:
            i1 = existing.get(c1)
            i2 = existing.get(c2)
            if i1 is not None and i2 is not None:
                self.concept_relations[i1].append(i2)
                self.concept_relations[i2].append(i1)

    def text_to_vector(self, text: str) -> np.ndarray:
        """将文本映射到概念空间向量"""
        from services.core.semantic_match import normalize, keyword_matches

        if not text:
            return np.zeros(len(self.concepts))

        norm_text = normalize(text)
        words = set(norm_text.split())
        vector = np.zeros(len(self.concepts))

        for i, term_set in enumerate(self.concept_terms):
            score = 0.0
            for term in term_set:
                norm_term = normalize(term)
                # 精确匹配
                if keyword_matches(norm_text, norm_term):
                    score += 1.0
                # 部分匹配（多个词的概念，如 "metal organic framework"）
                elif len(norm_term.split()) > 1:
                    term_words = set(norm_term.split())
                    overlap = len(words & term_words)
                    if overlap >= 2:  # 至少匹配2个词
                        score += 0.7
                # 词根匹配（如 catalyst -> catalysis, catalytic）
                elif self._stem_match(norm_text, norm_term):
                    score += 0.5

            if score > 0:
                vector[i] = min(score, 3.0)

        # 添加跨概念传播（软匹配）
        for i in range(len(self.concepts)):
            if vector[i] > 0:
                for rel_i in self.concept_relations.get(i, []):
                    vector[rel_i] = max(vector[rel_i], vector[i] * 0.4)

        return vector

    def _stem_match(self, text: str, term: str) -> bool:
        """词根匹配（如 catalysis 匹配 catalytic）"""
        if len(term) <= 3:
            return False
        # 取前4个字符作为词根
        stem = term[:4]
        return bool(re.search(r'(^|[^a-z])' + re.escape(stem) + r'[a-z]{0,6}($|[^a-z])', text))

    def cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def score(self, query: str, title: str, abstract: str = "") -> float:
        """计算查询与论文的语义相似度（0~100）"""
        q_vec = self.text_to_vector(query + " " + _extract_key_terms(query))
        t_vec = self.text_to_vector(title)
        a_vec = self.text_to_vector(abstract) if abstract else np.zeros(len(self.concepts))

        title_sim = self.cosine_similarity(q_vec, t_vec)
        abstract_sim = self.cosine_similarity(q_vec, a_vec) if abstract else 0

        # 加权：标题70%，摘要30%
        combined = title_sim * 70 + abstract_sim * 30
        return round(combined, 1)


# ==========================================================
# sentence-transformers 后端（可选安装）
# ==========================================================

class TransformerEmbedding:
    """sentence-transformers 包装器，如果安装了的话"""

    def __init__(self):
        self._model = None
        self._available = False
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        self._try_load()

    def _try_load(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._available = True
            print("[Embedding] sentence-transformers loaded (384-dim)")
        except ImportError:
            self._available = False

    def encode(self, text: str) -> np.ndarray:
        if not self._available or not self._model:
            return np.array([])
        return self._model.encode(text, normalize_embeddings=True)

    def similarity(self, q_emb: np.ndarray, text_emb: np.ndarray) -> float:
        if q_emb.size == 0 or text_emb.size == 0:
            return 0.0
        return float(np.dot(q_emb, text_emb))


def _extract_key_terms(text: str) -> str:
    """提取关键词用于增强向量"""
    from services.core.semantic_match import normalize
    words = normalize(text).split()
    return " ".join(words[:5])


# ==========================================================
# 统一语义匹配接口
# ==========================================================

_concept_engine: Optional[ConceptVectorEngine] = None
_transformer: Optional[TransformerEmbedding] = None
_query_emb_cache: dict = {"query": None, "emb": None}


def _get_concept_engine() -> ConceptVectorEngine:
    global _concept_engine
    if _concept_engine is None:
        _concept_engine = ConceptVectorEngine()
    return _concept_engine


def _get_transformer() -> TransformerEmbedding:
    global _transformer
    if _transformer is None:
        _transformer = TransformerEmbedding()
    return _transformer


def embedding_score(
    query: str,
    title: str,
    abstract: str = "",
    use_transformer: bool = False,
) -> float:
    """
    语义匹配评分（0~100）

    Args:
        query: 查询关键词
        title: 论文标题
        abstract: 论文摘要
        use_transformer: 是否使用 transformers（需安装）

    Returns:
        语义相似度分数
    """
    engine = _get_concept_engine()

    if use_transformer:
        tf = _get_transformer()
        if tf._available:
            global _query_emb_cache
            if _query_emb_cache["query"] != query:
                _query_emb_cache["query"] = query
                _query_emb_cache["emb"] = tf.encode(query)
            q_emb = _query_emb_cache["emb"]
            t_emb = tf.encode(title)
            a_emb = tf.encode(abstract) if abstract else np.array([])

            title_score = tf.similarity(q_emb, t_emb) * 70
            abstract_score = tf.similarity(q_emb, a_emb) * 30 if abstract else 0
            return round(title_score + abstract_score, 1)

    # 默认：概念向量匹配
    return engine.score(query, title, abstract)


# ==========================================================
# Test
# ==========================================================
if __name__ == "__main__":
    print("=== 概念向量匹配测试 ===\n")

    engine = ConceptVectorEngine()
    print(f"概念空间维度: {len(engine.concepts)}")
    print(f"概念: {engine.concepts[:10]}...\n")

    tests = [
        ("nickel catalyst", "Nickel single atom catalyst for CO2 reduction"),
        ("nickel catalyst", "Feminist studies on Catalyst Lead Editing"),
        ("mof co2", "Metal-organic framework derived porous carbon for CO2 capture"),
        ("mof co2", "Machine learning for protein structure prediction"),
        ("enzyme catalysis", "Enzymatic synthesis of chiral pharmaceutical intermediates"),
        ("enzyme catalysis", "Blockchain technology for supply chain management"),
        ("cross-coupling", "Palladium-catalyzed cross-coupling reaction for biaryl synthesis"),
        ("cross-coupling", "Quantum computing advances in cryptography"),
    ]

    for query, title in tests:
        score = engine.score(query, title, "")
        print(f"Query: '{query}'")
        print(f"Title: {title[:50]}...")
        print(f"Score: {score}")
        print()
