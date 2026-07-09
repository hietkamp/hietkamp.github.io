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

  // ── Practices dropdown ────────────────────────────────────────────────────
  const pracBtn  = document.getElementById("nav-prac-btn");
  const pracMenu = document.getElementById("prac-menu");

  if (pracBtn && pracMenu) {
    pracBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      const open = !pracMenu.classList.contains("hidden");
      pracMenu.classList.toggle("hidden", open);
      pracBtn.setAttribute("aria-expanded", String(!open));
    });

    document.addEventListener("click", function () {
      pracMenu.classList.add("hidden");
      pracBtn.setAttribute("aria-expanded", "false");
    });

    pracMenu.addEventListener("click", function (e) {
      e.stopPropagation();
    });

    // Keyboard: Escape closes
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        pracMenu.classList.add("hidden");
        pracBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  // ── Sidenav: populate from headings on the page ──────────────────────────
  function buildSidenav() {
    if (!sidenav) return;

    const headings = document.querySelectorAll(
      "main h2[id], main section[id] h2, main section[id]"
    );

    const links = [];

    // Collect <section id="..."> elements with a h2 inside
    document.querySelectorAll("main section[id]").forEach(function (sec) {
      const h2 = sec.querySelector("h2");
      if (!h2) return;
      links.push({ id: sec.id, label: h2.textContent.trim() });
    });

    if (links.length === 0) return;

    const label = document.createElement("div");
    label.className = "snav-section";
    label.textContent = "Op deze pagina";
    sidenav.appendChild(label);

    links.forEach(function (item) {
      const a = document.createElement("a");
      a.className  = "snav-link";
      a.href       = "#" + item.id;
      a.textContent = item.label;
      sidenav.appendChild(a);
    });

    // ── Intersection observer: highlight current section ──────────────────
    const allLinks = sidenav.querySelectorAll(".snav-link");

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

  // ── Search (no-op stub — extend later) ───────────────────────────────────
  const searchInput  = document.getElementById("site-search-input");
  const searchResults = document.getElementById("search-results-list");

  if (searchInput && searchResults) {
    searchInput.addEventListener("input", function () {
      if (searchInput.value.trim().length < 2) {
        searchResults.classList.add("hidden");
        return;
      }
      // Full-text search not yet implemented.
      searchResults.classList.add("hidden");
    });

    searchInput.addEventListener("blur", function () {
      setTimeout(function () {
        searchResults.classList.add("hidden");
      }, 200);
    });
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", buildSidenav);
})();
