from services.core.translator import translate_query
from utils.logger import log


def process_query(query: str) -> dict:
    query = query.strip()
    try:
        english_query = translate_query(query)
    except Exception as e:
        log.warning(f"Translation failed, using original query: {e}")
        english_query = query
    return {
        "original_query": query,
        "english_query": english_query,
        "search_query": english_query,
    }
if __name__ == "__main__":

    examples = [

        "镍基MOF催化剂",

        "nickel catalyst",

        "CO2 reduction",

        "电催化 CO2 reduction"

    ]

    for query in examples:

        print("=" * 50)

        print(

            process_query(

                query

            )

        )