// =====================================
// pagination_view.js
// 分页按钮显示
// =====================================


import {

    getPageInfo,

    goToPage,

    nextPage,

    prevPage

}
from "./pagination.js";



import {

    renderCurrentPage

}
from "./pagination_controller.js";



// =====================================
// Render Pagination Buttons
// =====================================

export function renderPagination(container){


    let pagination =
        document.getElementById(
            "pagination"
        );


    if(!pagination){


        pagination =
            document.createElement(
                "div"
            );


        pagination.id =
            "pagination";


        container.appendChild(
            pagination
        );


    }


    pagination.innerHTML="";



    const info =
        getPageInfo();



    if(info.totalPages <= 1){

        return;

    }



    // Previous

    const prev =
        document.createElement(
            "button"
        );


    prev.innerText="上一页";


    prev.disabled =
        info.currentPage === 1;


    prev.onclick=()=>{

        prevPage();

        renderCurrentPage();

    };


    pagination.appendChild(prev);



    // Page Number


    for(
        let i=1;
        i<=info.totalPages;
        i++
    ){


        const btn =
            document.createElement(
                "button"
            );


        btn.innerText=i;



        if(
            i === info.currentPage
        ){

            btn.className =
                "page-active";

        }



        btn.onclick=()=>{


            goToPage(i);


            renderCurrentPage();


        };


        pagination.appendChild(btn);


    }



    // Next


    const next =
        document.createElement(
            "button"
        );


    next.innerText="下一页";


    next.disabled =
        info.currentPage === info.totalPages;



    next.onclick=()=>{


        nextPage();


        renderCurrentPage();


    };


    pagination.appendChild(next);



}