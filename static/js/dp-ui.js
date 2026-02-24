/* =========================================================
   Destinos Posibles — Navbar scroll + Sticky TOC highlighting
   Vanilla JS (works with Bootstrap 5)
   ========================================================= */

(function () {
  // 1) Navbar: transparent on top, solid after 50px
  const nav = document.querySelector(".dp-navbar");
  const threshold = 50;

  function setNavbarState() {
    if (!nav) return;
    const y = window.scrollY || document.documentElement.scrollTop;

    if (y <= threshold) {
      nav.classList.add("dp-navbar--top");
      nav.classList.remove("dp-navbar--solid");
    } else {
      nav.classList.remove("dp-navbar--top");
      nav.classList.add("dp-navbar--solid");
    }
  }

  window.addEventListener("scroll", setNavbarState, { passive: true });
  window.addEventListener("resize", setNavbarState);
  document.addEventListener("DOMContentLoaded", setNavbarState);

  // 2) TOC: auto-build (optional) + active section highlight
  // If you already render TOC server-side, just ensure links are in .dp-toc a[href^="#"]
  const toc = document.querySelector(".dp-toc");
  const article = document.querySelector(".dp-prose");

  // Optional: build TOC from h2 if toc exists but empty (safe fallback)
  if (toc && article) {
    const list = toc.querySelector("ul");
    if (list && list.children.length === 0) {
      const h2s = Array.from(article.querySelectorAll("h2[id]"));
      h2s.forEach((h2) => {
        const a = document.createElement("a");
        a.href = `#${h2.id}`;
        a.textContent = h2.textContent.trim();
        const li = document.createElement("li");
        li.appendChild(a);
        list.appendChild(li);
      });
    }
  }

  // Active link highlighting with IntersectionObserver
  const tocLinks = toc ? Array.from(toc.querySelectorAll('a[href^="#"]')) : [];
  const headings = article ? Array.from(article.querySelectorAll("h2[id]")) : [];

  if (tocLinks.length && headings.length && "IntersectionObserver" in window) {
    const linkById = new Map(
      tocLinks.map((a) => [decodeURIComponent(a.getAttribute("href").slice(1)), a])
    );

    let activeId = null;

    const observer = new IntersectionObserver(
      (entries) => {
        // Pick the heading closest to top that is intersecting
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        if (!visible.length) return;

        const id = visible[0].target.id;
        if (id === activeId) return;

        activeId = id;

        tocLinks.forEach((a) => a.classList.remove("is-active"));
        const activeLink = linkById.get(id);
        if (activeLink) activeLink.classList.add("is-active");
      },
      {
        root: null,
        // Start tracking when heading is near top
        rootMargin: "-20% 0px -70% 0px",
        threshold: 0.01,
      }
    );

    headings.forEach((h) => observer.observe(h));
  }
})();