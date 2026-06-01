# CLAUDE.md — LabHero: Guía completa para Claude Code

Este archivo documenta toda la arquitectura, convenciones y decisiones de diseño
del proyecto **LabHero**, para uso de Claude Code en sesiones futuras.

---

## Descripción general

**LabHero** es un laboratorio visual interactivo para diseñar y previsualizar
hero-sections web (fondos animados, efectos, carrusel de imágenes, header corporativo,
sistema de diseño). Está pensado para el proyecto *El Malecón de la Salsa* (escuela de
baile en Castelldefels, España), pero es genérico.

El resultado es un único `index.html` autocontenido con ~3.250 líneas que, servido por
Nginx + Docker, expone un entorno profesional de diseño visual con:
- 7 efectos de fondo animados (canvas, SVG, vídeo)
- Filtros ópticos sobre imágenes con carrusel y 10 transiciones 2D (incluyendo difusión canvas)
- Header totalmente editable (logo, menú, efectos)
- Sistema de temas CSS intercambiables (10 ficheros de paleta blanco/verde/negro)
- Exportación/importación CSS+JSON unificada que persiste en el servidor

---

## Arquitectura Docker

```
docker-compose.yml
├── labhero-web          (nginx:1.27-alpine)  → puerto LABHERO_HTTP_PORT (def. 8081)
├── labhero-uploader     (Python Flask)        → puerto interno 5000
└── labhero-video-optimizer (Python FastAPI)   → puerto interno 8000
```

### Volúmenes críticos

| Servicio | Host | Contenedor | Modo |
|----------|------|------------|------|
| nginx | `./html` | `/usr/share/nginx/html` | `:ro` |
| uploader | `./html/media` | `/app/media` | `:rw` |
| uploader | `./html` | `/app/html` | `:ro` |
| uploader | `./html/assets/css` | `/app/html/assets/css` | `:rw` ← permite guardar unified |

El mount específico `:rw` de `assets/css` sobreescribe el `:ro` del mount padre de `/html`.

### Variables de entorno (`.env`)

```env
COMPOSE_PROJECT_NAME=labhero
LABHERO_HTTP_PORT=8081
NGINX_CONTAINER_NAME=labhero-web
UPLOADER_CONTAINER_NAME=labhero-uploader
VIDEO_OPTIMIZER_CONTAINER_NAME=labhero-video-optimizer
TZ=Europe/Madrid
MAX_UPLOAD_MB=10
```

---

## Backend: Uploader (`uploader/app.py`)

Flask con Gunicorn. Variables de entorno: `MEDIA_DIR` (`/app/media`), `HTML_DIR` (`/app/html`).

### Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/health` | Health check |
| `POST` | `/api/upload-logo` | Sube logo corporativo → `media/logo-current.{ext}` + `logo.json` |
| `POST` | `/api/upload-image-logo` | Logo de la sección imágenes → `image-logo-current.{ext}` + `image-logo.json` |
| `GET`  | `/api/list-media` | Lista vídeos, imágenes y CSS disponibles |
| `GET`  | `/api/list-css` | Alias de list-media para CSS |
| `POST` | `/api/save-asset` | Guarda `labHero_unified.css` o `labHero_unified.json` en `/assets/css/` |

`/api/save-asset` solo acepta los nombres `labHero_unified.css` y `labHero_unified.json` (allowlist estricta).

## Backend: Video Optimizer (`video-optimizer-backend/main.py`)

FastAPI con Uvicorn + FFmpeg. Un único endpoint:

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/optimize` | Recibe `file` (MP4), devuelve MP4 optimizado (H.264, max 1080p, 30fps, sin audio) |

---

## Nginx (`nginx/default.conf`)

- `/` → sirve `index.html` (sin caché)
- `/media/` → autoindex ON (permite que el JS detecte vídeos e imágenes)
- `/7media/` → alias de `/media/` (compatibilidad)
- `/assets/` → CSS con caché 1h
- `/api/` → proxy a uploader:5000
- `/api/optimize` → proxy dedicado a video-optimizer:8000 (timeout 900s)

**Importante:** el `autoindex on` en `/media/` es requerido por `scanServerMediaFolder()` en el JS para descubrir ficheros.

---

## Frontend: `html/index.html` (~3.250 líneas)

El fichero está organizado en bloques `<script>` acumulativos que se **parchean**
unos sobre otros usando el patrón *function override*:

```
<head>
  └─ <style id="custom-brand-variables">   ← CSS vars iniciales en :root
  └─ <style>                               ← Estilos base del laboratorio
  └─ <link id="labhero-default-unified">   ← labHero_unified.css (único CSS externo)

<body>
  └─ .topbar (header) + .lab (grid hero + panel lateral)

<script>  ← Script principal (líneas 392–1406)
  state, renderControls, applyVisuals, applyDesignTokens,
  motores canvas (particles, waves, magneticMouse, fireworks),
  magneticClickRepulse (repulsión por click en efecto 5)

<script id="labhero-v5-functional-patch">  ← (líneas 1409–2430)
  Carrusel, diffusion transition, video scan, logo upload,
  exportUnifiedCSS/JSON (versión base, sobrescrita por V8)

<script>  ← V6 VideoOptimization  (líneas 2433–2570)

<script>  ← V8 Header  (líneas 2573–3140)
  setupAppHeaderV8, renderHeaderControlsV8,
  exportUnifiedCSSV8, exportUnifiedJSONV8,
  saveAssetToServer → POST /api/save-asset

<script id="labhero-default-css-v9">  ← (líneas 3142–3162)
  Carga labHero_unified.css; fallback a los 4 ficheros individuales

<script id="labhero-magnifier-v9">  ← (líneas 3164–3210)
  Canvas animado para el efecto 7 (magnifier glass)
```

### Patrón de override de funciones

Cada versión guarda la función anterior y la extiende:
```js
const previousFn = window.switchControlPane || switchControlPane;
window.switchControlPane = switchControlPane = function(pane) {
  // nueva lógica
  previousFn(pane);
};
```

---

## Sistema CSS

### Ficheros de carga

Al arrancar, el frontend intenta en este orden:

1. `<link href="/assets/css/labHero_unified.css">` (en `<head>`)
2. JS V9 verifica con `HEAD` si existe; si no, inyecta los 4 individuales
3. `DOMContentLoaded`: fetch `/assets/css/labHero_unified.json` → fallback a `labHero_efects.json`
4. `DOMContentLoaded`: fetch CSS `/assets/css/labHero_unified.css` → fallback a `labHero_styles.css`

### Ficheros CSS en `/assets/css/`

| Fichero | Propósito |
|---------|-----------|
| `labHero_unified.css` | **Fichero maestro** — generado por ⬇ CSS, cargado al arranque |
| `labHero_unified.json` | **State maestro** — generado por ⬇ JSON, cargado al arranque |
| `labHero_styles.css` | Fallback: tokens de estilo (tipografía, colores, radios) |
| `labHero_efects.css` | Fallback: parámetros de efectos de fondo |
| `labHero_images.css` | Fallback: parámetros del carrusel de imágenes |
| `labHero_header.css` | Fallback: variables del header principal |
| `malecon_blanc.css` | Tema: Blanco puro + Esmeralda |
| `malecon_jade.css` | Tema: Blanco hueso + Verde jade editorial |
| `malecon_botanical.css` | Tema: Crema + Verde botánico |
| `malecon_sage.css` | Tema: Blanco nórdico + Sage suave |
| `malecon_obsidian.css` | Tema: Blanco glacial + Verde neón máximo contraste |
| `malecon_ivory.css` | Tema: Marfil + Verde oliva dorado |
| `malecon_cleanGlass.css` | Tema: Blanco glass + Verde cristal translúcido |
| `malecon_greenGlass.css` | Sistema de diseño completo con utilidades CSS |
| `malecon_greenWhite.css` | Sistema de diseño CSS3 con componentes web |
| `malecon_greenblack.css` | Tema: Blanco glacial + Verde neón puro |

### Variables CSS clave

```css
/* Obligatorias para que labHero funcione */
--font-h1, --font-body
--color-brand-primary, --color-brand-secondary
--color-bg-viewport, --color-bg-card
--color-text-main, --color-text-muted, --color-border
--card-radius, --card-bg-opacity
--brand-glow-effect, --card-shadow
--hero-text-shadow-strength, --hero-text-stroke-width
--hero-text-bg-opacity, --hero-text-align

/* Header */
--app-header-height, --app-header-logo-size, --app-header-logo-zoom
--app-header-bg-opacity, --app-header-blur, --app-header-border-opacity
--app-header-menu-gap, --app-header-menu-radius
--app-header-bg-rgba  (calculado dinámicamente en JS)

/* Efectos de fondo */
--blur, --waveWidth, --mask-opacity
--vid-blur, --vid-warmth, --vid-brightness, --vid-saturate, --vid-contrast
--speed2a, --speed2b, --speed2c
--c-blob1, --c-blob2, --c-blob3
--lupa-size, --lupa-zoom
```

---

## Efectos de fondo (panel "Efectos Fondo")

| # | Nombre | Tipo | Notas |
|---|--------|------|-------|
| 1 | Partículas | Canvas | Nodos + líneas, atracción al ratón |
| 2 | Gradientes líquidos | CSS (blobs) | Colores configurables: fusion/salsa/bachata |
| 3 | Vídeo Manual | `<video>` / YouTube | Scan automático de `/media/` via autoindex |
| 4 | Ondas cinemáticas | SVG | Animación requestAnimationFrame |
| 5 | Imanes Mouse | Canvas | Atracción al mover + **repulsión explosiva al hacer click** |
| 6 | Fuegos Artificiales | Canvas | Rockets + partículas |
| 7 | Lupa de Textos | Canvas dual | Canvas fondo + canvas lente con zoom real del contenido |

**Bug conocido resuelto:** Los canvas de efectos 5 y 6 se inicializan con tamaño 0×0 cuando
el div tiene `display:none`. Fix: `showEffect()` despacha `window.dispatchEvent(new Event('resize'))` al mostrar.

---

## Carrusel de imágenes

- **Fuente:** imágenes en `/media/` detectadas via `scanMediaInventory()` → `/api/list-media`
- **Transiciones:** 10 efectos 2D + 1 canvas (sin efectos 3D intencionalmente)
  - CSS: fade, slideLeft, slideRight, slideUp, zoomFade, blurFade, rotateFade, wipe, kenBurns
  - Canvas: **diffusion** — los píxeles de una imagen se dispersan y convergen en la siguiente
- **Bounds:** las transiciones no salen del área del `<img>` actual (posicionamiento via `getBoundingClientRect()`)
- **Difusión canvas:** samplea colores reales de ambas imágenes via `getImageData()`. Fallback verde de marca si hay restricciones CORS.

---

## Header principal

Construido dinámicamente por `setupAppHeaderV8()`. Estructura:
```
.topbar.app-header-v8
  └─ .app-header-inner-v8  (grid: logo | nav | export-zone)
       ├─ .app-header-logo-slot-v8  (overflow:hidden, altura fija)
       │    └─ .brand-logo-container  (transform:scale para zoom, sin padding/border)
       ├─ .main-web-menu-v8  (botones de panel)
       └─ .app-header-export-zone-v8  (📂 Importar | ⬇ CSS | ⬇ JSON)
  └─ .app-header-effect-row-v8  (barra de efectos, oculta en otros paneles)
```

**Logo:** sin decoración visual por defecto (`logoShape: 'none'`). El zoom usa
`transform: scale(--app-header-logo-zoom)` + `overflow:hidden` en el slot para que
NUNCA afecte la altura del header (controlada exclusivamente por `--app-header-height`).

---

## Exportación e importación unificada

### Export (botones ⬇ CSS y ⬇ JSON en el header)
1. Genera el contenido en memoria
2. Descarga al navegador (`triggerDownload`)
3. `saveAssetToServer(filename, content)` → `POST /api/save-asset` → sobreescribe en `/assets/css/`
4. El `<link id="labhero-default-unified">` se recarga con `?v=timestamp`

### Import (botón 📂 Importar en el header)
- Acepta `.json` y `.css`
- JSON: aplica `state.effects` + `state.designSystem`, re-renderiza todo
- CSS: `parseAndApplyCSSText()`, aplica variables a `:root`, actualiza header

---

## Logo del proyecto

**El Malecón de la Salsa** — escuela de baile en Castelldefels, España.
- Logo original: `html/media/logo_elmalecondelasalsa.png`
- Logo activo (servido en producción): `html/media/logo-current.png` (sobrescrito por el uploader)
- Paleta de marca: verde esmeralda (#1A7A42 por defecto), blanco, negro
- Tipografías: Space Grotesk (títulos), Inter (cuerpo)

---

## Scripts de servicio

```bash
./scripts/start.sh    # docker compose up -d
./scripts/stop.sh     # docker compose down
./scripts/logs.sh     # docker compose logs -f
./scripts/validate.sh # health checks
```

---

## Convenciones importantes

- **No crear CSS que sobrescriba estilos del `<style>` inline** del head — tienen precedencia intencionada.
- **`overflow:hidden` en `.app-header-logo-slot-v8`** es deliberado para recortar zoom del logo.
- **El autoindex de Nginx en `/media/`** es requerido; no desactivar.
- **Los efectos canvas** deben manejar el caso `clientWidth=0` (elemento oculto al init).
- **`labHero_unified.css` y `labHero_unified.json`** son los únicos ficheros de carga en producción. Los 4 `labHero_*.css` individuales son solo fallback de desarrollo.
- **`docker.compose.yml`** (con punto) es un backup antiguo — usar solo `docker-compose.yml`.
- El uploader usa `secure_filename()` de Werkzeug para logos y allowlist para unified.
- Todos los temas CSS deben definir las variables de la sección "Variables CSS clave" para ser compatibles con labHero.

---

## Paleta de colores del proyecto

| Rol | Color | Hex |
|-----|-------|-----|
| Verde esmeralda (primary) | ![](https://placehold.co/12x12/1A7A42/1A7A42) | `#1A7A42` |
| Blanco viewport | ![](https://placehold.co/12x12/F5FAF7/F5FAF7) | `#F5FAF7` |
| Negro tipográfico | ![](https://placehold.co/12x12/0C1F14/0C1F14) | `#0C1F14` |
| Verde claro (partículas) | ![](https://placehold.co/12x12/2FE56B/2FE56B) | `#2FE56B` |
| Borde suave | | `#C0D8CA` |

---

## GitHub

- **Repositorio:** `https://github.com/automatecodes/labHero`
- **Usuario Git:** `automatecodes`
- **Email:** configurado en `~/.gitconfig`
