import { state } from "../state.js";
import { art } from "../ui/art.js";
import { priceBlock, ratingPill } from "../ui/format.js";
import { priceDropped, user_size_low_stock, user_size_gone } from "../rules/verdict.js";
import { verdictStrip } from "./verdict-strip.js";

function tagsFor(item) {
  const tags = [];
  if (priceDropped(item)) tags.push(`<span class="pill pill-drop">Price dropped</span>`);
  if (user_size_low_stock(item)) tags.push(`<span class="pill pill-low">Low in stock</span>`);
  return tags.length ? `<div class="card-tags">${tags.join("")}</div>` : "";
}

export function productCard(item) {
  const inBag = state.bag.some((b) => b.id === item.id);
  const gone = user_size_gone(item);
  const overlay = gone
    ? ""
    : `<button type="button" class="add-btn${inBag ? " is-in" : ""}" data-add="${item.id}" aria-label="Add ${item.brand} to bag">
        <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M6.5 8.5h11l-.7 11.2H7.2L6.5 8.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9 8.4V7.2A3 3 0 0 1 12 4.2a3 3 0 0 1 3 3v1.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        ${inBag ? "Added" : "Add"}
      </button>`;
  const tools = gone
    ? `<div class="card-tools is-gone">
      <button type="button" class="tool-notify${state.alerts[item.id] ? " is-on" : ""}" data-notify="${item.id}">
        ${state.alerts[item.id] ? "Notifying" : "Notify when back"}
      </button>
      <button type="button" class="tool-remove" data-remove="${item.id}">Remove</button>
    </div>`
    : `<div class="card-tools">
      <button type="button" data-remove="${item.id}" aria-label="Remove from wishlist">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M5 7h14M10 7V5h4v2m-7 0 1 13h8l1-13" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <button type="button" data-add="${item.id}" aria-label="Move to bag">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="5" y="5" width="14" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
      </button>
      <button type="button" data-share="${item.id}" aria-label="Share">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="6" cy="12" r="2.1" fill="none" stroke="currentColor" stroke-width="1.7"/><circle cx="18" cy="6.5" r="2.1" fill="none" stroke="currentColor" stroke-width="1.7"/><circle cx="18" cy="17.5" r="2.1" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="m8 11 8-3.8M8 13l8 3.8" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>
      </button>
    </div>`;
  return `<article class="card${state.focusItemId === item.id ? " is-focus" : ""}" data-item-id="${item.id}">
    <div class="card-art">
      ${art(item.kind)}
      ${tagsFor(item)}
      ${ratingPill(item)}
      ${overlay}
    </div>
    <div class="card-body">
      <h3 class="brand">${item.brand}</h3>
      <p class="title">${item.title}</p>
      ${priceBlock(item)}
      <p class="delivery">Delivery on <strong>${item.delivery}</strong> <span class="mnow">m-now</span></p>
    </div>
    ${verdictStrip(item)}
    ${tools}
  </article>`;
}
