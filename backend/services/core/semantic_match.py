import re

# ==========================================================
# Chemistry Semantic Dictionary
# ==========================================================

SEMANTIC_DICT = {

    "nickel": [

        "nickel",

        "ni",

        "nickel-based",

        "ni-based"

    ],

    "mof": [

        "mof",

        "mofs",

        "metal organic framework",

        "metal-organic framework"

    ],

    "co2": [

        "co2",

        "co₂",

        "carbon dioxide",

        "co2 reduction",

        "carbon dioxide reduction",

        "co2rr"

    ],

    "her": [

        "her",

        "hydrogen evolution reaction"

    ],

    "oer": [

        "oer",

        "oxygen evolution reaction"

    ],

    "orr": [

        "orr",

        "oxygen reduction reaction"

    ]

}


# ==========================================================
# Normalize
# ==========================================================

def normalize(

    text: str

) -> str:

    text = text.lower()

    text = re.sub(

        r"\s+",

        " ",

        text

    )

    return text.strip()
# ==========================================================
# Expand One Keyword
# ==========================================================

def expand_keyword(

    keyword: str

):

    keyword = normalize(

        keyword

    )

    if keyword in SEMANTIC_DICT:

        return SEMANTIC_DICT[

            keyword

        ]

    return [

        keyword

    ]


# ==========================================================
# Expand Query
# ==========================================================

def expand_query(

    query: str

):

    result = []

    words = normalize(

        query

    ).split()

    for word in words:

        result.extend(

            expand_keyword(

                word

            )

        )

    return list(

        dict.fromkeys(

            result

        )

    )
# ==========================================================
# Semantic Match
# ==========================================================

def semantic_match(

    query: str,

    text: str

):

    text = normalize(

        text

    )

    matched = []

    keywords = expand_query(

        query

    )

    for keyword in keywords:

        if keyword in text:

            matched.append(

                keyword

            )

    return matched


if __name__ == "__main__":

    text = """

    Nickel single atom catalyst
    derived from metal organic framework
    exhibits excellent CO2 reduction.

    """

    print()

    print(

        "Expanded Keywords:"

    )

    for item in expand_query(

        "nickel MOF CO2"

    ):

        print(

            "-",

            item

        )

    print()

    print(

        "Matched:"

    )

    print(

        semantic_match(

            "nickel MOF CO2",

            text

        )

    )