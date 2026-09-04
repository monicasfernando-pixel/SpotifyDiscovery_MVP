import {
  sizeQty,
  is_at_price_floor,
  occasion_near,
  verdict,
} from "./verdict.js";

export function signalRank(item) {
  const qty = sizeQty(item);
  const stock = qty === 0 ? 100 : Math.max(0, 8 - qty) * 8;
  return (
    stock +
    item.days_oos_90 +
    (is_at_price_floor(item) ? 12 : 0) +
    (occasion_near(item) ? 8 : 0)
  );
}

export function groupedWishlist(items) {
  const groups = { act: [], gone: [], wait: [], decide: [] };
  for (const item of items) {
    const code = verdict(item);
    if (code === "BUY") groups.act.push(item);
    else if (code === "GONE") groups.gone.push(item);
    else if (code === "WAIT") groups.wait.push(item);
    else groups.decide.push(item);
  }
  const bySignal = (a, b) => signalRank(b) - signalRank(a);
  groups.act.sort(bySignal);
  groups.gone.sort(bySignal);
  groups.wait.sort(bySignal);
  groups.decide.sort(bySignal);
  return groups;
}

export function tallyVerdicts(items) {
  const counts = { BUY: 0, GONE: 0, WAIT: 0, DECIDE: 0 };
  let buySpend = 0;
  for (const item of items) {
    const code = verdict(item);
    counts[code] += 1;
    if (code === "BUY") buySpend += item.price;
  }
  return { counts, buySpend };
}
