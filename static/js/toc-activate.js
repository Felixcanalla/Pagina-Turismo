(function () {
  const toc = document.getElementById("toc");
  if (!toc) return;

  const links = Array.from(toc.querySelectorAll('a[href^="#"]'));
  if (!links.length) return;

  const idToLink = new Map();
  links.forEach((a) => {
    const id = decodeURIComponent(a.getAttribute("href").slice(1));
    if (id) idToLink.set(id, a);
  });

  const headings = Array.from(document.querySelectorAll(".post__body h2[id]"))
    .filter((h) => idToLink.has(h.id));

  if (!headings.length) return;

  let currentId = null;

  function setActive(id) {
    if (currentId === id) return;
    currentId = id;

    links.forEach((a) => a.classList.remove("is-active"));
    const active = idToLink.get(id);
    if (active) active.classList.add("is-active");
  }

  // Umbral: marca activa la sección cuando el h2 entra en la parte alta de la pantalla
  const observer = new IntersectionObserver(
    (entries) => {
      // quedate con los que están visibles
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

      if (visible.length) {
        setActive(visible[0].target.id);
      } else {
        // fallback: si no hay intersecting, busca el último h2 "pasado"
        const passed = headings
          .filter((h) => h.getBoundingClientRect().top < 120)
          .sort((a, b) => b.getBoundingClientRect().top - a.getBoundingClientRect().top);

        if (passed.length) setActive(passed[0].id);
      }
    },
    {
      root: null,
      // Ajustá este margin si tu header es más alto/bajo
      rootMargin: "-110px 0px -70% 0px",
      threshold: [0, 1.0],
    }
  );

  headings.forEach((h) => observer.observe(h));

  // Set inicial
  setActive(headings[0].id);
})();
