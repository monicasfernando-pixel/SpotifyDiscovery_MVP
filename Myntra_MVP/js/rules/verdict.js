import { inr } from "../ui/format.js";

export function sizeQty(item) {
  return item.stock[item.user_size] ?? 0;
}

export function is_at_price_floor(item) {
  return item.price <= Math.min(...item.price_history);
}

export function user_size_low_stock(item) {
  const qty = sizeQty(item);
  return qty > 0 && qty <= 3;
}

export function size_rarely_restocks(item) {
  return item.days_oos_90 >= 14;
}

export function occasion_near(item) {
  return Boolean(item.occasion && item.occasion.days_until <= 21);
}

export function user_size_gone(item) {
  return sizeQty(item) === 0;
}

export function priceDropped(item) {
  const hist = item.price_history;
  return hist.length >= 2 && item.price < hist[0];
}

export function inStock(item) {
  return sizeQty(item) > 0;
}

export function lowAndRare(item) {
  return user_size_low_stock(item) && size_rarely_restocks(item);
}

export function verdict(item) {
  if (user_size_gone(item)) return "GONE";
  const floor = is_at_price_floor(item);
  const low = user_size_low_stock(item);
  const rare = size_rarely_restocks(item);
  const occ = occasion_near(item);
  if ((floor && (low || rare || occ)) || (low && rare)) return "BUY";
  if (item.saved_days_ago >= 30 && !low && !occ) return "DECIDE";
  if (!floor) return "WAIT";
  return "DECIDE";
}

export function nudgeReason(item) {
  const qty = sizeQty(item);
  return `Only ${qty} left in size ${item.user_size}, and it's been out of stock ${item.days_oos_90} of the last 90 days.`;
}

export function reasonFor(item, code) {
  const size = item.user_size;
  const qty = sizeQty(item);
  if (code === "GONE") {
    return size_rarely_restocks(item)
      ? `Size ${size} is sold out and rarely restocks.`
      : `Size ${size} is sold out right now.`;
  }
  if (code === "BUY") {
    if (lowAndRare(item)) return nudgeReason(item);
    if (is_at_price_floor(item) && user_size_low_stock(item)) {
      return `At your lowest seen price, and size ${size} has ${qty} left.`;
    }
    if (is_at_price_floor(item) && occasion_near(item)) {
      return `Lowest seen price, and ${item.occasion.name} is in ${item.occasion.days_until} days.`;
    }
    return `Strong buy signals on price and availability for size ${size}.`;
  }
  if (code === "WAIT") {
    const floor = Math.min(...item.price_history);
    return `A lower price of ${inr(floor)} has shown up before — stock is still okay.`;
  }
  if (item.saved_days_ago >= 30) {
    return `Saved ${item.saved_days_ago} days ago with no date or stock pressure.`;
  }
  return `Price is at the floor, but size ${size} is plentiful — no rush.`;
}

export function isScarcityBuy(item) {
  return verdict(item) === "BUY" && lowAndRare(item);
}

export function signalsFor(item) {
  const floor = is_at_price_floor(item);
  const qty = sizeQty(item);
  return [
    floor ? "Price floor" : `Floor ${inr(Math.min(...item.price_history))}`,
    qty === 0 ? `Size ${item.user_size} gone` : `Size ${item.user_size}: ${qty} left`,
    size_rarely_restocks(item)
      ? `Rare restock · ${item.days_oos_90}d/90`
      : `Often back · ${item.days_oos_90}d/90`,
  ];
}
