import { searchPaper } from "./api.js";

// ================================
// ChemAI Frontend
// ================================

const keywordInput = document.getElementById("keyword");
const searchBtn = document.getElementById("searchBtn");
const results = document.getElementById("results");

// ================================
// Loading
// ================================

let loading = document.getElementById("loading");

if (!loading) {

    loading = document.createElement("div");

    loading.id = "loading";

    results.parentNode.insertBefore(

        loading,

        results

    );

}

// ================================
// Event
// ================================

searchBtn.addEventListener(

    "click",

    startSearch

);

keywordInput.addEventListener(

    "keydown",

    function (e) {

        if (e.key === "Enter") {

            startSearch();

        }

    }

);

// ================================
// Search
// ================================

async function startSearch() {

    const keyword = keywordInput.value.trim();

    if (keyword === "") {

        alert("请输入关键词");

        return;

    }

    loading.innerHTML = "<h2>Searching...</h2>";

    results.innerHTML = "";

    searchBtn.disabled = true;

    searchBtn.innerText = "Searching...";

    try {

        const data = await searchPaper(

            keyword

        );

        console.log(data);

        loading.innerHTML = "";

        showResults(

            data.results

        );

    }

    catch (err) {

        console.error(err);

        loading.innerHTML = "";

        results.innerHTML = `

            <div class="paper-card">

                <h2>❌ 无法连接后端</h2>

                <p>${err}</p>

            </div>

        `;

    }

    searchBtn.disabled = false;

    searchBtn.innerText = "搜索";

}

// ================================
// Show Results
// ================================

function showResults(papers) {

    results.innerHTML = "";

    if (!papers || papers.length === 0) {

        results.innerHTML = `

            <div class="paper-card">

                <h2>没有找到文献</h2>

            </div>

        `;

        return;

    }

    papers.forEach(

        paper => {

            const card = document.createElement(

                "div"

            );

            card.className = "paper-card";

            card.innerHTML = `

                <h2>

                    ${paper.title || ""}

                </h2>

                <p>

                    <b>Score：</b>

                    ${paper.score ?? "-"}

                </p>

                <p>

                    <b>Authors：</b>

                    ${paper.authors || "-"}

                </p>

                <p>

                    <b>Journal：</b>

                    ${paper.journal || "-"}

                </p>

                <p>

                    <b>Year：</b>

                    ${paper.year || "-"}

                </p>

                <p>

                    <b>Citations：</b>

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

            results.appendChild(

                card

            );

        }

    );

}