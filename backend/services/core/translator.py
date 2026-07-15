from deep_translator import GoogleTranslator


def translate_query(query: str) -> str:
    """
    中文 -> 英文
    英文 -> 原样返回
    """

    if not query:

        return ""

    try:

        if query.isascii():

            return query

        result = GoogleTranslator(

            source="auto",

            target="en"

        ).translate(

            query

        )

        return result

    except Exception:

        return query


if __name__ == "__main__":

    print(
        "Input: 镍基MOF催化剂"
    )

    print(
        "Output:",
        translate_query(
            "镍基MOF催化剂"
        )
    )

    print()

    print(
        "Input: nickel catalyst"
    )

    print(
        "Output:",
        translate_query(
            "nickel catalyst"
        )
    )