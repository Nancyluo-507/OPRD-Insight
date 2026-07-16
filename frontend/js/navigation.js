// =====================================
// navigation.js
// Sidebar Navigation
// =====================================

const menuItems = document.querySelectorAll("#navMenu li");

const pages = document.querySelectorAll(".page");

menuItems.forEach(item => {

    item.addEventListener("click", () => {

        // -----------------------------
        // 左侧菜单高亮
        // -----------------------------

        menuItems.forEach(menu => {

            menu.classList.remove("active");

        });

        item.classList.add("active");

        // -----------------------------
        // 页面切换
        // -----------------------------

        const pageId = item.dataset.page;

        pages.forEach(page => {

            page.classList.remove("active-page");

        });

        const target = document.getElementById(pageId);

        if (target) {

            target.classList.add("active-page");

        }

    });

});