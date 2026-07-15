# Design: Hero 3D + polimento futurista — descentralize.com.br

**Data:** 2026-07-15
**Status:** Aprovado por Jefferson

## Objetivo

Adicionar uma cena 3D interativa (rede de nós estilo blockchain) ao hero do `index.html` e scroll reveal nas seções, mantendo intactos SEO, AdSense/consent (LGPD) e Core Web Vitals.

## Escopo

**Dentro:** hero 3D com Three.js lazy-load; scroll reveal em títulos de seção, cards de artigos e painéis da home.
**Fora:** redesign das páginas internas (`sobre`, `contato`, artigos), tilt 3D em cards, glassmorphism, efeitos de texto. Nenhuma mudança em `build_pages.py` / `update_index.py`.

## Arquitetura

Site permanece estático, sem etapa de build nova. Duas adições:

1. **`assets/hero3d.js`** — módulo ES independente com toda a cena Three.js. Three.js importado de CDN (jsdelivr, versão pinada) via `import()` dinâmico dentro do módulo.
2. **Inline no `index.html`** — `<canvas id="hero3d">` no hero, ~20 linhas de CSS (posicionamento do canvas, gradiente de fallback, classes de reveal) e ~15 linhas de JS (IntersectionObserver do scroll reveal + gatilho de carregamento do hero3d).

## Hero 3D — comportamento

- Canvas absoluto atrás do conteúdo do hero (`z-index` abaixo do texto, `pointer-events: none`). Sob ele, gradiente CSS escuro que também é o fallback.
- Cena: ~120 nós (pontos com glow laranja `#ff9900`, blending aditivo) em nuvem esférica; linhas finas ligando nós a menos de um raio-limite (a "rede descentralizada").
- Animação: rotação lenta contínua + parallax sutil (~0.05 rad) seguindo o mouse com suavização.
- Carregamento: `requestIdleCallback` (fallback `setTimeout` 1500 ms) **e** hero visível via IntersectionObserver — só então o `import()` do Three.js dispara.
- Economia: `renderer.setPixelRatio(min(devicePixelRatio, 2))`; loop pausa com `document.hidden` ou hero fora da viewport; em telas < 768 px usa ~60 nós.

## Scroll reveal

- Elementos-alvo recebem classe `.reveal` (títulos `.section-title`, cards de artigo, painéis).
- IntersectionObserver adiciona `.reveal-in` na primeira entrada (threshold ~0.15) e faz `unobserve` — anima uma única vez.
- CSS: `opacity 0→1` + `translateY(14px)→0`, `~500ms`, easing ease-out (princípios da skill web-animation-design: rápido no fim, sem bounce, sem repetição).

## Fallbacks e acessibilidade

- `prefers-reduced-motion: reduce` → não inicializa Three.js nem reveal; conteúdo estático com gradiente.
- Sem WebGL (`canvas.getContext('webgl')` nulo) ou falha no `import()` do CDN → `catch` silencioso, gradiente permanece, site 100% funcional.
- Conteúdo do hero (h1, tagline, CTAs) permanece HTML puro no DOM — zero impacto em SEO/leitores de tela.

## Riscos

- **CDN de terceiro (jsdelivr):** indisponibilidade só afeta o efeito visual (fallback cobre). Versão pinada evita quebra por update.
- **CLS:** canvas é `position: absolute` dentro do hero já dimensionado — não desloca layout.
- **AdSense:** nenhum script de consentimento/ads é tocado.

## Verificação

1. Servidor local (`python -m http.server`) + Chrome (extensão): conferir hero 3D desktop, mobile (viewport estreito), aba `prefers-reduced-motion`.
2. Console sem erros; rede: Three.js só baixa após load e com hero visível.
3. Lighthouse antes/depois: Performance e SEO não podem cair (meta ≥ 90 em Performance mobile).
4. Commit local; push para produção **somente com aprovação explícita** do Jefferson.
