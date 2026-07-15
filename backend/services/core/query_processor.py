from services.core.translator import translate_query


def process_query(query: str) -> dict:
    """
    查询预处理

    输入：
        中文
        英文
        中英混合

    输出：
        {
            original_query,
            english_query,
            search_query
        }
    """

    query = query.strip()

    english_query = translate_query(
        query
    )

    result = {

        "original_query": query,

        "english_query": english_query,

        "search_query": english_query

    }

    return result
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