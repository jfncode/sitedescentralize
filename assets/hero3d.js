// hero3d.js — rede de nós 3D do hero (descentralize.com.br)
// Carrega Three.js de CDN só quando o navegador está ocioso E o hero visível.
// Qualquer falha degrada em silêncio para o gradiente CSS.

const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js';

const canvas = document.getElementById('hero3d');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

if (canvas && !reduced && supportsWebGL()) {
  whenIdle(() => whenVisible(canvas.parentElement, start));
}

function supportsWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch { return false; }
}

function whenIdle(cb) {
  if ('requestIdleCallback' in window) requestIdleCallback(cb, { timeout: 2000 });
  else setTimeout(cb, 1500);
}

function whenVisible(el, cb) {
  const io = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) { io.disconnect(); cb(); }
  });
  io.observe(el);
}

async function start() {
  let THREE;
  try { THREE = await import(THREE_URL); }
  catch { return; } // CDN falhou: fica o gradiente

  try {
    const hero = canvas.parentElement;
    const isMobile = innerWidth < 768;
    const NODE_COUNT = isMobile ? 60 : 120;
    const RADIUS = 4;
    const LINK_DIST = 1.6;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 100);
    camera.position.z = 7;

    // nós distribuídos numa nuvem esférica
    const positions = new Float32Array(NODE_COUNT * 3);
    for (let i = 0; i < NODE_COUNT; i++) {
      const r = RADIUS * Math.cbrt(Math.random());
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }

    const group = new THREE.Group();
    scene.add(group);

    const nodeGeo = new THREE.BufferGeometry();
    nodeGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const nodeMat = new THREE.PointsMaterial({
      size: 0.14,
      map: makeGlowTexture(THREE),
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      color: 0xff9900,
    });
    group.add(new THREE.Points(nodeGeo, nodeMat));

    // linhas entre nós próximos (a "rede")
    const linePos = [];
    for (let i = 0; i < NODE_COUNT; i++) {
      for (let j = i + 1; j < NODE_COUNT; j++) {
        const dx = positions[i*3] - positions[j*3];
        const dy = positions[i*3+1] - positions[j*3+1];
        const dz = positions[i*3+2] - positions[j*3+2];
        if (dx*dx + dy*dy + dz*dz < LINK_DIST * LINK_DIST) {
          linePos.push(positions[i*3], positions[i*3+1], positions[i*3+2],
                       positions[j*3], positions[j*3+1], positions[j*3+2]);
        }
      }
    }
    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(linePos), 3));
    const lineMat = new THREE.LineBasicMaterial({
      color: 0xff9900,
      transparent: true,
      opacity: 0.14,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    group.add(new THREE.LineSegments(lineGeo, lineMat));

    // parallax suave com o mouse
    let targetX = 0, targetY = 0;
    addEventListener('pointermove', (e) => {
      targetX = (e.clientX / innerWidth - 0.5) * 0.3;
      targetY = (e.clientY / innerHeight - 0.5) * 0.2;
    }, { passive: true });

    // pausa quando aba oculta ou hero fora da tela
    let running = true, rafId = 0;
    const setRunning = (on) => {
      if (on && !running) { running = true; rafId = requestAnimationFrame(tick); }
      else if (!on && running) { running = false; cancelAnimationFrame(rafId); }
    };
    document.addEventListener('visibilitychange', () => setRunning(!document.hidden));
    new IntersectionObserver((entries) =>
      setRunning(entries[0].isIntersecting && !document.hidden)
    ).observe(hero);

    function resize() {
      const w = hero.clientWidth, h = hero.clientHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    addEventListener('resize', resize, { passive: true });
    resize();

    function tick() {
      if (!running) return;
      group.rotation.y += 0.0009;
      group.rotation.x += (targetY - group.rotation.x) * 0.05;
      group.rotation.z += (targetX - group.rotation.z) * 0.05;
      renderer.render(scene, camera);
      rafId = requestAnimationFrame(tick);
    }
    rafId = requestAnimationFrame(tick);
  } catch { return; } // WebGL falhou (renderer, contexto, driver): fica o gradiente
}

// sprite circular com glow (evita os quadrados do PointsMaterial padrão)
function makeGlowTexture(THREE) {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(255,210,130,1)');
  grad.addColorStop(0.35, 'rgba(255,153,0,0.85)');
  grad.addColorStop(1, 'rgba(255,153,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}
