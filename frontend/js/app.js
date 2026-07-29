import { searchPaper, listFavorites } from "./api.js";

import { setFavorites } from "./render.js";


import {

    setPapers

}

from "./pagination.js";


import {

    initPagination,

    renderCurrentPage

}

from "./pagination_controller.js";

import { getUserId, isLoggedIn } from "./auth.js";

// ================================
// ChemVigil Frontend
// ================================


const keywordInput =
    document.getElementById("keyword");



const searchBtn =
    document.getElementById("searchBtn");


const results =
    document.getElementById("results");



// ================================
// Loading
// ================================


let loading =
    document.getElementById("loading");




// ================================
// User & Favorites
// ================================

let _appUserId = null;

(async function initApp() {
    if (!isLoggedIn()) return;
    _appUserId = getUserId();
    try {
        const favData = await listFavorites(_appUserId);
        const dois = (favData.articles || []).map(a => a.doi).filter(Boolean);
        setFavorites(_appUserId, dois);
    } catch (e) {
        console.warn("Failed to load favorites:", e);
    }
})();
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


        if(e.key === "Enter"){


            startSearch();


        }


    }

);



// ================================
// Search
// ================================

let _lastController = null;

async function startSearch(){

    if (_lastController) {
        _lastController.abort();
    }
    _lastController = new AbortController();
    const signal = _lastController.signal;

    const keyword =

        keywordInput.value.trim();



    if(keyword === ""){


        alert("请输入关键词");


        return;


    }



    loading.innerHTML =

        "<h2>Searching...</h2>";



    results.innerHTML = "";



    searchBtn.disabled = true;



    searchBtn.innerText =

        "Searching...";



    try{


        const data =

            await searchPaper(

                keyword,
                "all",
                signal

            );

        // Refresh favorites before rendering
        const uid = _appUserId || parseInt(localStorage.getItem("chemvigil_user_id")) || null;
        if (uid) {
            _appUserId = uid;
            try {
                const favData = await listFavorites(uid);
                const dois = (favData.articles || []).map(a => a.doi).filter(Boolean);
                setFavorites(uid, dois);
            } catch (e) {}
        }


        loading.innerHTML = "";



        // 保存50篇论文

        setPapers(

            data.results

        );



        // 初始化分页

        initPagination(

            results

        );



        // 显示第一页

        renderCurrentPage();



    }


    catch(err){

        if (err.name === "AbortError") return;

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



    searchBtn.innerText =

        "搜索";


}