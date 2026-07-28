import PhoneSim from "@/components/PhoneSim";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-5 bg-[#F0F0EC] px-4 py-10">
      <p className="max-w-md text-center text-[15px] font-medium leading-snug text-zinc-800">
        Your search bar knows what your neighbourhood is buying.
      </p>

      <div className="relative h-[840px] w-[390px] overflow-hidden rounded-[2rem] border border-zinc-200 bg-white shadow-[0_20px_60px_rgba(0,0,0,0.12)]">
        <PhoneSim />
      </div>

      <p className="text-[12px] text-zinc-500">
        Simulation — Blinkit-style quick commerce.
      </p>
    </main>
  );
}
