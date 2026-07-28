from datetime import datetime

from services.discovery.collector import collect_all
from services.discovery.interest_ranker import rank_items

from services.config.subscription import load_subscription
from services.templates.paper_card_template import build_paper_card


# ==========================================================
# Build Daily Email
# ==========================================================

def build_daily_email():

    # ------------------------------------------------------
    # User Subscription
    # ------------------------------------------------------

    config = load_subscription()

    keywords = config.get("keywords", [])

    top_k = config.get("top_k", 10)

    # ------------------------------------------------------
    # Collect Latest RSS Papers
    # ------------------------------------------------------

    papers = collect_all(limit=20)

    print("=" * 80)
    print(f"Collected RSS Papers : {len(papers)}")
    print("=" * 80)

    # ------------------------------------------------------
    # Interest Ranking
    # ------------------------------------------------------

    papers = rank_items(

        papers,

        keywords

    )

    papers = papers[:top_k]

    # ------------------------------------------------------
    # HTML Header
    # ------------------------------------------------------

    today = datetime.now().strftime("%Y-%m-%d")

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>ChemVigil Daily Recommendation</title>

<style>

body{{
    margin:0;
    padding:40px;
    background:#f5f7fb;
    font-family:Arial,sans-serif;
}}

.container{{
    width:900px;
    margin:auto;
}}

.header{{
    background:white;
    border-radius:18px;
    padding:35px;
    margin-bottom:35px;
    box-shadow:0 5px 20px rgba(0,0,0,.08);
}}

.logo{{
    font-size:46px;
    font-weight:bold;
    color:#2456c3;
}}

.subtitle{{
    color:#666;
    margin-top:8px;
}}

.date{{
    color:#999;
    margin-top:15px;
}}

.paper-card{{
    background:white;
    border-radius:16px;
    padding:28px;
    margin-bottom:28px;
    box-shadow:0 5px 18px rgba(0,0,0,.08);
}}

.paper-card h2{{
    color:#2456c3;
    line-height:1.4;
}}

.paper-card p{{
    line-height:1.8;
}}

.button{{
    display:inline-block;
    margin-top:10px;
    margin-right:10px;
    padding:10px 18px;
    background:#2456c3;
    color:white;
    border-radius:8px;
    text-decoration:none;
}}

.footer{{
    margin-top:50px;
    text-align:center;
    color:#999;
}}

</style>

</head>

<body>

<div class="container">

<div class="header">

<div class="logo">

ChemVigil

</div>

<div class="subtitle">

Intelligent Literature Discovery Platform

</div>

<h2>

📰 Daily Literature Recommendation

</h2>

<div class="date">

Generated on {today}

</div>

</div>

"""

    # ------------------------------------------------------
    # Paper Cards
    # ------------------------------------------------------

    if len(papers) == 0:

        html += """

<div class="paper-card">

<h2>No Papers Today</h2>

<p>

No RSS papers were collected today.

</p>

</div>

"""

    else:

        for paper in papers:

            html += build_paper_card(

                paper

            )

    # ------------------------------------------------------
    # Footer
    # ------------------------------------------------------

    html += """

<div class="footer">

Generated automatically by ChemVigil

</div>

</div>

</body>

</html>

"""

    return html