// Shared page behaviour: sticky bar shadow, fade-up on scroll, count-up numbers, compare slider.
(() => {
  const bar = document.getElementById('bar');
  if (bar) {
    const onScroll = () => bar.classList.toggle('solid', scrollY > 8);
    addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const countUp = n => {
    const end = +n.dataset.count, t0 = performance.now(), dur = 1600;
    const tick = t => {
      const p = Math.min((t - t0) / dur, 1), k = 1 - Math.pow(1 - p, 3);
      n.textContent = Math.round(end * k).toLocaleString('en-US');
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  const io = new IntersectionObserver(entries => entries.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add('in'); io.unobserve(e.target);
    const n = e.target.querySelector('[data-count]');
    if (n && !reduce) countUp(n);
  }), { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));

  // Hero video: tap once to get the normal player controls (play/pause, timeline, fullscreen)
  const hero = document.getElementById('hero-video');
  if (hero) hero.addEventListener('click', () => { if (!hero.controls) { hero.controls = true; hero.play(); } });

  // Swipeable project media: dots follow the scroll position
  document.querySelectorAll('.media').forEach(strip => {
    const dots = strip.nextElementSibling?.classList.contains('media-dots') ? [...strip.nextElementSibling.children] : [];
    const mark = () => { const i = Math.round(strip.scrollLeft / strip.clientWidth); dots.forEach((d, k) => d.classList.toggle('on', k === i)); };
    strip.addEventListener('scroll', mark, { passive: true }); mark();
  });

  const cmp = document.getElementById('cmp');
  if (cmp) {
    const [bottom, top] = cmp.querySelectorAll('video');
    cmp.querySelector('input').addEventListener('input', e => cmp.style.setProperty('--pos', e.target.value + '%'));
    setInterval(() => { if (Math.abs(top.currentTime - bottom.currentTime) > 0.15) top.currentTime = bottom.currentTime; }, 1000);
  }
})();
