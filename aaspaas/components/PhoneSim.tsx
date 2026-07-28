"use client";

import { useMemo, useState } from "react";
import demandData from "@/data/demand.json";
import catalogData from "@/data/catalog.json";
import BottomSheet from "./BottomSheet";
import type { DemandItem, CatalogItem } from "./types";

const demand = demandData as DemandItem[];
const catalog = catalogData as CatalogItem[];

const THUMB = ["#F6C445", "#7BC67E", "#6EB5FF", "#FF8FAB", "#C9A0FF", "#FFB347", "#A8DADC", "#E9C46A"];
const RECENT = ["dosa ma", "banan", "oil", "dosa batter", "milk"];
const TOP_PICKS = catalog.filter((_, i) => i % 8 === 0).slice(0, 6);

function HighlightMatch({ text, query }: { text: string; query: string }) {
  const i = text.toLowerCase().indexOf(query.toLowerCase());
  if (i < 0) return <span className="font-semibold text-[#1C1C1C]">{text}</span>;
  const before = text.slice(0, i);
  const match = text.slice(i, i + query.length);
  const after = text.slice(i + query.length);
  return (
    <span>
      {before}
      <span className="text-[#7E8794]">{match}</span>
      <span className="font-semibold text-[#1C1C1C]">{after}</span>
    </span>
  );
}

function ProductCard({
  product,
  color,
  onAdd,
}: {
  product: CatalogItem;
  color: string;
  onAdd?: () => void;
}) {
  const mrp = Math.round(product.price * 1.25);
  return (
    <div className="w-[140px] shrink-0">
      <div className="overflow-hidden rounded-2xl bg-white">
        <div className="h-[110px] w-full" style={{ background: color }} />
        <div className="flex items-center justify-between gap-1 px-2 py-1.5">
          <span className="text-[11px] text-[#1C1C1C]">1 pc</span>
          <button
            type="button"
            onClick={onAdd}
            className="rounded-lg border-[1.5px] border-[#0C831F] px-3 py-0.5 text-[12px] font-bold uppercase text-[#0C831F]"
          >
            ADD
          </button>
        </div>
      </div>
      <div className="mt-1.5 space-y-0.5 px-0.5">
        <p className="text-[13px] font-bold text-[#1C1C1C]">
          ₹{product.price}{" "}
          <span className="text-[11px] font-normal text-[#7E8794] line-through">
            ₹{mrp}
          </span>
        </p>
        <p className="line-clamp-2 text-[12px] leading-snug text-[#1C1C1C]">
          {product.name}
        </p>
        <p className="text-[11px] text-amber-500">
          ★ {product.rating}{" "}
          <span className="text-[#7E8794]">
            ({Math.round(product.rating * 200)})
          </span>
        </p>
        <p className="text-[11px] text-[#7E8794]">⏱ 13 mins</p>
      </div>
    </div>
  );
}

export default function PhoneSim() {
  const [query, setQuery] = useState("");
  const [cartCount, setCartCount] = useState(0);
  const [activeDemand, setActiveDemand] = useState<DemandItem | null>(null);
  const [recents, setRecents] = useState(RECENT);

  const q = query.trim().toLowerCase();
  const matches = useMemo(
    () =>
      q
        ? catalog.filter((p) => p.name.toLowerCase().includes(q)).slice(0, 8)
        : [],
    [q],
  );
  const showIceHint = q.startsWith("ice");
  const iceDemand = demand.find((d) => d.id === "ice-cream")!;

  function openDemand(item: DemandItem) {
    setActiveDemand(item);
  }

  function productsFor(item: DemandItem) {
    return catalog.filter((p) => p.category === item.category);
  }

  function onQueryChange(value: string) {
    setQuery(value);
    setActiveDemand(null);
  }

  return (
    <div className="relative isolate flex h-full w-full flex-col overflow-hidden bg-[#FAF7EC] text-[#1C1C1C]">
      <div className="shrink-0 bg-[#F8CB46] px-3.5 pb-3 pt-3">
        <p className="text-[15px] font-bold leading-tight text-[#1C1C1C]">
          Aaspaas · delivery in 13 minutes
        </p>
        <p className="mt-0.5 text-[11px] font-medium text-[#1C1C1C]/60">
          HOME - Flat 43 ▾
        </p>
      </div>

      <div className="shrink-0 bg-[#FAF7EC] px-3.5 pt-3">
        <input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search for atta, dal, coke and more"
          className="w-full rounded-full border-0 bg-white px-4 py-2.5 text-[13px] text-[#1C1C1C] shadow-sm outline-none ring-1 ring-zinc-200/80 placeholder:text-[#7E8794] focus:ring-[#0C831F]/40"
        />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3.5 pb-20 pt-4">
        {!q && (
          <>
            <section>
              <h2 className="mb-3 text-[20px] font-bold text-[#1C1C1C]">
                Around you right now · Sector 47
              </h2>
              <ul className="space-y-2">
                {demand.map((d) => (
                  <li key={d.id}>
                    <button
                      type="button"
                      onClick={() => openDemand(d)}
                      className="w-full rounded-2xl bg-white px-3 py-3 text-left shadow-sm"
                    >
                      <p className="text-[13px] font-semibold text-[#1C1C1C]">
                        {d.category} · {d.orders} orders {d.window}
                      </p>
                      <p className="mt-0.5 text-[11px] text-[#0C831F]">
                        New for you — you haven&apos;t tried this category
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            </section>

            <section className="mt-7">
              <div className="mb-3 flex items-baseline justify-between">
                <h2 className="text-[20px] font-bold text-[#1C1C1C]">
                  Recent searches
                </h2>
                <button
                  type="button"
                  onClick={() => setRecents([])}
                  className="text-[13px] font-semibold text-[#0C831F]"
                >
                  clear
                </button>
              </div>
              {recents.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {recents.map((term) => (
                    <button
                      key={term}
                      type="button"
                      onClick={() => onQueryChange(term)}
                      className="inline-flex items-center gap-1.5 rounded-full border border-zinc-300 bg-white px-3 py-1.5 text-[12px] text-[#1C1C1C]"
                    >
                      <span className="text-[#7E8794]" aria-hidden>
                        ⌕
                      </span>
                      {term}
                    </button>
                  ))}
                </div>
              )}
            </section>

            <section className="mt-7">
              <h2 className="mb-3 text-[20px] font-bold text-[#1C1C1C]">
                Top picks for you
              </h2>
              <div className="-mx-3.5 flex gap-3 overflow-x-auto px-3.5 pb-1">
                {TOP_PICKS.map((p, i) => (
                  <ProductCard
                    key={p.name}
                    product={p}
                    color={THUMB[i % THUMB.length]}
                    onAdd={() => setCartCount((c) => c + 1)}
                  />
                ))}
              </div>
            </section>
          </>
        )}

        {q && matches.length > 0 && (
          <ul className="space-y-1">
            {matches.map((p, i) => (
              <li key={p.name}>
                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-lg px-1 py-2 text-left hover:bg-white/60"
                >
                  <span
                    className="h-10 w-10 shrink-0 rounded-lg"
                    style={{ background: THUMB[i % THUMB.length] }}
                  />
                  <span className="text-[14px]">
                    <HighlightMatch text={p.name} query={q} />
                  </span>
                </button>
              </li>
            ))}
            {showIceHint && (
              <li>
                <button
                  type="button"
                  onClick={() => openDemand(iceDemand)}
                  className="mt-1 flex w-full items-center gap-3 rounded-xl border border-[#0C831F]/25 bg-[#EAF7EE] px-3 py-2.5 text-left"
                >
                  <span className="h-10 w-10 shrink-0 rounded-lg bg-[#F8CB46]" />
                  <span className="text-[13px] font-semibold text-[#0C831F]">
                    Ice cream · 214 ordered near you tonight · new for you
                  </span>
                </button>
              </li>
            )}
          </ul>
        )}

        {q && matches.length === 0 && (
          <>
            {showIceHint && (
              <button
                type="button"
                onClick={() => openDemand(iceDemand)}
                className="mb-3 flex w-full items-center gap-3 rounded-xl border border-[#0C831F]/25 bg-[#EAF7EE] px-3 py-2.5 text-left"
              >
                <span className="h-10 w-10 shrink-0 rounded-lg bg-[#F8CB46]" />
                <span className="text-[13px] font-semibold text-[#0C831F]">
                  Ice cream · 214 ordered near you tonight · new for you
                </span>
              </button>
            )}
            <div className="rounded-2xl border border-dashed border-zinc-300 bg-white px-4 py-8 text-center">
              <p className="text-[13px] text-[#7E8794]">Looking for alternatives…</p>
            </div>
          </>
        )}
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-4 z-30 flex justify-center">
        <div className="pointer-events-auto flex items-center gap-2 rounded-full bg-[#1C1C1C] px-5 py-2.5 text-[13px] font-medium text-white shadow-lg">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#F8CB46] text-[11px] font-bold text-[#1C1C1C]">
            {cartCount}
          </span>
          View cart
        </div>
      </div>

      {activeDemand && (
        <BottomSheet
          demand={activeDemand}
          products={productsFor(activeDemand)}
          onClose={() => setActiveDemand(null)}
          onAdd={() => setCartCount((c) => c + 1)}
        />
      )}
    </div>
  );
}
