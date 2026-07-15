from services.translator import translate_query
from services.semantic_match import expand_query


# ============================================================
# Query Understanding Pipeline
# ============================================================

def understand_query(query: str):

    # 原始输入
    original_query = query.strip()

    # 中文翻译
    english_query = translate_query(

        original_query

    )

    # 关键词扩展
    keywords = expand_query(

        english_query

    )

    # 去重
    keywords = list(

        dict.fromkeys(

            keywords

        )

    )

    return {

        "original": original_query,

        "english": english_query,

        "keywords": keywords,

        "search_query": " ".join(

            keywords

        )

    }


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    result = understand_query(

        "镍基金属有机框架催化剂"

    )

    print(result)