import { art, SPARKLE_SVG } from "../ui/art.js";
import { previewItemLabel, previewReasonFrag } from "../rules/nudge.js";
import { user_size_gone } from "../rules/verdict.js";
import { state } from "../state.js";

export function renderBagStrip(item) {
  const label = previewItemLabel(item);
  const frag = previewReasonFrag(item);
  return `<aside class="urgent-strip" aria-label="Wishlist Assistant">
    <span class="urgent-id">${SPARKLE_SVG} Wishlist Assistant</span>
    <button type="button" class="urgent-main" data-urgent-open="${item.id}" aria-label="View ${label} in wishlist">
      <span class="urgent-name">${label}</span>
      <span class="urgent-frag">${frag}</span>
    </button>
    <button type="button" class="urgent-add" data-urgent-add="${item.id}">Add</button>
    <button type="button" class="urgent-close" data-urgent-close aria-label="Dismiss">
      <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M7 7l10 10M17 7 7 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
    </button>
  </aside>`;
}

export function bindBagStrip(root, { onDismiss, onAdd, onOpen }) {
  if (!root) return;
  const closeBtn = root.querySelector("[data-urgent-close]");
  if (closeBtn) {
    closeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      onDismiss();
    });
  }
  const addBtn = root.querySelector("[data-urgent-add]");
  if (addBtn) {
    addBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = addBtn.dataset.urgentAdd;
      const item = state.wishlist.find((w) => w.id === id);
      onAdd(id, item && !user_size_gone(item));
    });
  }
  const openBtn = root.querySelector("[data-urgent-open]");
  if (openBtn) {
    openBtn.addEventListener("click", () => onOpen(openBtn.dataset.urgentOpen));
  }
}
