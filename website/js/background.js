(function () {
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let width = 0;
  let height = 0;
  let nodes = [];
  let animationId = null;

  const NODE_COUNT = prefersReduced ? 0 : 48;
  const CONNECT_DIST = 140;
  const MOUSE = { x: -1000, y: -1000, active: false };

  function resize() {
    const wrap = canvas.parentElement;
    width = wrap.offsetWidth;
    height = wrap.offsetHeight;
    canvas.width = width * devicePixelRatio;
    canvas.height = height * devicePixelRatio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  }

  function initNodes() {
    nodes = Array.from({ length: NODE_COUNT }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      r: Math.random() * 1.5 + 0.5,
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    const gradient = ctx.createRadialGradient(
      width * 0.5, height * 0.3, 0,
      width * 0.5, height * 0.3, width * 0.6
    );
    gradient.addColorStop(0, 'rgba(255, 255, 255, 0.04)');
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      a.x += a.vx;
      a.y += a.vy;
      if (a.x < 0 || a.x > width) a.vx *= -1;
      if (a.y < 0 || a.y > height) a.vy *= -1;

      if (MOUSE.active) {
        const dx = MOUSE.x - a.x;
        const dy = MOUSE.y - a.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 180) {
          a.x -= dx * 0.008;
          a.y -= dy * 0.008;
        }
      }

      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.hypot(dx, dy);
        if (dist < CONNECT_DIST) {
          const alpha = (1 - dist / CONNECT_DIST) * 0.12;
          ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }

    for (const node of nodes) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
      ctx.fill();
    }

    animationId = requestAnimationFrame(draw);
  }

  resize();
  initNodes();
  if (!prefersReduced && NODE_COUNT > 0) draw();

  window.addEventListener('resize', () => {
    resize();
    initNodes();
  });

  canvas.parentElement?.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    MOUSE.x = e.clientX - rect.left;
    MOUSE.y = e.clientY - rect.top;
    MOUSE.active = true;
  });

  canvas.parentElement?.addEventListener('mouseleave', () => {
    MOUSE.active = false;
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(animationId);
    } else if (!prefersReduced && NODE_COUNT > 0) {
      draw();
    }
  });
})();