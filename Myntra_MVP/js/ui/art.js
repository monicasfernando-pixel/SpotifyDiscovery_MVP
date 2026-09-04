export const SPARKLE_SVG = `<svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true"><path d="M12 3.2 13.1 8 18 9.2 13.1 10.4 12 15.2 10.9 10.4 6 9.2 10.9 8z" fill="currentColor"/><path d="M18.2 14.2 18.8 16.4 21 17l-2.2.6-.6 2.2-.6-2.2-2.2-.6 2.2-.6zM5.4 13.4l.5 1.6 1.6.5-1.6.5-.5 1.6-.5-1.6-1.6-.5 1.6-.5z" fill="currentColor"/></svg>`;

export function art(kind) {
  const scenes = {
    kurta: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#f3ddd0"/><rect x="0" y="0" width="180" height="240" fill="#c45c48" opacity=".12"/><path d="M90 38c14 0 22 10 22 18v8l18 10 8 86c-16 22-32 34-48 34s-32-12-48-34l8-86 18-10v-8c0-8 8-18 22-18z" fill="#9b2d3a"/><path d="M68 66h44l-4 92H72z" fill="#c45c48"/><circle cx="90" cy="78" r="4" fill="#e8c56b"/><path d="M72 120h36M74 136h32" stroke="#e8c56b" stroke-width="1.4" opacity=".7"/></svg>`,
    heels: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#f4eadc"/><path d="M36 150c28-8 54-28 78-32 16-3 32 2 40 10l8 8c-18 6-30 8-40 22-4 6-6 14 2 22l-70 8c-10-20-16-28-18-38z" fill="#c4a484"/><path d="M122 158v36c0 6 6 10 14 8 6-2 8-8 8-14v-22z" fill="#8d6b4a"/><ellipse cx="86" cy="198" rx="52" ry="7" fill="#d7c4aa"/></svg>`,
    watch: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#e4e7ee"/><rect x="78" y="28" width="24" height="52" rx="6" fill="#2c3038"/><rect x="78" y="160" width="24" height="52" rx="6" fill="#2c3038"/><circle cx="90" cy="120" r="38" fill="#1f232b" stroke="#c5c9d1" stroke-width="6"/><circle cx="90" cy="120" r="28" fill="#f4f1ea"/><path d="M90 120v-16M90 120l12 8" stroke="#1f232b" stroke-width="2.4" stroke-linecap="round"/><circle cx="90" cy="120" r="3" fill="#c45c48"/></svg>`,
    shirt: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#e7eef6"/><path d="M46 58l28-16 16 18 16-18 28 16-12 22v96H58V80z" fill="#6fa0c8"/><path d="M74 42l16 20 16-20-8-8h-16z" fill="#dbe7f2"/><circle cx="90" cy="86" r="2.4" fill="#eef4fa"/><circle cx="90" cy="104" r="2.4" fill="#eef4fa"/><circle cx="90" cy="122" r="2.4" fill="#eef4fa"/></svg>`,
    wedges: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#f6e6d8"/><path d="M40 148c30-6 58-24 82-22 14 1 28 8 34 16l-8 10c-16 4-28 2-38 14-18 22-36 32-70 28z" fill="#a56b45"/><path d="M118 156l18 40H58c8-20 28-36 60-40z" fill="#7a4a2c"/><ellipse cx="90" cy="202" rx="50" ry="6" fill="#d8b89a"/></svg>`,
    crocs: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#f3e4ee"/><ellipse cx="92" cy="150" rx="58" ry="28" fill="#e28bb8"/><path d="M40 148c8-22 36-36 70-28 18 4 32 16 36 28-20 16-50 24-84 16-10-2-18-8-22-16z" fill="#f0a3c8"/><circle cx="70" cy="138" r="4" fill="#f8d5e6"/><circle cx="86" cy="132" r="4" fill="#f8d5e6"/><circle cx="102" cy="136" r="4" fill="#f8d5e6"/><circle cx="78" cy="148" r="3.4" fill="#f8d5e6"/><circle cx="96" cy="146" r="3.4" fill="#f8d5e6"/></svg>`,
    jeans: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#d9e2ee"/><path d="M62 36h56l8 20-10 150H64L54 56z" fill="#3b5c8a"/><path d="M90 56v150" stroke="#2a4568" stroke-width="2"/><rect x="70" y="48" width="40" height="10" rx="2" fill="#c8a25a"/></svg>`,
    tee: `<svg viewBox="0 0 180 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="180" height="240" fill="#ece7e2"/><path d="M44 70l32-20 14 16 14-16 32 20-14 18v90H58V88z" fill="#2b2f36"/><path d="M76 50c6 12 22 12 28 0" fill="none" stroke="#ece7e2" stroke-width="3"/></svg>`,
  };
  return scenes[kind] || scenes.shirt;
}

export function iconSvg(name) {
  if (name === "check") {
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5 9.2 17 19 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }
  if (name === "clock") {
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M12 8v5l3 2" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>`;
  }
  if (name === "help") {
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.6 2.2c-.8.4-1.2 1-1.2 2" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="16.6" r="1" fill="currentColor"/></svg>`;
  }
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M8 8l8 8M16 8l-8 8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>`;
}
