"use client";

import type { DemandItem, CatalogItem } from "./types";

const COLORS = ["#F6C445", "#7BC67E", "#6EB5FF", "#FF8FAB", "#C9A0FF", "#FFB347"];

type Props = {
  demand: DemandItem;
  products: CatalogItem[];
  onClose: () => void;
  onAdd: () => void;
};

export default function BottomSheet({ demand, products, onClose, onAdd }: Props) {
  return (
    <div className="absolute inset-0 z-40 flex flex-col justify-end overflow-hidden">
      <button
        type="button"
        aria-label="Close sheet"
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />
      <div className="relative z-10 max-h-full animate-sheet-up overflow-y-auto rounded-t-2xl bg-white px-4 pb-6 pt-3 shadow-xl">
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-zinc-300" />
        <p className="text-[13px] font-medium leading-snug text-zinc-800">
          {demand.sentence}
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2.5">
          {products.slice(0, 2).map((p, i) => (
            <div
              key={p.name}
              className="overflow-hidden rounded-xl border border-zinc-100 bg-zinc-50"
            >
              <div
                className="h-16 w-full"
                style={{ background: COLORS[i % COLORS.length] }}
              />
              <div className="space-y-1 p-2">
                <p className="line-clamp-2 text-[12px] font-medium text-zinc-900">
                  {p.name}
                </p>
                <p className="text-[12px] text-zinc-700">₹{p.price}</p>
                <p className="text-[11px] text-amber-600">★ {p.rating}</p>
                <button
                  type="button"
                  onClick={onAdd}
                  className="mt-1 w-full rounded-md border border-[#0C831F] bg-white py-1 text-[11px] font-bold tracking-wide text-[#0C831F]"
                >
                  ADD
                </button>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 rounded-lg bg-[#F4F9E0] px-3 py-2 text-[12px] font-medium text-[#4A6B10]">
          {demand.entryOffer}
        </div>
      </div>
    </div>
  );
}
