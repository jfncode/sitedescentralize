# Hero 3D + Scroll Reveal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar cena 3D de rede de nós (Three.js, lazy) atrás do hero do descentralize.com.br e scroll reveal nas seções, sem impactar SEO/AdSense/Core Web Vitals.

**Architecture:** Site estático sem build. Um módulo ES novo (`assets/hero3d.js`) contém toda a lógica 3D e importa Three.js de CDN dinamicamente, só quando ocioso + hero visível. Scroll reveal é CSS + IntersectionObserver inline no `index.html`. Fallback: gradiente CSS; qualquer falha degrada silenciosamente.

**Tech Stack:** HTML/CSS/JS vanilla, Three.js `0.165.0` via jsdelivr (versão pinada), IntersectionObserver.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-15-hero3d-futurista-design.md`
- Não tocar em scripts de AdSense/consent/GA4 nem em `build_pages.py` / `update_index.py`.
- Three.js **somente** via `import()` dinâmico após `requestIdleCallback` (fallback `setTimeout` 1500ms) **e** hero visível.
- `prefers-reduced-motion: reduce` → nem 3D nem reveal.
- Sem WebGL ou CDN fora do ar → `catch` silencioso, gradiente permanece.
- `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`; mobile (<768px) usa 60 nós, desktop 120.
- Cor de destaque: `#ff9900` (var(--accent) do site).
- Push para produção só com aprovação explícita do Jefferson.

---

### Task 1: Módulo `assets/hero3d.js` (cena Three.js completa)

**Files:**
- Create: `assets/hero3d.js`

**Interfaces:**
- Consumes: elemento `<canvas id="hero3d">` dentro de `<section class="hero">` (criado na Task 2).
- Produces: script auto-executável; nenhuma API exportada. Task 2 só precisa referenciar `<script type="module" src="/assets/hero3d.js">`.

- [ ] **Step 1: Criar o arquivo com o módulo completo**

```js
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
```

- [ ] **Step 2: Verificar sintaxe do módulo**

Run: `node --check assets/hero3d.js`
Expected: sem saída (exit 0). (`node --check` valida sintaxe; APIs de browser não são executadas.)

- [ ] **Step 3: Commit**

```bash
git add assets/hero3d.js
git commit -m "feat(hero): modulo Three.js da rede de nos 3D (lazy, com fallbacks)"
```

---

### Task 2: Wiring do hero no `index.html` (canvas + CSS + script)

**Files:**
- Modify: `index.html:298-304` (CSS `.hero`), `index.html:958` (antes de `</style>`), `index.html:996-1004` (markup do hero), `index.html:4394` (antes de `</body>`)

**Interfaces:**
- Consumes: nada de tasks anteriores (o script da Task 1 só ativa se o canvas existir).
- Produces: `<canvas id="hero3d">` como primeiro filho de `section.hero`; conteúdo do hero acima do canvas via z-index.

- [ ] **Step 1: Adicionar gradiente e overflow ao CSS `.hero` existente**

No bloco `.hero` (linha ~298), acrescentar `overflow: hidden` e o gradiente (fallback permanente):

```css
.hero {
    padding: 60px 24px 40px;
    text-align: center;
    max-width: 1100px;
    margin: 0 auto;
    position: relative;
    overflow: hidden;
    background: radial-gradient(ellipse 80% 60% at 50% 20%, rgba(255,153,0,0.07), transparent 70%);
}
```

- [ ] **Step 2: Adicionar CSS do canvas antes de `</style>` (linha ~958)**

```css
/* hero 3D — canvas atrás do conteúdo */
#hero3d {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
}
.hero > :not(#hero3d) { position: relative; z-index: 1; }
```

- [ ] **Step 3: Inserir o canvas como primeiro filho do hero (linha ~996)**

```html
<section class="hero" id="home">
<canvas id="hero3d" aria-hidden="true"></canvas>
<div class="hero-tag">// SAIA DA MATRIX</div>
```

- [ ] **Step 4: Referenciar o módulo antes de `</body>` (linha ~4394)**

```html
<script type="module" src="/assets/hero3d.js"></script>
```

- [ ] **Step 5: Smoke test no navegador**

Run: `python -m http.server 8000` (na raiz do repo) e abrir `http://localhost:8000`.
Expected: hero com rede de nós laranja girando atrás do texto; console sem erros; aba Network mostra `three.module.js` baixando **depois** do load.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(hero): canvas 3D + gradiente fallback + z-index do conteudo"
```

---

### Task 3: Scroll reveal (CSS + IntersectionObserver)

**Files:**
- Modify: `index.html:~958` (antes de `</style>`), `index.html:~4394` (antes de `</body>`, junto ao script da Task 2)

**Interfaces:**
- Consumes: classes já existentes no HTML: `.section-head`, `.post-card`, `.tool-card`, `.widget` (as classes `.reveal`/`.reveal-in` são adicionadas via JS — HTML não é editado card a card).
- Produces: nada consumido por outras tasks.

- [ ] **Step 1: Adicionar CSS do reveal antes de `</style>`**

```css
/* scroll reveal — só com motion permitido */
@media (prefers-reduced-motion: no-preference) {
    .reveal {
        opacity: 0;
        transform: translateY(14px);
        transition: opacity 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                    transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }
    .reveal-in { opacity: 1; transform: none; }
}
```

- [ ] **Step 2: Adicionar o observer antes de `</body>`**

```html
<script>
(function () {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (!('IntersectionObserver' in window)) return;
    var els = document.querySelectorAll('.section-head, .post-card, .tool-card, .widget');
    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
            if (e.isIntersecting) { e.target.classList.add('reveal-in'); io.unobserve(e.target); }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { el.classList.add('reveal'); io.observe(el); });
})();
</script>
```

- [ ] **Step 3: Testar no navegador**

Run: recarregar `http://localhost:8000` e rolar a página inteira.
Expected: seções/cards surgem com fade+slide uma única vez; nada fica invisível ao final da rolagem (inclusive cards filtrados por categoria); console limpo.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(ui): scroll reveal com IntersectionObserver (respeita reduced-motion)"
```

---

### Task 4: Verificação final (visual, fallbacks, Lighthouse)

**Files:**
- Nenhum arquivo novo; correções pontuais se a verificação falhar.

**Interfaces:**
- Consumes: site completo das Tasks 1–3 rodando em `http://localhost:8000`.
- Produces: evidência de verificação (screenshots + scores) relatada ao Jefferson.

- [ ] **Step 1: Verificação visual desktop e mobile (Chrome/extensão)**

Abrir `http://localhost:8000` no Chrome: screenshot do hero desktop; redimensionar para ~390px de largura e capturar de novo.
Expected: 3D fluido no desktop; no mobile a cena aparece com menos nós e sem jank ao rolar.

- [ ] **Step 2: Testar fallback reduced-motion**

No DevTools → Rendering → "Emulate CSS media feature prefers-reduced-motion: reduce" e recarregar.
Expected: sem canvas animado (gradiente estático), conteúdo todo visível sem animações.

- [ ] **Step 3: Conferir consoles e rede**

Expected: zero erros no console; `three.module.js` (~170KB) só aparece na aba Network após o load; scripts de AdSense/GA4/consent inalterados e carregando como antes.

- [ ] **Step 4: Lighthouse (mobile)**

Run: `npx lighthouse http://localhost:8000 --quiet --chrome-flags="--headless" --only-categories=performance,seo --output=json --output-path=./lighthouse-after.json` e ler `categories.performance.score` / `categories.seo.score`.
Expected: Performance ≥ 0.90 e SEO igual ao valor anterior à mudança. (`lighthouse-after.json` é temporário — não commitar.)

- [ ] **Step 5: Relatar resultado e aguardar aprovação para push**

Mostrar ao Jefferson screenshots + scores. **Não fazer `git push` sem ok explícito** (site em produção).
