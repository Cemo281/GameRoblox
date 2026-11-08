const { CompositionStage, useComposition, Shot, Easing, animate, clamp, useTweaks, TweaksPanel, TweakSection, TweakSelect, TweakRadio, TweakSlider, TweakToggle } = window;

const ORDRE = ['Commun', 'Rare', 'Légendaire', 'Mythique', 'Secret'];
const RARETES = {
  Commun: { hex: '#A3A2A5', light: '#E4E3E6', dark: '#5C5B60', glow: 'rgba(228,227,230,.8)' },
  Rare: { hex: '#0078FF', light: '#6CC0FF', dark: '#003A80', glow: 'rgba(108,192,255,.85)' },
  'Légendaire': { hex: '#FFBE00', light: '#FFE98A', dark: '#8A5A00', glow: 'rgba(255,233,138,.9)' },
  Mythique: { hex: '#C800FF', light: '#EBA0FF', dark: '#5A0080', glow: 'rgba(235,160,255,.9)' },
  Secret: { hex: '#FF2828', light: '#FF9A9A', dark: '#6E0606', glow: 'rgba(255,154,154,.95)' },
};
const PERSOS = { A: { img: 'img/perso_a_pied.png', nom: 'Capitaine', base: 100 }, B: { img: 'img/perso_b_pied.png', nom: 'Sabreur', base: 90 } };
const INK = '#0D0A1C';
const OUT = (w, c = INK) => `0 ${w}px 0 ${c}, ${w}px 0 0 ${c}, -${w}px 0 0 ${c}, 0 -${w}px 0 ${c}, ${w}px ${w}px 0 ${c}, -${w}px ${w}px 0 ${c}`;

// Three motion helpers — every move goes through these.
const MOTION = {
  enter: (from, to, start, end) => animate({ from, to, start, end, ease: Easing.easeOutCubic }),
  pop: (from, to, start, end) => animate({ from, to, start, end, ease: Easing.easeOutBack }),
  snap: (from, to, start, end) => animate({ from, to, start, end, ease: Easing.easeInOutQuart }),
};

// Rarity climb: one step per tier up to the drawn rarity, spread over the "Montee" section.
function paliers(C, cible) {
  const n = ORDRE.indexOf(cible) + 1;
  const start = C.Montee + 0.2, span = C.Impact - C.Montee - 0.5;
  return ORDRE.slice(0, n).map((nom, i) => ({ nom, t: start + (n === 1 ? span * 0.3 : (i * span) / (n - 1)) }));
}
function palierActuel(T, P) { let k = -1; P.forEach((p, i) => { if (T >= p.t) k = i; }); return k; }

function Fond({ T, C, R, cur, total }) {
  const rev = MOTION.enter(0, 1, C.Impact + 0.2, C.Revelation + 0.6)(T);
  const out = MOTION.snap(1, 0, total - 0.8, total)(T);
  const tierOp = cur ? MOTION.enter(0.25, 0.55, C.Montee, C.Impact)(T) : 0;
  const colT = cur ? RARETES[cur.nom] : R;
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 60%, #1E1838 0%, #0C0A1A 55%, #040308 100%)' }} />
      <div style={{ position: 'absolute', inset: 0, opacity: T < C.Impact ? tierOp * out : 0, background: `radial-gradient(ellipse at 50% 62%, ${colT.hex} 0%, ${colT.dark} 30%, rgba(4,3,8,0) 65%)` }} />
      <div style={{ position: 'absolute', inset: 0, opacity: rev * out * 0.9, background: `radial-gradient(ellipse at 50% 50%, ${R.hex} 0%, ${R.dark} 40%, rgba(4,3,8,0) 75%)` }} />
      <div style={{ position: 'absolute', inset: 0, opacity: (tierOp * 0.5 + rev * 0.45) * out, background: 'radial-gradient(circle, rgba(255,255,255,.2) 1.6px, rgba(255,255,255,0) 2.2px) 0 0/12px 12px', WebkitMaskImage: 'radial-gradient(ellipse at 50% 50%, transparent 30%, #000 85%)', maskImage: 'radial-gradient(ellipse at 50% 50%, transparent 30%, #000 85%)' }} />
    </div>
  );
}

function Projecteur({ T, C, cur, total }) {
  const on = MOTION.enter(0, 1, 0.1, 1.0)(T) * MOTION.snap(1, 0, C.Impact, C.Impact + 0.3)(T);
  const col = cur ? RARETES[cur.nom].light : '#FFFFFF';
  const flick = 0.9 + Math.sin(T * 23) * 0.05;
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: on * flick * MOTION.snap(1, 0, total - 0.8, total)(T), pointerEvents: 'none' }}>
      <div style={{ position: 'absolute', left: 350, top: -40, width: 400, height: 620, background: `linear-gradient(180deg, ${col}55, ${col}10 70%, rgba(255,255,255,0))`, clipPath: 'polygon(42% 0, 58% 0, 100% 100%, 0 100%)' }} />
      <div style={{ position: 'absolute', left: 390, top: 500, width: 320, height: 70, borderRadius: '50%', background: `radial-gradient(closest-side, ${col}66, rgba(255,255,255,0))` }} />
    </div>
  );
}

// Classic R6 rig in real 3D: 6 cuboids projected to SVG polygons (painter's sort, rim lighting).
const hx = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const mixC = (a, b, k) => { const A = hx(a), B = hx(b); return 'rgb(' + A.map((v, i) => Math.round(v + (B[i] - v) * clamp(k, 0, 1))).join(',') + ')'; };
const PARTS = [
  { c: [0, 1, 0], s: [0.96, 2, 0.96], pivot: [0, 2, 0], sw: 'legL', dx: -0.5 },
  { c: [0, 1, 0], s: [0.96, 2, 0.96], pivot: [0, 2, 0], sw: 'legR', dx: 0.5 },
  { c: [0, 3, 0], s: [2, 2, 1], dx: 0 },
  { c: [0, 3, 0], s: [0.96, 2, 0.96], pivot: [0, 4, 0], sw: 'armL', dx: -1.5 },
  { c: [0, 3, 0], s: [0.96, 2, 0.96], pivot: [0, 4, 0], sw: 'armR', dx: 1.5 },
  { c: [0, 4.62, 0], s: [1.2, 1.2, 1.2], pivot: [0, 4, 0], sw: 'head', dx: 0 },
];
const FACES = [[0, 1, 2, 3, [0, 0, -1]], [5, 4, 7, 6, [0, 0, 1]], [4, 0, 3, 7, [-1, 0, 0]], [1, 5, 6, 2, [1, 0, 0]], [3, 2, 6, 7, [0, 1, 0]], [4, 5, 1, 0, [0, -1, 0]]];
function Rig({ yaw = 0, pitch = 10, swing = 0, headTilt = 0, base = '#07050D', rim = '#3A3462', flat = null, edge = 1 }) {
  const W = 360, H = 400, S = 50, CX = 180, GY = 372, F = 14;
  const ry = yaw * Math.PI / 180, rp = pitch * Math.PI / 180;
  const rotX = (v, a, p) => { const y = v[1] - p[1], z = v[2] - p[2]; return [v[0], p[1] + y * Math.cos(a) - z * Math.sin(a), p[2] + y * Math.sin(a) + z * Math.cos(a)]; };
  const rotZ = (v, a, p) => { const x = v[0] - p[0], y = v[1] - p[1]; return [p[0] + x * Math.cos(a) - y * Math.sin(a), p[1] + x * Math.sin(a) + y * Math.cos(a), v[2]]; };
  const world = v => { const x = v[0] * Math.cos(ry) + v[2] * Math.sin(ry), z = -v[0] * Math.sin(ry) + v[2] * Math.cos(ry); const y = v[1] - 2.6; return [x, 2.6 + y * Math.cos(rp) - z * Math.sin(rp), y * Math.sin(rp) + z * Math.cos(rp)]; };
  const proj = v => { const k = F / (F - v[2]); return [CX + v[0] * S * k, GY - v[1] * S * k]; };
  const ang = { legL: -swing * 0.6, legR: swing * 0.6, armL: swing, armR: -swing, head: 0 };
  const polys = [];
  PARTS.forEach((p, pi) => {
    const [sx, sy, sz] = p.s, c = [p.c[0] + p.dx, p.c[1], p.c[2]];
    let V = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]].map(([x, y, z]) => [c[0] + x * sx / 2, c[1] + y * sy / 2, c[2] + z * sz / 2]);
    const a = (ang[p.sw] || 0) * Math.PI / 180, pv = p.pivot ? [c[0], p.pivot[1], 0] : null;
    if (pv && p.sw !== 'head') V = V.map(v => rotX(v, a, pv));
    if (p.sw === 'head') V = V.map(v => rotZ(v, headTilt * Math.PI / 180, pv));
    const Wv = V.map(world);
    const PC = Wv.reduce((s, v) => [s[0] + v[0] / 8, s[1] + v[1] / 8, s[2] + v[2] / 8], [0, 0, 0]);
    FACES.forEach(([i0, i1, i2, i3]) => {
      const cen = [i0, i1, i2, i3].map(i => Wv[i]).reduce((s, v) => [s[0] + v[0] / 4, s[1] + v[1] / 4, s[2] + v[2] / 4], [0, 0, 0]);
      let n = [cen[0] - PC[0], cen[1] - PC[1], cen[2] - PC[2]];
      const L = Math.hypot(...n) || 1; n = n.map(x => x / L);
      const toCam = [-cen[0], -cen[1] + 2.6, F - cen[2]], tl = Math.hypot(...toCam);
      if (n[0] * toCam[0] + n[1] * toCam[1] + n[2] * toCam[2] <= 0) return;
      const lam = clamp(n[0] * -0.35 + n[1] * 0.75 + n[2] * 0.55, 0, 1);
      const rimK = clamp(1 - Math.abs((n[0] * toCam[0] + n[1] * toCam[1] + n[2] * toCam[2]) / tl), 0, 1);
      const fill = flat || mixC(mixC(base, '#4A4080', 0.12 + lam * 0.6), rim, rimK * rimK * 0.75 + (n[1] > 0.6 ? 0.22 : 0) + (n[0] > 0.5 ? 0.12 : 0));
      polys.push({ z: cen[2], pts: [i0, i1, i2, i3].map(i => proj(Wv[i]).map(x => x.toFixed(1)).join(',')).join(' '), fill, key: pi + '-' + i0 + i1 });
    });
  });
  polys.sort((p, q) => p.z - q.z);
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
      {polys.map(p => <polygon key={p.key} points={p.pts} fill={p.fill} stroke={flat || rim} strokeOpacity={flat ? 1 : 0.55 * edge} strokeWidth={flat ? 1 : 1.4} strokeLinejoin="round" />)}
    </svg>
  );
}

function RigScene({ T, C, P, cur, total }) {
  const appear = MOTION.enter(0, 1, 0.2, 1.4)(T);
  const rise = MOTION.enter(40, 0, 0.2, 1.4)(T);
  let punch = 0, kick = 0;
  P.forEach(p => { const d = T - p.t; if (d >= 0 && d < 0.35) punch = Math.max(punch, Math.sin((d / 0.35) * Math.PI) * (1 - d / 0.35)); kick += 90 * Easing.easeOutCubic(clamp(d / 0.55, 0, 1)); });
  const charge = clamp((T - C.Montee) / (C.Impact - C.Montee), 0, 1);
  const tremble = T > C.Montee && T < C.Impact ? Math.sin(T * 64) * charge * charge * 2.5 : 0;
  const yaw = -30 + T * 22 + kick;
  const swing = 6 + Math.sin(T * 2.4) * 8 + punch * 22;
  const gone = MOTION.snap(1, 0, C.Impact + 0.25, C.Impact + 0.45)(T);
  const whiten = MOTION.enter(0, 1, C.Impact - 0.3, C.Impact + 0.05)(T);
  const R = cur ? RARETES[cur.nom] : null;
  const rim = R ? R.light : '#4A3F86';
  const base = whiten > 0 ? mixC('#07050D', '#FFFFFF', whiten) : '#07050D';
  const scale = (1 + punch * 0.08 + charge * 0.06) * MOTION.pop(0.85, 1, 0.2, 1.4)(T);
  return (
    <div style={{ position: 'absolute', left: 370, top: 150 + rise, width: 360, height: 400, opacity: appear * gone, transform: `scale(${scale}) rotate(${tremble}deg)`, transformOrigin: '50% 93%' }}>
      <div style={{ position: 'absolute', left: 30, top: 40, width: 300, height: 340, borderRadius: '50%', background: `radial-gradient(closest-side, ${R ? R.hex : '#2A2448'}${R ? '88' : '55'}, rgba(0,0,0,0))`, transform: `scale(${1 + punch * 0.4})` }} />
      <div style={{ position: 'absolute', left: 90, top: 356, width: 180, height: 30, borderRadius: '50%', background: 'rgba(0,0,0,.6)' }} />
      <Rig yaw={yaw} swing={swing} headTilt={Math.sin(T * 1.8) * 4} base={base} rim={whiten > 0.6 ? '#FFFFFF' : rim} />
    </div>
  );
}

function Ondes({ T, P }) {
  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      {P.map((p, i) => {
        const k = clamp((T - p.t) / 0.7, 0, 1);
        const vis = T >= p.t && k < 1;
        const R = RARETES[p.nom];
        return (
          <div key={i} style={{ position: 'absolute', left: 550 - 60, top: 400 - 60, width: 120, height: 120, borderRadius: '50%', border: `${6 - k * 4}px solid ${R.light}`, opacity: vis ? 1 - k : 0, transform: `scale(${0.6 + Easing.easeOutCubic(k) * 4.2})` }} />
        );
      })}
    </div>
  );
}

function Jauge({ T, C, P, cur, total }) {
  const on = MOTION.enter(0, 1, C.Montee - 0.1, C.Montee + 0.3)(T) * MOTION.snap(1, 0, C.Impact - 0.1, C.Impact + 0.15)(T);
  const idx = palierActuel(T, P);
  const last = idx >= 0 ? P[idx] : null;
  const k = last ? clamp((T - last.t) / 0.3, 0, 1) : 0;
  const R = cur ? RARETES[cur.nom] : RARETES.Commun;
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: 552, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, opacity: on }}>
      <div style={{ display: 'flex', gap: 10 }}>
        {ORDRE.map((nom, i) => {
          const lit = i <= idx; const r = RARETES[nom];
          return <div key={nom} style={{ width: 52, height: 12, borderRadius: 3, transform: 'skewX(-20deg)', background: lit ? `linear-gradient(180deg, ${r.light}, ${r.hex})` : '#1C1738', border: `1.5px solid ${lit ? INK : '#3E3478'}`, boxShadow: lit && i === idx ? `0 0 14px ${r.hex}` : 'none' }} />;
        })}
      </div>
    </div>
  );
}

function LabelPalier({ T, C, P, cur }) {
  if (!cur) return null;
  const idx = palierActuel(T, P), last = P[idx];
  const k = clamp((T - last.t) / 0.32, 0, 1);
  const s = 1 + (1 - Easing.easeOutBack(k)) * 1.2;
  const off = MOTION.snap(1, 0, C.Impact - 0.1, C.Impact + 0.1)(T);
  const R = RARETES[cur.nom];
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: 86, display: 'flex', justifyContent: 'center', opacity: off * clamp(k * 3, 0, 1) }}>
      <div style={{ transform: `rotate(-5deg) scale(${s})`, font: "400 58px 'Fredoka One'", color: '#FFFFFF', letterSpacing: 2, textShadow: `${OUT(4)}, 7px 9px 0 ${R.hex}` }}>{cur.nom.toUpperCase()}{idx > 0 ? ' !' : ''}</div>
    </div>
  );
}

function Particules({ T, C, R, cur, total }) {
  const on = MOTION.enter(0, 1, 0, 1.2)(T) * MOTION.snap(1, 0, total - 0.8, total)(T);
  const boost = T > C.Impact ? 2.4 : 1 + clamp((T - C.Montee) / 3, 0, 1);
  const col = T < C.Impact ? (cur ? RARETES[cur.nom].light : '#C9C3E6') : R.light;
  const pts = [];
  for (let i = 0; i < 30; i++) {
    const x = 120 + ((i * 397) % 860), sp = 40 + ((i * 53) % 60), y = 650 - ((T * sp * boost + i * 83) % 700), s = 2 + (i % 4);
    pts.push(<div key={i} style={{ position: 'absolute', left: x + Math.sin(T * 1.3 + i) * 14, top: y, width: s, height: s, borderRadius: s, background: col, opacity: on * (0.35 + (i % 3) * 0.2) }} />);
  }
  return <div style={{ position: 'absolute', inset: 0 }}>{pts}</div>;
}

function Impact({ T, C }) {
  const t0 = C.Impact + 0.05;
  const lines = 'repeating-conic-gradient(from 0deg, #FFFFFF 0deg 1.2deg, rgba(255,255,255,0) 1.2deg 4.5deg, #FFFFFF 4.5deg 5.4deg, rgba(255,255,255,0) 5.4deg 10deg)';
  const linesInk = 'repeating-conic-gradient(from 7deg, #0D0A1C 0deg 1.2deg, rgba(13,10,28,0) 1.2deg 4.5deg, #0D0A1C 4.5deg 5.4deg, rgba(13,10,28,0) 5.4deg 10deg)';
  const flash = T >= t0 + 0.3 ? MOTION.enter(1, 0, t0 + 0.3, t0 + 0.9)(T) : 0;
  return (
    <>
      <Shot from={t0} to={t0 + 0.14}>
        <div style={{ position: 'absolute', inset: 0, background: '#0D0A1C', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', left: -450, top: -620, width: 2000, height: 2000, background: `radial-gradient(closest-side, #0D0A1C 12%, rgba(13,10,28,0) 40%), ${lines}` }} />
          <div style={{ position: 'absolute', left: 370, top: 150, width: 360, height: 400, transform: 'scale(1.15)', transformOrigin: '50% 93%' }}><Rig flat="#FFFFFF" yaw={35} swing={24} headTilt={-4} /></div>
        </div>
      </Shot>
      <Shot from={t0 + 0.14} to={t0 + 0.3}>
        <div style={{ position: 'absolute', inset: 0, background: '#FFFFFF', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', left: -450, top: -620, width: 2000, height: 2000, background: `radial-gradient(closest-side, #FFFFFF 14%, rgba(255,255,255,0) 42%), ${linesInk}`, transform: 'scale(1.2)' }} />
          <div style={{ position: 'absolute', left: 370, top: 150, width: 360, height: 400, transform: 'scale(1.22) rotate(-3deg)', transformOrigin: '50% 93%' }}><Rig flat="#0D0A1C" yaw={-30} swing={-30} headTilt={6} /></div>
        </div>
      </Shot>
      <div style={{ position: 'absolute', inset: 0, background: '#FFFFFF', opacity: flash, pointerEvents: 'none' }} />
    </>
  );
}

function Rayons({ T, C, R, total }) {
  const on = MOTION.pop(0, 1, C.Impact + 0.3, C.Revelation + 0.4)(T) * MOTION.snap(1, 0, total - 0.8, total)(T);
  const spin = T * 18;
  return (
    <div style={{ position: 'absolute', left: 150, top: -110, width: 800, height: 800, opacity: clamp(on, 0, 1), transform: `scale(${0.4 + on * 0.6})` }}>
      <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', transform: `rotate(${spin}deg)`, background: `radial-gradient(closest-side, rgba(4,3,8,0) 18%, rgba(4,3,8,1) 100%), repeating-conic-gradient(from 0deg, ${R.light}99 0deg 6deg, rgba(0,0,0,0) 6deg 22.5deg)` }} />
      <div style={{ position: 'absolute', inset: 120, borderRadius: '50%', transform: `rotate(${-spin * 1.4}deg)`, background: 'radial-gradient(closest-side, rgba(4,3,8,0) 25%, rgba(4,3,8,1) 100%), repeating-conic-gradient(from 10deg, rgba(255,255,255,.4) 0deg 3deg, rgba(0,0,0,0) 3deg 15deg)' }} />
    </div>
  );
}

function Heros({ T, C, R, perso, total }) {
  const s = C.Impact + 0.35;
  const rise = MOTION.pop(0, 1, s, s + 0.8)(T);
  const silh = MOTION.enter(1, 0, s + 0.1, s + 0.7)(T);
  const breathe = 1 + Math.sin(T * 2) * 0.012;
  const push = 1 + MOTION.enter(0, 0.05, C.Pose, total)(T);
  const out = MOTION.snap(1, 0, total - 0.8, total - 0.2)(T);
  return (
    <div style={{ position: 'absolute', left: 310, top: 50, width: 480, height: 540, opacity: clamp(rise, 0, 1) * out, transform: `translateY(${(1 - rise) * 60}px) scale(${(0.7 + rise * 0.3) * breathe * push})`, transformOrigin: '50% 92%' }}>
      <div style={{ position: 'absolute', left: 40, top: 50, width: 400, height: 400, borderRadius: '50%', background: `radial-gradient(closest-side, ${R.glow}, rgba(255,255,255,0))` }} />
      <div style={{ position: 'absolute', left: 90, bottom: 22, width: 300, height: 40, borderRadius: '50%', background: 'rgba(4,3,8,.6)' }} />
      <img src={perso.img} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain' }} />
      <img src={perso.img} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain', filter: 'brightness(0)', opacity: silh }} />
    </div>
  );
}

function Titres({ T, C, R, rarete, perso, etoiles, total }) {
  const s = C.Revelation + 0.2;
  const stamp = MOTION.pop(2.4, 1, s, s + 0.35)(T);
  const stampOp = clamp(MOTION.enter(0, 1, s, s + 0.15)(T), 0, 1);
  const ribbon = MOTION.enter(-700, 0, s + 0.35, s + 0.85)(T);
  const name = MOTION.enter(-40, 0, s + 0.55, s + 1.0)(T);
  const nameOp = clamp(MOTION.enter(0, 1, s + 0.55, s + 0.9)(T), 0, 1);
  const out = MOTION.snap(1, 0, total - 0.8, total - 0.2)(T);
  const info = clamp(MOTION.enter(0, 1, C.Pose, C.Pose + 0.6)(T), 0, 1);
  const revenu = Math.round(perso.base * (1 + 0.2 * etoiles));
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: out }}>
      <div style={{ position: 'absolute', left: 56, top: 54, opacity: stampOp, transform: `rotate(-6deg) scale(${stamp})`, transformOrigin: '0 50%' }}>
        <div style={{ font: "400 64px 'Fredoka One'", color: '#FFFFFF', letterSpacing: 2, textShadow: `${OUT(4)}, 8px 10px 0 ${R.hex}` }}>{rarete.toUpperCase()} !</div>
      </div>
      <div style={{ position: 'absolute', left: 0, top: 452, transform: `translateX(${ribbon}px) rotate(-4deg)`, transformOrigin: '0 50%' }}>
        <div style={{ position: 'relative', width: 620, height: 92, background: `linear-gradient(90deg, ${R.dark} 0%, ${R.hex} 60%, rgba(0,0,0,0) 100%)`, clipPath: 'polygon(0 0, 100% 0, 92% 100%, 0 100%)' }}>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 6, height: 2, background: 'linear-gradient(90deg, #FFD66B, rgba(255,214,107,0))' }} />
          <div style={{ position: 'absolute', left: 0, right: 0, bottom: 6, height: 2, background: 'linear-gradient(90deg, #FFD66B, rgba(255,214,107,0))' }} />
          <div style={{ position: 'absolute', left: 64, top: 8, opacity: nameOp, transform: `translateX(${name}px)`, font: "400 62px 'Fredoka One'", color: '#FFFFFF', textShadow: OUT(3), whiteSpace: 'nowrap' }}>{perso.nom}</div>
        </div>
      </div>
      <div style={{ position: 'absolute', left: 74, top: 560, display: 'flex', gap: 8, transform: 'rotate(-4deg)' }}>
        {[1, 2, 3, 4, 5].map(i => {
          const st = s + 1.0 + i * 0.22, on = i <= etoiles;
          const k = on ? MOTION.pop(0, 1, st, st + 0.3)(T) : clamp(MOTION.enter(0, 1, s + 0.9, s + 1.2)(T), 0, 1);
          return <img key={i} src={on ? 'icons2/etoile.svg' : 'icons2/etoile_vide.svg'} style={{ width: 46, height: 46, opacity: clamp(k, 0, 1), transform: `scale(${on ? k : 1}) rotate(${on ? (1 - clamp(k, 0, 1)) * -120 : 0}deg)` }} />;
        })}
      </div>
      <div style={{ position: 'absolute', right: 60, bottom: 46, opacity: info, transform: `translateY(${(1 - info) * 20}px)`, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ height: 40, padding: '0 14px 0 8px', display: 'flex', alignItems: 'center', gap: 6, borderRadius: 10, background: 'rgba(13,10,28,.85)', border: '1.5px solid #3E3478', font: "400 20px 'Fredoka One'", color: '#7DF08A' }}>
          <img src="icons/billets.png" style={{ width: 26, height: 26 }} />+{revenu} $/s
        </div>
        <div style={{ position: 'relative', height: 50, padding: '0 28px', display: 'flex', alignItems: 'center', borderRadius: 12, border: `2px solid ${INK}`, background: 'linear-gradient(180deg,#B6FFB0,#5EE06A 50%,#2FAE45)', boxShadow: '0 3px 0 #1E8A33', font: "400 22px 'Fredoka One'", color: '#0B2A10', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: '48%', background: 'rgba(255,255,255,.3)' }} />
          <span style={{ position: 'relative' }}>Super !</span>
        </div>
      </div>
    </div>
  );
}

function Piece({ t }) {
  const { T, CUES, authoredTotal } = useComposition();
  const rarete = ORDRE.includes(t.rarete) ? t.rarete : 'Mythique';
  const R = RARETES[rarete];
  const perso = { ...(PERSOS[t.perso] || PERSOS.B) };
  if (rarete === 'Secret') perso.nom += ' Éveillé';
  const total = authoredTotal;
  const P = paliers(CUES, rarete);
  const idx = palierActuel(T, P);
  const cur = idx >= 0 ? P[idx] : null;
  let shake = 0;
  P.forEach((p, i) => { const d = T - p.t; if (d >= 0 && d < 0.3) shake = Math.sin(d * 120) * (3 + i * 2.5) * (1 - d / 0.3); });
  if (T > CUES.Impact + 0.3 && T < CUES.Impact + 0.9) shake = Math.sin(T * 90) * 10 * (1 - (T - CUES.Impact - 0.3) / 0.6);
  return (
    <div data-screen-label={`t=${Math.floor(T)}s`} style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: '#040308' }}>
      <div style={{ position: 'absolute', inset: 0, transform: `translate(${shake}px, ${shake * 0.5}px)` }}>
        <Fond T={T} C={CUES} R={R} cur={cur} total={total} />
        <Rayons T={T} C={CUES} R={R} total={total} />
        <Projecteur T={T} C={CUES} cur={cur} total={total} />
        <Particules T={T} C={CUES} R={R} cur={cur} total={total} />
        <Ondes T={T} P={P} />
        <RigScene T={T} C={CUES} P={P} cur={cur} total={total} />
        <LabelPalier T={T} C={CUES} P={P} cur={cur} />
        <Jauge T={T} C={CUES} P={P} cur={cur} total={total} />
        <Heros T={T} C={CUES} R={R} perso={perso} total={total} />
        <Titres T={T} C={CUES} R={R} rarete={rarete} perso={perso} etoiles={t.etoiles} total={total} />
      </div>
      <Impact T={T} C={CUES} />
    </div>
  );
}

function TirageAnim() {
  const [t, setTweak] = useTweaks(window.TWEAK_DEFAULTS);
  return (
    <>
      <CompositionStage width={1100} height={650} scenes={window.OM_SCENES} playback={window.OM_PLAYBACK} bg="#040308">
        <Piece t={t} />
      </CompositionStage>
      <TweaksPanel>
        <TweakSection label="Tirage" />
        <TweakSelect label="Rareté finale" value={t.rarete} options={ORDRE} onChange={v => setTweak('rarete', v)} />
        <TweakRadio label="Personnage" value={t.perso} options={['A', 'B']} onChange={v => setTweak('perso', v)} />
        <TweakSlider label="Étoiles" value={t.etoiles} min={1} max={5} step={1} onChange={v => setTweak('etoiles', v)} />
        <TweakSection label="Éditeur" />
        <TweakToggle label="Motion editor" value={t.motionEditor} onChange={v => setTweak('motionEditor', v)} />
      </TweaksPanel>
    </>
  );
}

window.TirageAnim = TirageAnim;
