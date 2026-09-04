export const VERDICT_META = {
  BUY: { key: "buy", label: "BUY NOW", icon: "check" },
  WAIT: { key: "wait", label: "WORTH WAITING", icon: "clock" },
  DECIDE: { key: "decide", label: "STILL WANT IT?", icon: "help" },
  GONE: { key: "gone", label: "GONE IN YOUR SIZE", icon: "gone" },
};

export const TRIAGE_ROWS = [
  { code: "BUY", jump: "act", label: "act now" },
  { code: "GONE", jump: "gone", label: "not available in your size" },
  { code: "WAIT", jump: "wait", label: "can wait" },
  { code: "DECIDE", jump: "decide", label: "no rush" },
];

export const DISCLAIMER =
  "Concept prototype — verdicts computed live by rules; AI relevance shown with representative outputs; runs on sample data, production would read Myntra's existing SKU & price-history services.";
