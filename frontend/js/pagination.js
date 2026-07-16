// ======================================
// Pagination Data Store
// ======================================


// 所有论文数据

let allPapers = [];


// 当前页

let currentPage = 1;


// 每页数量

const pageSize = 10;



// ======================================
// OpenAlex Cursor
// ======================================


let nextCursor = "*";



// ======================================
// Set Papers
// ======================================


export function setPapers(papers){


    allPapers = papers || [];


    currentPage = 1;


}



// ======================================
// Get Current Page Papers
// ======================================


export function getCurrentPage(){


    const start =

        (currentPage - 1) * pageSize;



    const end =

        start + pageSize;



    return allPapers.slice(

        start,

        end

    );


}



// ======================================
// Page Control
// ======================================



// 下一页

export function nextPage(){


    const maxPage =

        Math.ceil(

            allPapers.length / pageSize

        );



    if(currentPage < maxPage){


        currentPage++;


    }


}



// 上一页

export function previousPage(){


    if(currentPage > 1){


        currentPage--;


    }


}



// 兼容旧版本 pagination_view.js

export function prevPage(){


    previousPage();


}




// 跳转指定页

export function goToPage(page){


    const maxPage =

        Math.ceil(

            allPapers.length / pageSize

        );



    if(page < 1){


        return;


    }



    if(page > maxPage){


        return;


    }



    currentPage = page;


}



// ======================================
// Page Info
// ======================================


export function getPageInfo(){


    const totalPages =


        Math.ceil(

            allPapers.length / pageSize

        );



    return {


        currentPage,


        // 新旧名称都保留

        totalPage: totalPages,


        totalPages: totalPages


    };


}



// ======================================
// Cursor
// ======================================



export function setNextCursor(cursor){


    nextCursor = cursor;


}



export function getNextCursor(){


    return nextCursor;


}