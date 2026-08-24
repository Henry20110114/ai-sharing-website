(function () {
  var root = document.documentElement;

  // Language toggle (default: Chinese; choice persisted in localStorage)
  var langBtn = document.getElementById("lang-toggle");
  function applyLang(lang) {
    root.dataset.lang = lang;
    root.setAttribute("lang", lang === "en" ? "en" : "zh-CN");
    try { localStorage.setItem("site-lang", lang); } catch (e) {}
  }
  applyLang(root.dataset.lang === "en" ? "en" : "zh");
  if (langBtn) {
    langBtn.addEventListener("click", function () {
      applyLang(root.dataset.lang === "en" ? "zh" : "en");
    });
  }

  // Mobile navigation
  var header = document.querySelector(".site-header");
  var navBtn = document.querySelector(".nav-toggle");
  if (header && navBtn) {
    navBtn.addEventListener("click", function () {
      var open = header.classList.toggle("nav-open");
      navBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

})();
