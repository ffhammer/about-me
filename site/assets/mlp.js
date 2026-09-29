// MLP scroll indicator: one small net for the whole page = the scroll position.
// Layers you scrolled past keep firing, the current layer glows bright blue, and a front of
// blue dots on the connections sits exactly at the current scroll position. Layers below are idle (black).
// Desktop: vertical column on the right. Phone: horizontal strip at the bottom.
(() => {
  const WIDTH = 3;                                   // nodes per layer
  let BLUE = '#2F63D8', BRIGHT = '#3D86FF', INK = '#1E2420';
  const readColours = () => { const cs = getComputedStyle(document.documentElement);   // follow the site theme
    BLUE = cs.getPropertyValue('--mlp').trim() || BLUE; BRIGHT = cs.getPropertyValue('--mlp-bright').trim() || BRIGHT; INK = cs.getPropertyValue('--text').trim() || INK; };
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // stable pseudo-random "weights"
  const rand = (...k) => { let h = 2166136261; for (const c of k.join('|')) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
    h += 0x6D2B79F5; h = Math.imul(h ^ h >>> 15, h | 1); h ^= h + Math.imul(h ^ h >>> 7, h | 61); return ((h ^ h >>> 14) >>> 0) / 4294967296; };

  const box = document.createElement('div');
  box.className = 'mlp'; box.setAttribute('aria-hidden', 'true');
  box.innerHTML = '<canvas></canvas>';
  document.body.append(box);
  const canvas = box.querySelector('canvas'), ctx = canvas.getContext('2d');

  let W = 0, H = 0, vertical = true, L = 9;

  function resize() {
    vertical = innerWidth >= 1100;
    const r = canvas.getBoundingClientRect(), dpr = devicePixelRatio || 1;
    W = r.width; H = r.height;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // as many layers as fit comfortably along the flow axis
    L = Math.max(5, Math.min(vertical ? 9 : 12, Math.floor((vertical ? H : W) / (vertical ? 52 : 34))));
  }

  const progress = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    return max > 0 ? Math.min(1, Math.max(0, scrollY / max)) : 1;
  };

  // node position: layer k along the flow axis, node j across it
  function pos(k, j) {
    const padA = vertical ? 12 : 16, padC = vertical ? 14 : 11;
    const along = padA + (k / (L - 1)) * ((vertical ? H : W) - 2 * padA);
    const across = padC + (j / (WIDTH - 1)) * ((vertical ? W : H) - 2 * padC);
    return vertical ? [across, along] : [along, across];
  }

  function draw(time) {
    readColours();
    const p = progress() * (L - 1), k0 = Math.min(Math.floor(p), L - 2), f = p - k0;   // current segment k0 -> k0+1
    const r = vertical ? 5.5 : 4;
    ctx.clearRect(0, 0, W, H);

    // soft highlight band around the current position
    const [bx, by] = pos(p, 0), band = vertical ? 16 : 12;
    ctx.fillStyle = BRIGHT; ctx.globalAlpha = 0.08;
    if (vertical) ctx.fillRect(0, by - band, W, 2 * band); else ctx.fillRect(bx - band, 0, 2 * band, H);

    // connections
    for (let k = 0; k < L - 1; k++) for (let a = 0; a < WIDTH; a++) for (let b = 0; b < WIDTH; b++) {
      const [x1, y1] = pos(k, a), [x2, y2] = pos(k + 1, b), w = rand(k, a, b);
      ctx.lineWidth = 0.6;
      if (k < k0) {                       // finished: blue, weighted, occasional firing pulses
        ctx.strokeStyle = BLUE; ctx.globalAlpha = 0.15 + 0.4 * w;
        line(x1, y1, x2, y2);
        if (!reduce && w > 0.72) {
          const t = ((time / 1600) + rand(k, a, b, 'o')) % 1;
          dot(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, vertical ? 2.4 : 1.9, BLUE, 0.85, 4);
        }
      } else if (k === k0) {              // current: filled up to the scroll position, dots on the front
        ctx.strokeStyle = INK; ctx.globalAlpha = 0.12; line(x1, y1, x2, y2);
        if (w > 0.35) {
          const fx = x1 + (x2 - x1) * f, fy = y1 + (y2 - y1) * f;
          ctx.strokeStyle = BRIGHT; ctx.globalAlpha = 0.35 + 0.45 * w; ctx.lineWidth = 1.6; line(x1, y1, fx, fy);
          dot(fx, fy, vertical ? 3.4 : 2.6, BRIGHT, 1, 10);
        }
      } else {                            // not reached yet
        ctx.strokeStyle = INK; ctx.globalAlpha = 0.12; line(x1, y1, x2, y2);
      }
    }

    // nodes
    for (let k = 0; k < L; k++) for (let j = 0; j < WIDTH; j++) {
      const [x, y] = pos(k, j);
      dot(x, y, r, INK, 1);
      if (k < k0 || (k === k0 && f > 0)) {               // fired: blue, flickering a little
        const w = rand(k, j, 'n'), flick = reduce ? 1 : 0.85 + 0.15 * Math.sin(time / 500 + w * 12);
        dot(x, y, r + 0.3, k === k0 ? BRIGHT : BLUE, (k === k0 ? 1 : 0.35 + 0.6 * w) * flick, k === k0 ? 8 : 0);
      }
      if (k === k0 + 1 && f > 0.02) dot(x, y, r + 0.3, BRIGHT, f, 8 * f);   // next layer lights up as you arrive
    }
    // ring around the current layer
    for (let j = 0; j < WIDTH; j++) {
      const [x, y] = pos(f < 0.5 ? k0 : k0 + 1, j);
      ctx.globalAlpha = 0.55; ctx.strokeStyle = BRIGHT; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(x, y, r + 3 + (reduce ? 0 : Math.sin(time / 300) * 0.8), 0, 7); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  function line(x1, y1, x2, y2) { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); }
  function dot(x, y, r, colour, alpha, glow = 0) {
    ctx.globalAlpha = alpha; ctx.fillStyle = colour;
    if (glow) { ctx.shadowColor = colour; ctx.shadowBlur = glow; }
    ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
    ctx.shadowBlur = 0;
  }

  let queued = false;
  const frame = time => { queued = false; draw(time); if (!reduce) queue(); };
  const queue = () => { if (!queued) { queued = true; requestAnimationFrame(frame); } };
  addEventListener('resize', () => { resize(); queue(); });
  addEventListener('scroll', queue, { passive: true });
  resize(); queue();
})();
