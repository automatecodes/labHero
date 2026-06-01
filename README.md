# LabHero Docker Complete v5

## Prompt de trabajo

El usuario solicita corregir el laboratorio visual para que:

- El logo corporativo se actualice inmediatamente al seleccionar un fichero.
- El logo se guarde físicamente en `/media` y se recupere en el próximo acceso.
- El logo de **Efectos Imagen** también se actualice en pantalla, se guarde en `/media` y se recupere al recargar.
- El control de vídeo deje de ser botón “Siguiente” y pase a ser un selector desplegable con los nombres reales de los vídeos disponibles.
- Al seleccionar un vídeo local, el `<video>` se recargue con el fichero correspondiente.
- El efecto imán vuelva a movimiento browniano al hacer click, hasta que haya un nuevo movimiento de mouse.
- La lupa no tenga borde.
- En **Efectos Imagen** se pueda activar un carrusel desde `/media`, con intervalo configurable, controles anterior/siguiente superpuestos y nombre del fichero en la parte inferior central.
- El export CSS incluya los parámetros nuevos.

## Estructura

```text
labhero_docker_complete/
├── .env
├── docker-compose.yml
├── docker.compose.yml
├── README.md
├── html/
│   ├── index.html
│   ├── labHero_efects.json
│   ├── labHero_styles.css
│   ├── assets/
│   └── media/
├── nginx/
│   └── default.conf
├── scripts/
│   ├── start.sh
│   ├── stop.sh
│   ├── logs.sh
│   └── validate.sh
└── uploader/
    ├── Dockerfile
    ├── app.py
    └── requirements.txt
```

## Arranque

```bash
cd labhero_docker_complete
docker compose --env-file .env up -d --build
```

Abrir:

```text
http://localhost:8081
```

Parar:

```bash
docker compose --env-file .env down
```

## Servicios Docker

### `labhero-web`

Servidor Nginx estático. Sirve:

- `/index.html`
- `/media/`
- `/7media/` como alias compatible de `/media/`
- `/labHero_efects.json`
- `/labHero_styles.css`

### `labhero-uploader`

Servicio Flask interno usado por el navegador para persistir archivos en `/media`.

Endpoints:

```text
GET  /api/list-media
GET  /api/list-css
POST /api/upload-logo
POST /api/upload-image-logo
```

## Uso de vídeos locales

Copia vídeos en:

```text
html/media/
```

Formatos aceptados:

```text
.mp4, .webm, .mov, .m4v, .ogv
```

En la interfaz:

1. Abre **3. Vídeo Manual**.
2. Pulsa **Re-escanear /media** si acabas de copiar ficheros.
3. Usa el desplegable **Vídeo local disponible en /media**.
4. Al seleccionar un nombre, el vídeo se recarga inmediatamente.

## Logos persistentes

### Logo de marca

Ruta en UI:

```text
Estilos Marca > Subir Logo de Fondo
```

Al seleccionar un fichero:

- Se muestra una previsualización inmediata.
- Se envía a `/api/upload-logo`.
- Se guarda en:

```text
html/media/logo-current.<ext>
html/media/logo.json
```

Al recargar la web, se lee `/media/logo.json` y se restaura el logo.

### Logo de Efectos Imagen

Ruta en UI:

```text
Efectos Imagen > Subir Logo de Medios Imagen
```

Al seleccionar un fichero:

- Se muestra superpuesto sobre la imagen.
- Se envía a `/api/upload-image-logo`.
- Se guarda en:

```text
html/media/image-logo-current.<ext>
html/media/image-logo.json
```

Al recargar la web, se lee `/media/image-logo.json`.

## Carrusel de imágenes desde `/media`

Copia imágenes en:

```text
html/media/
```

Formatos aceptados:

```text
.png, .jpg, .jpeg, .webp, .gif, .svg
```

En la interfaz:

1. Abre **Efectos Imagen**.
2. Marca **Convertir imagen en carrusel desde /media**.
3. Ajusta **Tiempo visible por imagen**. Valor por defecto: `5s`.
4. Usa los controles superpuestos izquierda/derecha para pasar manualmente.
5. El nombre del fichero aparece abajo, sin extensión.

## CSS existentes

Copia CSS en cualquiera de estas rutas:

```text
html/media/
html/
html/assets/css/
```

En la interfaz:

```text
Estilos Marca > Aplicar CSS existente desde /media
```

Usa **Re-escanear CSS** si acabas de copiar nuevos ficheros.

## Exportación

### Export de Efectos Imagen

Incluye ahora:

```css
--labhero-image-logo-url
--labhero-carousel-enabled
--labhero-carousel-delay
--labhero-carousel-folder
--labhero-carousel-selected-image
```

### Export de Estilos Marca

Incluye ahora:

```css
--brand-logo-url
```

## Validación

Validaciones realizadas en el paquete generado:

```text
JavaScript embebido: OK
YAML docker-compose.yml: OK
Python uploader/app.py: OK
ZIP generado correctamente
```

## Nota técnica importante

Un navegador no puede escribir directamente en `/media` cuando la web se sirve como HTML estático. Por eso se incluye el servicio `labhero-uploader`. Si se elimina ese servicio, los logos podrán verse como previsualización temporal con `blob:` o `base64`, pero no quedarán persistidos en disco.

---

## VideoOtimization integrado en LabHero

Se ha incorporado la aplicación `video-optimizer` como un panel adicional al mismo nivel que:

- Efectos Fondo
- Efectos Imagen
- Estilos Marca
- VideoOtimization

### Backend añadido

El paquete incluye un nuevo servicio Docker:

```yaml
labhero-video-optimizer:
  build:
    context: ./video-optimizer-backend
```

Este servicio usa FastAPI + FFmpeg para procesar vídeos MP4.

### Endpoint publicado por Nginx

```text
POST /api/optimize
```

El endpoint espera un formulario `multipart/form-data` con el campo:

```text
file
```

### Perfil técnico de salida

El vídeo optimizado se devuelve al navegador para descarga con este perfil:

- Formato: MP4
- Códec: H.264 / libx264
- Resolución máxima: 1920 px de ancho, conservando proporción
- FPS: 30
- Bitrate objetivo: 3 Mbps
- Maxrate: 4 Mbps
- Audio: eliminado

Este perfil está pensado para vídeos de fondo web, reduciendo peso, evitando problemas de autoplay con audio y descargando carga del navegador.

### Uso desde la interfaz

1. Arranca el stack:

```bash
docker compose --env-file .env up -d --build
```

2. Abre:

```text
http://localhost:8081
```

3. Pulsa la pestaña:

```text
VideoOtimization
```

4. Selecciona un fichero `.mp4`.
5. Pulsa **Optimizar vídeo**.
6. El navegador descargará automáticamente el resultado como:

```text
nombre-original.optimized.mp4
```

### Código fuente original incluido

El ZIP conserva la app subida originalmente en:

```text
source_uploaded/video-optimizer/
```

La integración operativa usada por LabHero está en:

```text
video-optimizer-backend/
```

## Cambios v7 - Hero sin recuadro y textos legibles

Se elimina el recuadro visual que envolvía los textos del hero. El bloque central queda sobre fondo transparente, sin borde y sin sombra de tarjeta.

Para mantener legibilidad sobre vídeos, partículas o imágenes, se usa el patrón más habitual en landings con fondos visuales: texto grande con `text-shadow`, un contorno fino mediante `-webkit-text-stroke` y, opcionalmente, un velo radial oscuro muy suave detrás del texto.

En **Estilos Marca** se añade la sección **Textos Hero sin Recuadro**, con estos controles:

- **Estilo visual de texto**: Cinemático con glow, contraste limpio, contorno fuerte o velo suave.
- **Intensidad de sombra / glow del texto**.
- **Grosor de contorno del título**.
- **Velo oscuro detrás del texto**.
- **Alineación del bloque de texto**.

La exportación CSS de **Estilos Marca** incluye ahora:

```css
--hero-text-style-preset
--hero-text-shadow-strength
--hero-text-stroke-width
--hero-text-bg-opacity
--hero-text-align
```

Recomendación práctica: para fondos con vídeo o mucha variación de color, usar **Cinemático con sombra y glow** o **Contorno fuerte para vídeo**. Para fondos oscuros y limpios, usar **Contraste limpio sin halo**.

---

# Actualización v8: Header editable y CSS en assets

## Header principal

Se ha añadido una nueva sección principal llamada **Header**. El logo se ha movido al borde izquierdo del header y el menú principal de la web se ha migrado al propio header.

El menú principal controla ahora estas áreas:

- Efectos Fondo
- Efectos Imagen
- Estilos Marca
- Header
- VideoOtimization

La navegación de efectos concretos —Partículas, Aurora, Vídeo, Ondas, Imanes, Fuegos Artificiales y Lupa— queda como submenú visible únicamente cuando se está en **Efectos Fondo**.

## Controles disponibles en Header

Desde la sección **Header** puedes modificar:

- Imagen del logo persistida en `/media/logo-current.*`.
- Altura del header.
- Tamaño del logo.
- Opacidad del fondo.
- Blur del fondo.
- Opacidad de la línea inferior.
- Activación/desactivación de comportamiento sticky.
- Texto de cada opción del menú.
- Estilo visual del menú.
- Efecto hover del menú.
- Alineación del menú.
- Separación entre opciones.
- Radio de botones.
- Animación del logo.
- Forma del contenedor del logo.

## CSS existentes de marca

El selector de CSS existentes busca ahora en estas rutas:

```text
html/*.css
html/assets/*.css
html/assets/css/*.css
html/media/*.css
```

No es obligatorio usar la carpeta `css`. Puedes dejar ficheros `.css` directamente en:

```text
html/assets/
```

La carpeta recomendada para mantener orden en proyectos grandes es:

```text
html/assets/css/
```

El paquete incluye dos CSS de ejemplo para validar la detección:

```text
html/assets/malecon_header_neon.css
html/assets/css/malecon_clean_glass.css
```

## Reconstrucción recomendada

Después de actualizar el ZIP, reconstruye los contenedores:

```bash
docker compose --env-file .env up -d --build
```

Abre la web y entra en:

```text
Estilos Marca > Aplicar CSS existente
```

Deberías ver los CSS de `/assets` y `/assets/css` en el desplegable.


## v9 - CSS por defecto y carpeta canónica

Se han instalado como CSS por defecto de arranque en `html/assets/css/`:

- `labHero_styles.css`
- `labHero_efects.css` generado desde `labHero_efects.json`
- `labHero_images.css`
- `malecon_salsa_glassgreen.css`
- `malecon_salsa_greenblack.css`

La carpeta canónica es `html/assets/css/`; no se mantienen duplicados en `html/` para evitar entradas repetidas en el selector.

Los CSS anteriores similares se han movido a `source_uploaded/archived_css_before_v9/` para evitar que aparezcan mezclados en el selector y para no sobreescribir los ficheros entregados en esta versión.

El selector de estilos de marca debe listar los CSS desde `/assets/css/`. La carpeta `css` no es técnicamente obligatoria si se usa `/assets`, pero queda recomendada como carpeta canónica para mantener separados estilos, imágenes y scripts.

### Media

No se han añadido imágenes ni vídeos nuevos porque en esta entrega solo se recibieron CSS y JSON. La carpeta persistente para recursos multimedia sigue siendo `html/media/`. Coloca ahí vídeos e imágenes reales para que el escáner de `/media/` los detecte.
