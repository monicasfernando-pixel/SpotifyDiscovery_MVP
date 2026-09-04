import { state } from "../state.js";
import { DISCLAIMER } from "../data/meta.js";
import { art } from "../ui/art.js";
import { inr, priceBlock } from "../ui/format.js";
import { actNowPreviewItem, shouldShowBagStrip } from "../rules/nudge.js";
import { renderBagStrip } from "../components/bag-strip.js";

function bagTotals() {
  return state.bag.reduce(
    (acc, item) => {
      acc.mrp += item.mrp * item.qty;
      acc.price += item.price * item.qty;
      return acc;
    },
    { mrp: 0, price: 0 }
  );
}

function bagRow(item) {
  return `<article class="bag-item">
    <div class="card-art">${art(item.kind)}</div>
    <div>
      <h3 class="bag-brand">${item.brand}</h3>
      <p class="bag-title">${item.title}</p>
      <p class="bag-meta">Size: ${item.user_size} · Qty: ${item.qty}</p>
      ${priceBlock(item)}
    </div>
  </article>`;
}

export function renderBag() {
  const { mrp, price } = bagTotals();
  const discount = mrp - price;
  return `<section class="page bag-page">
    ${shouldShowBagStrip() ? renderBagStrip(actNowPreviewItem()) : ""}
    <div class="bag-list">${state.bag.map(bagRow).join("")}</div>
    <div class="coupon"><span>Apply Coupon</span><span>›</span></div>
    <div class="summary">
      <h2>Price details</h2>
      <div class="row"><span>Total MRP</span><span>${inr(mrp)}</span></div>
      <div class="row"><span>Discount on MRP</span><span>− ${inr(discount)}</span></div>
      <div class="row"><span>Convenience fee</span><span>FREE</span></div>
      <div class="row total"><span>Total amount</span><strong>${inr(price)}</strong></div>
    </div>
    <button type="button" class="place-order" id="placeOrder">Place order</button>
    <p class="disclaimer">${DISCLAIMER}</p>
  </section>`;
}
