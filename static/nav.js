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

  // ── Mobile toggles ────────────────────────────────────────────────────────
  // Two independent mobile menus can exist on a page: the left #sidenav
  // (page siblings, only on detail pages) and #navbar-menu (the Hoofdnavigatie
  // row, on every page). Each has its own toggle button, but only one should
  // be open at a time, so opening either closes the other.
  const sidenavToggle  = document.querySelector(".topnav-toggle");
  const sidenav        = document.getElementById("sidenav");
  const sidenavOverlay = document.getElementById("sidenav-overlay");

  const navbarToggle = document.querySelector(".navbar-toggle");
  const navbarMenu    = document.getElementById("navbar-menu");

  function closeSidenav() {
    if (sidenav)        sidenav.classList.remove("open");
    if (sidenavOverlay) sidenavOverlay.classList.add("hidden");
    if (sidenavToggle)  sidenavToggle.setAttribute("aria-expanded", "false");
  }

  function closeNavbarMenu() {
    if (navbarMenu)   navbarMenu.classList.remove("open");
    if (navbarToggle) navbarToggle.setAttribute("aria-expanded", "false");
  }

  if (sidenavToggle) {
    sidenavToggle.addEventListener("click", function () {
      const open = sidenav && sidenav.classList.contains("open");
      closeNavbarMenu();
      if (open) {
        closeSidenav();
      } else {
        if (sidenav)        sidenav.classList.add("open");
        if (sidenavOverlay) sidenavOverlay.classList.remove("hidden");
        sidenavToggle.setAttribute("aria-expanded", "true");
      }
    });
  }

  if (sidenavOverlay) {
    sidenavOverlay.addEventListener("click", closeSidenav);
  }

  if (navbarToggle && navbarMenu) {
    navbarToggle.addEventListener("click", function () {
      const open = navbarMenu.classList.contains("open");
      closeSidenav();
      if (open) {
        closeNavbarMenu();
      } else {
        navbarMenu.classList.add("open");
        navbarToggle.setAttribute("aria-expanded", "true");
      }
    });

    // Closing on link click and outside-click keeps the dropdown from being
    // left open after navigating away or tapping elsewhere on the page.
    navbarMenu.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", closeNavbarMenu);
    });

    document.addEventListener("click", function (e) {
      if (!navbarMenu.classList.contains("open")) return;
      if (navbarMenu.contains(e.target) || navbarToggle.contains(e.target)) return;
      closeNavbarMenu();
    });
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
