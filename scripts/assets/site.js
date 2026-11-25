// Progressive enhancement only: every page works without this file.
document.addEventListener("DOMContentLoaded", () => {
  if (typeof renderMathInElement === "function") {
    renderMathInElement(document.querySelector(".document-content"), {
      delimiters: [
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false },
      ],
      throwOnError: false,
    });
  }

  // The contents list is a collapsed <details> on narrow screens and a sidebar
  // on wide ones; the sidebar needs it open.
  const toc = document.querySelector(".xls-toc details");
  if (toc && matchMedia("(width >= 1200px)").matches) toc.open = true;

  const table = document.getElementById("standards-table");
  if (!table) return;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  const cell = (row, column) => row.querySelector(`[data-column="${column}"]`);
  const key = (row, column) => {
    const td = cell(row, column);
    return td.dataset.sort ?? td.textContent.trim().toLowerCase();
  };

  table.querySelectorAll("th[data-column]").forEach((th) => {
    th.querySelector("button").addEventListener("click", () => {
      const column = th.dataset.column;
      const ascending = th.getAttribute("aria-sort") !== "ascending";
      table
        .querySelectorAll("th[aria-sort]")
        .forEach((h) => h.removeAttribute("aria-sort"));
      th.setAttribute("aria-sort", ascending ? "ascending" : "descending");
      rows
        .sort(
          (a, b) =>
            key(a, column).localeCompare(key(b, column), undefined, {
              numeric: true,
            }) * (ascending ? 1 : -1),
        )
        .forEach((row) => tbody.appendChild(row));
    });
  });

  const filter = document.getElementById("standards-filter");
  const count = document.getElementById("standards-count");
  filter.hidden = false;
  filter.addEventListener("input", () => {
    const terms = filter.value.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    rows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      row.hidden = !terms.every((t) => text.includes(t));
      shown += !row.hidden;
    });
    count.textContent = terms.length ? `${shown} of ${rows.length}` : "";
  });
});
