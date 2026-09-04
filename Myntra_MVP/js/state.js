import { WISHLIST, CATALOG } from "./data/catalog.js";

export const state = {
  screen: "wishlist",
  query: "",
  filter: "all",
  category: null,
  showVerdicts: false,
  whyOpen: {},
  wishlist: WISHLIST.map((item) => ({ ...item })),
  bag: [
    { ...CATALOG.jeans, qty: 1 },
    { ...CATALOG.tee, qty: 1 },
  ],
  stripDone: false,
  focusItemId: null,
  alerts: {},
};
