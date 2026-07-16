// ========================================
// ChemAI API
// ========================================


const API_BASE =

    "http://127.0.0.1:8000";



// ========================================
// Search Papers
// ========================================


export async function searchPaper(keyword) {


    const url =

        `${API_BASE}/search?q=${encodeURIComponent(keyword)}`;



    const response =

        await fetch(url);



    if(!response.ok){


        throw new Error(

            `HTTP ${response.status}`

        );


    }



    const data =

        await response.json();



    return data;


}