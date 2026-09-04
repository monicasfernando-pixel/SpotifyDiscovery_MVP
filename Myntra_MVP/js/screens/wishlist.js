import { state } from "../state.js";
import { DISCLAIMER } from "../data/meta.js";
import { art } from "../ui/art.js";
import { inStock } from "../rules/verdict.js";
import { groupedWishlist } from "../rules/groups.js";
import { productCard } from "../components/product-card.js";
import { renderTriageStrip } from "../components/triage.js";

function matchesQuery(item) {
  if (!state.query) return true;
  const q = state.query.toLowerCase();
  return (
    item.brand.toLowerCase().includes(q) ||
    item.title.toLowerCase().includes(q) ||
    item.category.toLowerCase().includes(q)
  );
}

export function visibleWishlist() {
  return state.wishlist.filter((item) => {
    if (!matchesQuery(item)) return false;
    if (state.filter === "oos") return !inStock(item);
    if (state.category && item.category !== state.category) return false;
    return true;
  });
}

function categoryRow() {
  const cats = [];
  for (const item of state.wishlist) {
    if (!cats.some((c) => c.category === item.category)) cats.push(item);
  }
  return `<div class="cat-row" role="list">
    ${cats
      .map(
        (item) => `<button type="button" class="cat-item${state.category === item.category ? " is-on" : ""}" data-cat="${item.category}">
      <span class="cat-thumb">${art(item.kind)}</span>
      <span>${item.category}</span>
    </button>`
      )
      .join("")}
  </div>`;
}

function renderCardGrid(items) {
  if (!items.length) return `<p class="empty">No items in this view.</p>`;
  if (!state.showVerdicts) {
    return `<div class="grid">${items.map(productCard).join("")}</div>`;
  }
  const groups = groupedWishlist(items);
  const sections = [
    { key: "act", title: "Act now", items: groups.act },
    { key: "gone", title: "Not available in your size", items: groups.gone },
    { key: "wait", title: "Can wait", items: groups.wait },
    { key: "decide", title: "No rush", items: groups.decide },
  ];
  return sections
    .filter((s) => s.items.length)
    .map(
      (s) => `<section class="wish-group wish-group-${s.key}">
      <h2 class="wish-group-h">${s.title} <span>(${s.items.length})</span></h2>
      <div class="grid">${s.items.map(productCard).join("")}</div>
    </section>`
    )
    .join("");
}

export function renderWishlist() {
  const items = visibleWishlist();
  return `<section class="page wish-page">
    <button type="button" class="addr" id="addrBtn">
      <span class="addr-pin" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 21s7-6.2 7-11.2A7 7 0 0 0 5 9.8C5 14.8 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="9.8" r="2.2" fill="currentColor"/></svg>
      </span>
      <span class="addr-text">Jane Doe - Flat 45, gate -4, kailash kunj apartm...</span>
      <span class="addr-chevron" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="16" height="16"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
      </span>
    </button>
    <div class="filter-row">
      <button type="button" class="chip chip-ref" aria-disabled="true">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="4" y="6" width="12" height="12" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M8 6V4.8A1.8 1.8 0 0 1 9.8 3h8.4A1.8 1.8 0 0 1 20 4.8V14" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>
        Collections
        <span class="chip-tip">Exists in Myntra for a different purpose, depicted here just for UI reference.</span>
      </button>
      <button type="button" class="chip" data-filter="oos" aria-pressed="${state.filter === "oos"}">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="4" y="7" width="16" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M8 7V5.5A2.5 2.5 0 0 1 10.5 3h3A2.5 2.5 0 0 1 16 5.5V7M9 12l6 6M15 12l-6 6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
        Out of Stock
      </button>
      <button type="button" class="chip chip-assist" id="assistChip" aria-pressed="${state.showVerdicts}">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 3.2 13.1 8 18 9.2 13.1 10.4 12 15.2 10.9 10.4 6 9.2 10.9 8z" fill="currentColor"/><path d="M18.2 14.2 18.8 16.4 21 17l-2.2.6-.6 2.2-.6-2.2-2.2-.6 2.2-.6zM5.4 13.4l.5 1.6 1.6.5-1.6.5-.5 1.6-.5-1.6-1.6-.5 1.6-.5z" fill="currentColor"/></svg>
        Wishlist Assistant
      </button>
    </div>
    ${
      state.showVerdicts
        ? `<div class="sort-caption">
      <p>Sorted by what's worth buying now</p>
      <button type="button" class="sort-reset" id="assistReset">Reset</button>
    </div>`
        : ""
    }
    ${categoryRow()}
    ${renderTriageStrip(items)}
    ${renderCardGrid(items)}
    <p class="disclaimer">${DISCLAIMER}</p>
  </section>`;
}
