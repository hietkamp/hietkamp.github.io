/* nav.js — Essence Way of Working site navigation */
(function () {
  "use strict";

  // ── Header height sync ────────────────────────────────────────────────────
  // The disclaimer banner wraps to a different number of lines depending on
  // viewport width, so the fixed header's height isn't constant. Sidenav,
  // overlay and sticky-toolbar offsets read --header-h instead of a fixed px.
  const header = document.querySelector(".topnav");

  function syncHeaderHeight() {
    if (!header) return;
    document.documentElement.style.setProperty("--header-h", header.offsetHeight + "px");
  }

  syncHeaderHeight();
  window.addEventListener("resize", syncHeaderHeight);
  window.addEventListener("load", syncHeaderHeight);

  // ── Mobile toggle ─────────────────────────────────────────────────────────
  const toggle   = document.querySelector(".topnav-toggle");
  const navItems = document.querySelector(".topnav-items");
  const sidenav  = document.getElementById("sidenav");
  const overlay  = document.getElementById("sidenav-overlay");

  function closeMobileNav() {
    if (navItems)  navItems.classList.remove("open");
    if (sidenav)   sidenav.classList.remove("open");
    if (overlay)   overlay.classList.add("hidden");
    if (toggle)    toggle.setAttribute("aria-expanded", "false");
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      const open = sidenav && sidenav.classList.contains("open");
      if (open) {
        closeMobileNav();
      } else {
        if (sidenav)  sidenav.classList.add("open");
        if (overlay)  overlay.classList.remove("hidden");
        toggle.setAttribute("aria-expanded", "true");
      }
    });
  }

  if (overlay) {
    overlay.addEventListener("click", closeMobileNav);
  }

  // ── Page TOC (right column): populate from headings on the page ──────────
  // The left #sidenav is server-rendered site navigation (siblings) — this
  // only ever fills the separate right-hand #page-toc with in-page anchors,
  // so the two never mix content.
  function buildPageToc() {
    const toc = document.getElementById("page-toc");
    if (!toc) return;

    const links = [];

    document.querySelectorAll("main section[id]").forEach(function (sec) {
      const h2 = sec.querySelector("h2");
      if (!h2) return;
      links.push({ id: sec.id, label: h2.textContent.trim() });
    });

    if (links.length === 0) return;

    const label = document.createElement("div");
    label.className = "snav-section";
    label.textContent = "Op deze pagina";
    toc.appendChild(label);

    links.forEach(function (item) {
      const a = document.createElement("a");
      a.className  = "snav-link";
      a.href       = "#" + item.id;
      a.textContent = item.label;
      toc.appendChild(a);
    });

    // ── Intersection observer: highlight current section ──────────────────
    const allLinks = toc.querySelectorAll(".snav-link");

    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            allLinks.forEach(function (a) {
              a.classList.toggle(
                "active",
                a.getAttribute("href") === "#" + entry.target.id
              );
            });
          }
        });
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );

    document.querySelectorAll("main section[id]").forEach(function (sec) {
      observer.observe(sec);
    });
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", buildPageToc);
})();
