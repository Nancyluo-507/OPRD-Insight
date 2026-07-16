// =====================================
// render.js
// =====================================

function buildKeywordHTML(keywords){

    if(!keywords || keywords.length===0){

        return "";

    }

    return `

        <p class="keyword-line">

            <b>🏷️ Keywords：</b>

            <span class="keyword-list">

                ${keywords
                    .slice(0,4)
                    .map(
                        keyword=>`<span class="keyword-tag">${keyword}</span>`
                    )
                    .join("")}

                ${
                    keywords.length>4
                    ? `<span class="keyword-more">+${keywords.length-4}</span>`
                    : ""
                }

            </span>

        </p>

    `;

}

function buildAbstractHTML(paper){

    let abstract="";

    if(paper.highlighted_abstract){

        abstract=paper.highlighted_abstract;

    }

    else{

        abstract=paper.abstract||"";

    }

    if(!abstract){

        return "";

    }

    abstract=abstract.replace(

        /<mark>(.*?)<\/mark>/gi,

        '<span class="keyword-highlight">$1</span>'

    );

    const needCollapse=abstract.length>350;

    const shortHTML=

        needCollapse

        ? abstract.substring(0,350)+"..."

        : abstract;

    return `

        <p class="abstract-line">

            <b>📝 Abstract：</b>

            <span class="abstract-text">

                ${shortHTML}

            </span>

            ${
                needCollapse

                ? `<span class="read-more">Read More</span>`

                : ""

            }

        </p>

    `;

}

export function renderPaperCard(paper){

    const card=document.createElement("div");

    card.className="paper-card";

    const keywordHTML=buildKeywordHTML(

        paper.keywords

    );

    let abstract = paper.highlighted_abstract || paper.abstract || "";

    abstract = abstract.replace(

        /<mark>(.*?)<\/mark>/gi,

        '<span class="keyword-highlight">$1</span>'

);

    const abstractHTML = buildAbstractHTML(

        paper

    );

    card.innerHTML=`

        <h2>

            ${paper.title||""}

        </h2>

        <p>

            <b>👤 Authors：</b>

            ${paper.authors||"-"}

        </p>

        <p>

            <b>📖 Journal：</b>

            ${paper.journal||"-"}

            &nbsp;&nbsp;&nbsp;

            <b>📅 Year：</b>

            ${paper.year||"-"}

        </p>

        <p>

            <b>🏢 Publisher：</b>

            ${paper.publisher||"-"}

        </p>

        <p>

            ${
                paper.is_open_access
                ? "🟢 <b>Open Access</b>"
                : "🔒 <b>Closed Access</b>"
            }

        </p>

        ${keywordHTML}

        ${abstractHTML}
        <p>

            💬 <b>Citations：</b>

            ${paper.citation || 0}

        </p>

        <div class="links">

            ${
                paper.doi_url
                ? `<a href="${paper.doi_url}" target="_blank">DOI</a>`
                : ""
            }

            ${
                paper.pdf_url
                ? `<a href="${paper.pdf_url}" target="_blank">PDF</a>`
                : ""
            }

        </div>

    `;

    //--------------------------------------------------
    // Read More
    //--------------------------------------------------

    const readMore = card.querySelector(".read-more");

if(readMore){

    const abstractText = card.querySelector(".abstract-text");

    const fullHTML = abstract;

    const shortHTML =

        abstract.length > 350

        ? abstract.substring(0,350) + "..."

        : abstract;

    let expanded = false;

    readMore.addEventListener("click",()=>{

        expanded = !expanded;

        if(expanded){

            abstractText.innerHTML = fullHTML;

            readMore.textContent = "Show Less";

        }

        else{

            abstractText.innerHTML = shortHTML;

            readMore.textContent = "Read More";

        }

    });

}

    return card;

}

// =====================================
// Render Results
// =====================================

export function renderResults(container,papers){

    container.innerHTML="";

    if(!papers || papers.length===0){

        container.innerHTML=`

            <div class="paper-card">

                <h2>没有找到文献</h2>

            </div>

        `;

        return;

    }

    papers.forEach(paper=>{

        container.appendChild(

            renderPaperCard(paper)

        );

    });

}