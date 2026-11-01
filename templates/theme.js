/* Colour theme button: auto -> light -> dark. Runs on every page. */
(function () {
  "use strict";
  /* ---- theme: auto -> light -> dark ---- */
  var root = document.documentElement, tb = document.getElementById("theme");
  function themeLabel() { tb.textContent = "Theme: " + (root.getAttribute("data-theme") || "auto"); }
  tb.addEventListener("click", function () {
    var cur = root.getAttribute("data-theme"), nxt = cur === null ? "light" : cur === "light" ? "dark" : null;
    if (nxt) root.setAttribute("data-theme", nxt); else root.removeAttribute("data-theme");
    try { if (nxt) localStorage.setItem("bbr-theme", nxt); else localStorage.removeItem("bbr-theme"); } catch (err) { /* ignore */ }
    themeLabel();
  });
  themeLabel();
})();
