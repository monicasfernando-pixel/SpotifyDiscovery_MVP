import { state } from "./state.js";
import { WISHLIST } from "./data/catalog.js";
import {
  is_at_price_floor,
  user_size_low_stock,
  size_rarely_restocks,
  occasion_near,
  verdict,
  isScarcityBuy,
  user_size_gone,
} from "./rules/verdict.js";
import { decideReadyItem, actNowPreviewItem } from "./rules/nudge.js";
import { renderWishlist } from "./screens/wishlist.js";
import { renderBag } from "./screens/bag.js";
import { renderStub } from "./screens/stubs.js";
import { bindBagStrip } from "./components/bag-strip.js";
import { jumpToWishGroup } from "./components/triage.js";

const screenEl = document.getElementById("screen");
const toastEl = document.getElementById("toast");
const searchInput = document.getElementById("searchInput");

function showToast(message) {
  toastEl.hidden = false;
  toastEl.textContent = message;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => {
    toastEl.hidden = true;
  }, 2800);
}

function updateUrgentUi() {
  const hasUrgent = Boolean(actNowPreviewItem());
  document.querySelectorAll(".wish-heart .sparkle-badge").forEach((el) => {
    el.hidden = !hasUrgent;
  });
}

function updateChrome() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.screen === state.screen);
  });
  const n = state.bag.length;
  document.querySelectorAll(".bag-count").forEach((el) => {
    el.hidden = n === 0;
    el.textContent = String(n);
  });
  const tabBadge = document.getElementById("tabBagBadge");
  if (tabBadge) {
    tabBadge.hidden = n === 0;
    tabBadge.textContent = String(n);
  }
  const wishCount = document.getElementById("wishCount");
  if (wishCount) {
    const c = state.wishlist.length;
    wishCount.textContent = `${c} ${c === 1 ? "item" : "items"}`;
  }
  const appBar = document.getElementById("appBar");
  const wishBar = document.getElementById("wishBar");
  const bagBar = document.getElementById("bagBar");
  const phone = document.getElementById("phone");
  appBar.hidden = state.screen === "wishlist" || state.screen === "bag";
  wishBar.hidden = state.screen !== "wishlist";
  bagBar.hidden = state.screen !== "bag";
  phone.classList.toggle("is-wishlist", state.screen === "wishlist");
  phone.classList.toggle("is-bag", state.screen === "bag");
  const tabBar = document.getElementById("tabBar");
  if (tabBar) tabBar.hidden = state.screen === "bag" || state.screen === "wishlist";
  updateUrgentUi();
}

function revealFocusedItem() {
  if (state.screen !== "wishlist" || !state.focusItemId) return;
  const card = screenEl.querySelector(`[data-item-id="${CSS.escape(state.focusItemId)}"]`);
  state.focusItemId = null;
  if (!card) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  requestAnimationFrame(() => {
    card.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
  });
}

function render() {
  if (state.screen === "wishlist") screenEl.innerHTML = renderWishlist();
  else if (state.screen === "bag") screenEl.innerHTML = renderBag();
  else screenEl.innerHTML = renderStub(state.screen);
  updateChrome();
  bindPage();
  revealFocusedItem();
}

function go(screen) {
  if (state.screen === screen && screen !== "bag") {
    screenEl.focus();
    return;
  }
  if (state.screen === "bag" && screen !== "bag") {
    state.stripDone = true;
  }
  state.screen = screen;
  render();
  screenEl.focus({ preventScroll: true });
}

function addToBag(id) {
  const item = state.wishlist.find((w) => w.id === id);
  if (!item) return;
  if (user_size_gone(item)) {
    showToast(`Size ${item.user_size} is gone — can’t add this one.`);
    return;
  }
  const existing = state.bag.find((b) => b.id === id);
  if (existing) {
    existing.qty += 1;
    showToast("Quantity updated in bag.");
  } else {
    state.bag.push({ ...item, qty: 1 });
    showToast("Added to bag.");
  }
  render();
}

function openWishlistItem(id) {
  state.showVerdicts = true;
  state.whyOpen = { [id]: true };
  state.focusItemId = id;
  state.filter = "all";
  state.category = null;
  const item = state.wishlist.find((w) => w.id === id);
  if (item && state.query) {
    const q = state.query.toLowerCase();
    const matches =
      item.brand.toLowerCase().includes(q) ||
      item.title.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q);
    if (!matches) {
      state.query = "";
      searchInput.value = "";
    }
  }
  go("wishlist");
}

function toggleAssistant(force) {
  state.showVerdicts = typeof force === "boolean" ? force : !state.showVerdicts;
  state.whyOpen = {};
  render();
  if (state.showVerdicts) {
    const first = screenEl.querySelector(".wish-group-act") || screenEl.querySelector(".verdict");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (first) first.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" });
  }
}

function bindPage() {
  screenEl.querySelectorAll("[data-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = btn.dataset.filter;
      state.filter = state.filter === next ? "all" : next;
      state.category = null;
      render();
    });
  });
  screenEl.querySelectorAll("[data-cat]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.category = state.category === btn.dataset.cat ? null : btn.dataset.cat;
      render();
    });
  });
  screenEl.querySelectorAll("[data-notify]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.notify;
      const item = state.wishlist.find((w) => w.id === id);
      state.alerts[id] = true;
      render();
      showToast(
        item
          ? `We’ll notify you if size ${item.user_size} is back — prototype.`
          : "We’ll notify you if it’s back — prototype."
      );
    });
  });
  screenEl.querySelectorAll("[data-add]").forEach((btn) => {
    btn.addEventListener("click", () => addToBag(btn.dataset.add));
  });
  screenEl.querySelectorAll("[data-remove]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.wishlist = state.wishlist.filter((item) => item.id !== btn.dataset.remove);
      render();
    });
  });
  screenEl.querySelectorAll("[data-share]").forEach((btn) => {
    btn.addEventListener("click", () => showToast("Link copied — prototype share."));
  });
  const assistChip = document.getElementById("assistChip");
  if (assistChip) assistChip.addEventListener("click", () => toggleAssistant());
  const assistReset = document.getElementById("assistReset");
  if (assistReset) assistReset.addEventListener("click", () => toggleAssistant(false));
  const collectionsChip = screenEl.querySelector(".chip-ref");
  if (collectionsChip) {
    collectionsChip.addEventListener("click", (e) => e.preventDefault());
  }
  bindBagStrip(screenEl.querySelector(".urgent-strip"), {
    onDismiss() {
      state.stripDone = true;
      render();
    },
    onAdd(id, markDone) {
      if (markDone) state.stripDone = true;
      addToBag(id);
    },
    onOpen: openWishlistItem,
  });
  screenEl.querySelectorAll("[data-jump]").forEach((btn) => {
    btn.addEventListener("click", () => jumpToWishGroup(screenEl, btn.dataset.jump));
  });
  screenEl.querySelectorAll("[data-why]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.dataset.why;
      const y = screenEl.scrollTop;
      state.whyOpen[id] = !state.whyOpen[id];
      render();
      screenEl.scrollTop = y;
    });
  });
  const addr = document.getElementById("addrBtn");
  if (addr) {
    addr.addEventListener("click", () => showToast("Delivering to Flat 45, Kailash Kunj."));
  }
  const place = document.getElementById("placeOrder");
  if (place) {
    place.addEventListener("click", () => {
      showToast("Prototype only — no payment. Checkout would start here.");
    });
  }
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => go(tab.dataset.screen));
});
document.getElementById("headerWishBtn").addEventListener("click", () => go("wishlist"));
document.getElementById("bagWishBtn").addEventListener("click", () => go("wishlist"));
document.getElementById("profileBtn").addEventListener("click", () => {
  showToast("Sign in lives in the real app — this is a concept prototype.");
});
document.getElementById("wishEditBtn").addEventListener("click", () => {
  showToast("Select items to edit — prototype.");
});
document.getElementById("wishBackBtn").addEventListener("click", () => go("home"));
document.getElementById("bagBackBtn").addEventListener("click", () => go("wishlist"));
document.getElementById("bagAddrBtn").addEventListener("click", () => {
  showToast("Delivering to Flat 45, Kailash Kunj.");
});
document.getElementById("phone").addEventListener("click", (e) => {
  const bagBtn = e.target.closest("[data-open-bag]");
  if (bagBtn) {
    e.preventDefault();
    go("bag");
    return;
  }
  const homeBtn = e.target.closest("[data-go-home]");
  if (homeBtn) {
    e.preventDefault();
    go("home");
  }
});

searchInput.addEventListener("input", () => {
  state.query = searchInput.value.trim();
  if (state.screen === "wishlist") render();
});

render();

window.__assistantRules = {
  is_at_price_floor,
  user_size_low_stock,
  size_rarely_restocks,
  occasion_near,
  verdict,
  isScarcityBuy,
  decideReadyItem,
  WISHLIST,
};
