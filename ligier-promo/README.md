# Ligier: video promocional

Video de 54 s en 1920×1080 a 30 fps, con música sintetizada. Presenta **Ligier Grass Bio**, el producto estrella, y los tres lanzamientos: **Cero**, **Tracker** y **Orbit**.

Archivo final: `output/ligier-promo.mp4`

## Guion

| Tiempo | Escena | Qué pasa |
|---|---|---|
| 0:00–0:05 | Intro | Amanecer sobre el lote con niebla de pulverización. Se arma el logo LIGIER y aparece "Especialistas en calidad de aplicación". |
| 0:05–0:10 | Cada gota cuenta | Plano macro de una hoja con dos casos. Sin adyuvante, la gota rebota y se evapora. Con Grass Bio, moja, cubre y penetra. |
| 0:10–0:17 | Grass Bio | Bidón como producto estrella, con los beneficios: penetración, antievaporante, mojado y estabilidad del caldo. |
| 0:17–0:20 | 3 nuevos lanzamientos | Aparecen los bidones de Cero, Tracker y Orbit. |
| 0:20–0:29 | Cero | Se carga un tanque y la espuma desborda. Al verter Cero, la espuma desaparece y el medidor baja de 100 % a 0 %. |
| 0:29–0:38 | Tracker | De noche en el cultivo, una linterna UV de 365 nm barre las hojas. Las gotas con trazador se iluminan y aparecen retículas de verificación. |
| 0:38–0:47 | Orbit | Un dron pulverizador al atardecer, con anillos orbitales. Las gotas bajan en espiral hasta el cultivo. |
| 0:47–0:54 | Cierre | Los cuatro bidones, el logo, "Aplicá mejor." y ligieragro.com.ar. |

## Cómo regenerarlo

```bash
python3 music.py      # crea output/soundtrack.wav
node render.js        # renderiza los cuadros con Chromium (Playwright) y ffmpeg, y genera output/ligier-promo.mp4
node render.js --stills 8,25,36   # cuadros de prueba en output/stills/
```

Para ver la animación en vivo, abrí `index.html` en el navegador. Hacé clic para reiniciarla con la música.

Toda la animación está en `index.html`, en canvas. Cada escena es una función `sNombre(t, duración)` y la línea de tiempo está en `SCENES`. Los textos, colores (`PRODUCTS`) y tiempos se editan ahí. Si cambiás las duraciones, actualizá también `BOUNDS` en `music.py`.

## Pendientes

- Los colores de marca y las etiquetas de los bidones son **ilustrativos**, porque no se pudo acceder a ligieragro.com.ar desde el entorno de render. Conviene reemplazarlos por el logo, la paleta y las fotos reales de los envases.
- Los textos de producto salen de información pública:
  - Grass Bio: penetración, antievaporante, humectante y estabilizante del caldo.
  - Cero: antiespumante para la preparación del caldo.
  - Tracker: trazador visual con marcador fluorescente visible con UV de 365 nm, que reemplaza las tarjetas hidrosensibles.
  - Orbit: adyuvante de doble acción para aplicaciones aéreas.

  Hay que validarlos con el equipo técnico antes de publicar.
