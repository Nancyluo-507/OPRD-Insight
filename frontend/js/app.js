import { searchPaper } from "./api.js";
import { renderResults } from "./render.js";

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
    function(e){

        if(e.key==="Enter"){

            startSearch();

        }

    }

);

// ================================
// Search
// ================================

async function startSearch(){

    const keyword = keywordInput.value.trim();

    if(keyword===""){

        alert("请输入关键词");

        return;

    }

    loading.innerHTML = "<h2>Searching...</h2>";

    results.innerHTML = "";

    searchBtn.disabled = true;

    searchBtn.innerText = "Searching...";

    try{

        const data = await searchPaper(keyword);

        loading.innerHTML = "";

        renderResults(

            results,

            data.results

        );

    }

    catch(err){

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