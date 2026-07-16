// =====================================
// pagination_controller.js
// 分页控制中心
// =====================================


import {

    getCurrentPage

}
from "./pagination.js";


import {

    renderResults

}
from "./render.js";


import {

    renderPagination

}
from "./pagination_view.js";



// 当前结果容器

let resultsContainer = null;



// =====================================
// 初始化
// =====================================

export function initPagination(container){

    resultsContainer = container;

}



// =====================================
// 渲染当前页
// =====================================

export function renderCurrentPage(){


    if(!resultsContainer){

        return;

    }


    const papers =
        getCurrentPage();



    renderResults(

        resultsContainer,

        papers

    );


    renderPagination(

        resultsContainer.parentNode

    );


}