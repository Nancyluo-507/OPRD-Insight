from html import escape

from services.models.rss_paper import RSSPaper


# ==========================================================
# Helpers
# ==========================================================

def text(value):

    if value is None:
        return ""

    return escape(str(value))


# ==========================================================
# Build RSS Paper Card
# ==========================================================

def build_paper_card(
    paper: RSSPaper
) -> str:

    html = """
<div class="paper-card">
"""

    # ------------------------------------------------------
    # Title
    # ------------------------------------------------------

    html += f"""
<h2>{text(paper.title)}</h2>
"""

    # ------------------------------------------------------
    # Published
    # ------------------------------------------------------

    if paper.published:

        html += f"""
<p>

<b>📅 Published</b><br>

{text(paper.published)}

</p>
"""

    # ------------------------------------------------------
    # Source
    # ------------------------------------------------------

    if paper.source:

        html += f"""
<p>

<b>🌍 Source</b><br>

{text(paper.source)}

</p>
"""

    # ------------------------------------------------------
    # Authors
    # ------------------------------------------------------

    if paper.authors:

        html += f"""
<p>

<b>👤 Authors</b><br>

{text(", ".join(paper.authors))}

</p>
"""

    # ------------------------------------------------------
    # Journal
    # ------------------------------------------------------

    if paper.journal:

        html += f"""
<p>

<b>📚 Journal</b><br>

{text(paper.journal)}

</p>
"""

    # ------------------------------------------------------
    # Publisher
    # ------------------------------------------------------

    if paper.publisher:

        html += f"""
<p>

<b>🏢 Publisher</b><br>

{text(paper.publisher)}

</p>
"""

    # ------------------------------------------------------
    # Keywords
    # ------------------------------------------------------

    if paper.keywords:

        html += f"""
<p>

<b>🏷 Keywords</b><br>

{text(", ".join(paper.keywords))}

</p>
"""

    # ------------------------------------------------------
    # Subjects
    # ------------------------------------------------------

    if paper.subjects:

        html += f"""
<p>

<b>🧪 Subjects</b><br>

{text(", ".join(paper.subjects))}

</p>
"""

    # ------------------------------------------------------
    # Abstract
    # ------------------------------------------------------

    if paper.abstract:

        html += f"""
<p>

<b>📄 Abstract</b><br>

{text(paper.abstract)}

</p>
"""

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    elif paper.summary:

        html += f"""
<p>

<b>📝 Summary</b><br>

{text(paper.summary)}

</p>
"""

    # ------------------------------------------------------
    # Buttons
    # ------------------------------------------------------

    html += "<p>"

    if paper.url:

        html += f"""
<a
class="button"
href="{paper.url}"
target="_blank">

🔗 Read Original

</a>
"""

    if paper.doi:

        html += f"""
<a
class="button"
href="https://doi.org/{paper.doi}"
target="_blank">

DOI

</a>
"""

    html += "</p>"

    html += """

</div>

"""

    return html