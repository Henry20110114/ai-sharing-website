(function () {
  var root = document.documentElement;

  // Language: the <head> script already picked zh/en (saved choice, else browser language).
  // Only an explicit toggle is saved, so a visitor who never toggles keeps following their browser.
  var langBtn = document.getElementById("lang-toggle");
  function applyLang(lang, save) {
    root.dataset.lang = lang;
    root.setAttribute("lang", lang === "en" ? "en" : "zh-CN");
    if (save) {
      try { localStorage.setItem("site-lang", lang); } catch (e) {}
    }
  }
  applyLang(root.dataset.lang === "en" ? "en" : "zh", false);
  if (langBtn) {
    langBtn.addEventListener("click", function () {
      applyLang(root.dataset.lang === "en" ? "zh" : "en", true);
    });
  }

  // Mobile navigation: toggle button, and close on outside tap or Escape
  var header = document.querySelector(".site-header");
  var navBtn = document.querySelector(".nav-toggle");
  if (header && navBtn) {
    function setOpen(open) {
      header.classList.toggle("nav-open", open);
      navBtn.setAttribute("aria-expanded", open ? "true" : "false");
    }
    navBtn.addEventListener("click", function () {
      setOpen(!header.classList.contains("nav-open"));
    });
    document.addEventListener("click", function (e) {
      if (header.classList.contains("nav-open") && !header.contains(e.target)) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && header.classList.contains("nav-open")) {
        setOpen(false);
        navBtn.focus();
      }
    });
  }
})();
