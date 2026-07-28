export type DemandItem = {
  id: string;
  category: string;
  orders: number;
  window: string;
  sentence: string;
  entryOffer: string;
};

export type CatalogItem = {
  name: string;
  category: string;
  price: number;
  rating: number;
};
