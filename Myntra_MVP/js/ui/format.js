export function inr(n) {
  return "₹" + Number(n).toLocaleString("en-IN");
}

export function offPct(item) {
  return Math.round((1 - item.price / item.mrp) * 100);
}

export function priceBlock(item) {
  return `<div class="price-row">
    <span class="price">${inr(item.price)}</span>
    <span class="off">${offPct(item)}% OFF</span>
    <span class="mrp">${inr(item.mrp)}</span>
  </div>`;
}

export function ratingPill(item) {
  return `<span class="rating">${item.rating} <span class="star" aria-hidden="true">★</span></span>`;
}
