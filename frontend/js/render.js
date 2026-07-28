// =====================================
// render.js
// =====================================

import { saveUserArticle } from "./api.js";

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

let _userId = null;
let _favDois = new Set();

export function setFavorites(userId, favDois) {
    _userId = userId;
    _favDois = new Set(favDois || []);
}

export function renderPaperCard(paper){

    const card=document.createElement("div");

    card.className="paper-card";

    const isFav = _favDois.has(paper.doi);
    const starChar = isFav ? "★" : "☆";

    const keywordHTML=buildKeywordHTML(

        paper.keywords

    );

    const abstractHTML = buildAbstractHTML(

        paper

    );

    card.innerHTML=`
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <h2 style="flex:1;">

            ${paper.title||""}

            </h2>
            <span class="star-btn" data-doi="${paper.doi || ""}" style="font-size:20px;cursor:pointer;user-select:none;line-height:1;margin-left:12px;color:${isFav ? "#f59e0b" : "#94a3b8"};">${starChar}</span>
        </div>

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

    const starEl = card.querySelector(".star-btn");
    if (starEl) {
        starEl.addEventListener("click", async () => {
            const doi = starEl.dataset.doi;
            if (!doi) return;
            if (!_userId) return;
            const isFav = _favDois.has(doi);
            try {
                const data = await saveUserArticle(_userId, doi, !isFav, paper.title);
                if (data.is_favorite) {
                    starEl.style.color = "#f59e0b";
                    starEl.textContent = "★";
                    _favDois.add(doi);
                } else {
                    starEl.style.color = "#94a3b8";
                    starEl.textContent = "☆";
                    _favDois.delete(doi);
                }
            } catch (e) {
                console.error("Favorite toggle failed:", e);
                starEl.textContent = "✗";
                setTimeout(() => { starEl.textContent = isFav ? "★" : "☆"; }, 1500);
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