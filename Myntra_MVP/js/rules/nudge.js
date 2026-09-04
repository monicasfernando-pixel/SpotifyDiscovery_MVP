import { state } from "../state.js";
import { isScarcityBuy, sizeQty, user_size_gone } from "./verdict.js";

export function decideReadyItem() {
  const inBag = new Set(state.bag.map((b) => b.id));
  const candidates = state.wishlist.filter(
    (item) => isScarcityBuy(item) && !inBag.has(item.id)
  );
  if (!candidates.length) return null;
  candidates.sort((a, b) => {
    const stockDiff = sizeQty(a) - sizeQty(b);
    if (stockDiff !== 0) return stockDiff;
    return b.days_oos_90 - a.days_oos_90;
  });
  return candidates[0];
}

export function actNowPreviewItem() {
  return decideReadyItem();
}

export function shouldShowBagStrip() {
  return !state.stripDone && Boolean(actNowPreviewItem());
}

export function previewItemLabel(item) {
  return `${item.brand} ${item.kind}`;
}

export function previewReasonFrag(item) {
  if (user_size_gone(item)) return `size ${item.user_size} gone`;
  return `size ${item.user_size} nearly gone`;
}
