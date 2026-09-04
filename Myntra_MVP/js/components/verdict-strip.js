import { state } from "../state.js";
import { VERDICT_META } from "../data/meta.js";
import { verdict, reasonFor, signalsFor } from "../rules/verdict.js";
import { iconSvg } from "../ui/art.js";

export function verdictStrip(item) {
  if (!state.showVerdicts) return "";
  const code = verdict(item);
  const meta = VERDICT_META[code];
  const open = Boolean(state.whyOpen[item.id]);
  const chips = signalsFor(item)
    .map((s) => `<span class="signal">${s}</span>`)
    .join("");
  const reason = reasonFor(item, code);
  return `<aside class="verdict verdict-${meta.key}${open ? " is-open" : ""}" aria-label="Assistant ${meta.label}">
    <div class="verdict-compact">
      <span class="verdict-ico">${iconSvg(meta.icon)}</span>
      <p class="verdict-line"><strong>${meta.label}</strong> — ${reason}</p>
      <button type="button" class="why-btn" data-why="${item.id}" aria-expanded="${open}">Why?</button>
    </div>
    <div class="verdict-detail" ${open ? "" : "hidden"}>
      <div class="signals">${chips}</div>
      <p class="ai-line"><strong>AI</strong> ${item.ai_relevance}</p>
    </div>
  </aside>`;
}
