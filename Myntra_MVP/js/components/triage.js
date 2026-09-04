import { state } from "../state.js";
import { TRIAGE_ROWS, VERDICT_META } from "../data/meta.js";
import { tallyVerdicts } from "../rules/groups.js";
import { iconSvg, SPARKLE_SVG } from "../ui/art.js";
import { inr } from "../ui/format.js";

export function renderTriageStrip(items) {
  if (!state.showVerdicts || !items.length) return "";
  const { counts, buySpend } = tallyVerdicts(items);
  const pills = TRIAGE_ROWS.filter((row) => counts[row.code] > 0)
    .map((row) => {
      const n = counts[row.code];
      const meta = VERDICT_META[row.code];
      const phrase = `${n} ${row.label}`;
      return `<button type="button" class="triage-pill triage-${meta.key}" data-jump="${row.jump}" aria-label="${phrase}">
        <span class="triage-ico">${iconSvg(meta.icon)}</span>
        <span class="triage-n">${n}</span>
        <span class="triage-label">${row.label}</span>
      </button>`;
    })
    .join("");
  if (!pills) return "";
  const spend =
    counts.BUY > 0 ? `<span class="triage-spend">${inr(buySpend)} to act on</span>` : "";
  return `<aside class="triage" aria-label="Assistant summary">
    <p class="triage-id">${SPARKLE_SVG} Wishlist Assistant</p>
    <div class="triage-counts">${pills}${spend}</div>
  </aside>`;
}

export function jumpToWishGroup(screenEl, key) {
  const el = screenEl.querySelector(`.wish-group-${key}`);
  if (!el) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ block: "start", behavior: reduce ? "auto" : "smooth" });
}
