# Ski Info — app de Android

Envoltorio nativo mínimo (una sola `Activity` con un `WebView`) que carga
`https://sospi01.github.io/SKI-APP/`. No es un TWA: no necesita verificar
ningún dominio (`assetlinks.json`) porque el `WebView` no le pide a Android
que confíe en el origen web como si fuera la propia app — simplemente
muestra la página dentro de un componente propio. Toda la lógica (buscador,
mapa, tiempo, sol) sigue viviendo en `docs/index.html`; esta app solo le
pone icono, nombre y pantalla completa sin barra de navegador.

## Por qué no se puede compilar aquí

Compilar un APK/AAB necesita el Android SDK, que se descarga de servidores
de Google (`dl.google.com`) a los que este entorno no tiene acceso. Por eso
la compilación real ocurre en GitHub Actions
(`.github/workflows/build-android.yml`), que sí tiene acceso normal a
internet. El proyecto en sí (código, recursos, iconos, Gradle wrapper) está
completo y committeado; solo falta que ese workflow lo compile.

## Puesta en marcha (una sola vez)

1. **Añade los secretos de firma al repo** (Settings → Secrets and
   variables → Actions → New repository secret). El keystore de firma ya
   está generado; los valores exactos te los ha pasado Claude como archivo
   aparte (nunca se ha subido al repositorio, es sensible):
   - `SKIINFO_KEYSTORE_BASE64` — el `.jks` codificado en base64.
   - `SKIINFO_KEYSTORE_PASSWORD`
   - `SKIINFO_KEY_ALIAS`
   - `SKIINFO_KEY_PASSWORD`

   Guarda también el archivo `.jks` original en un sitio seguro (gestor de
   contraseñas, disco cifrado) — si lo pierdes y no has activado *Play App
   Signing*, no podrás publicar actualizaciones de la app con la misma
   identidad. Al crear la app en Play Console, dejar activado *Play App
   Signing* (viene por defecto) hace que esto sea recuperable si alguna vez
   se pierde.

2. **Lanza el build**: pestaña Actions → "Build Android app" → Run workflow
   (o simplemente vuelve a hacer push a algo dentro de `mobile-app/`).

3. **Descarga el resultado**: al terminar, el run tiene un artifact
   `ski-info-release` con el `.aab` (para subir a Play Console) y un `.apk`
   (para probar la app directamente en un móvil Android antes de publicar,
   instalándolo con "Fuentes desconocidas" activado).

## Estructura

- `app/src/main/java/com/sospedra/skiinfo/MainActivity.java` — el `WebView`,
  manejo del botón atrás, pantalla de "sin conexión" con reintento, y
  apertura de los enlaces externos (web oficial, Booking…) en el navegador
  del sistema mediante Custom Tabs en vez de dentro del `WebView`.
- `app/src/main/res/` — iconos (adaptativos + legacy), tema, strings.
- Package: `com.sospedra.skiinfo` — **irreversible una vez publicado**.

## Pendiente fuera de este repo

- Crear la ficha de la app en Play Console (título, descripción, capturas,
  cuestionario de contenido, formulario de seguridad de datos).
- Subir el `.aab` a una pista (interna / cerrada / producción).
- La política de privacidad ya está lista en `docs/privacy.html` — su URL
  pública es `https://sospi01.github.io/SKI-APP/privacy.html`.
