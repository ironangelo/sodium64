# Gate C, etapa 1: paquete experimental para N64

El `manifest.json` identifica el SHA exacto del candidato, el baseline y los
hashes de todos los archivos. Es un prototipo acotado: composición de 256 × 8
píxeles, primer tramo de ocho líneas, BG1/BG2, brillo completo y suma a mitad
con las excepciones de clipping/ausencia de Sub. No es todavía el iris completo.

## Archivos que se ejecutan

| Archivo en `hardware/` | Uso |
| --- | --- |
| `visual.z64` | Ventana móvil, sin carga de sonido activa. Continúa funcionando. |
| `mixed.z64` | Misma imagen, ocho voces SPC/DSP, trabajo CPU y DMA/HDMA. Continúa funcionando. |
| `visual-hw-profile.z64` | Captura SRAM del candidato visual. |
| `mixed-hw-profile.z64` | Captura SRAM del candidato con carga mixta. |
| `baseline-visual-hw-profile.z64` | Mismo guest visual en el master estable fijado. |
| `baseline-mixed-hw-profile.z64` | Mismo guest mixto en el master estable fijado. |
| `fixed`, `absent`, `control`, `clip`, `prevent`, `both` `.z64` | Seis controles estáticos originales. |

Los guests son originales; no contienen ROMs comerciales. El baseline conserva
su composición anterior: sirve para comparar estabilidad/coste, no se espera
que reproduzca la imagen reparada del candidato.

## Una sesión de hardware

1. Verificar `SHA256SUMS` después de extraer el paquete (`sha256sum -c SHA256SUMS`).
   Usar N64 NTSC y guardar modelo de consola, cartucho, firmware y salida de vídeo.
   Configurar el cartucho para SRAM de 32 KiB si no reconoce el encabezado.
2. Ejecutar `visual.z64`. En la zona superior debe verse una banda fina: negro
   dentro de una ventana que se mueve y cambia de ancho, mezcla rojo/verde
   fuera. `expected/` contiene ampliaciones exactas de varias fases. El resto
   de pantalla está fuera del contrato del prototipo. Grabar unos 20 segundos
   para observar continuidad, corrupción o congelamiento.
3. Ejecutar `mixed.z64`: misma banda y sonido sostenido de ocho tonos. Grabar
   imagen y audio. Registrar silencios, cortes, distorsión o bloqueos. El audio
   de referencia es una señal sintética, no música.
4. Ejecutar cada variante `*-hw-profile.z64` por separado. No cambiar ajustes:
   fuerza frameskip 0, APU 21, audio 4 y precision 8. Usa dos ventanas de 60 VI
   de calentamiento y cinco ventanas de 60 VI medidas. Al terminar guarda SRAM
   y deja la pantalla roja; esperar ese rojo, volver al menú del cartucho según
   su procedimiento de guardado y copiar el save antes de correr otra variante.
5. Conservar los cuatro saves con nombres distintos, vídeo y hashes. La sesión
   debe devolver una captura válida por workload y build; si falta el rojo o el
   decoder rechaza el save, registrar fallo sin convertirlo en una medición.

El candidato normal ya usa los ajustes anteriores por defecto. Las variantes
baseline de este paquete son HW_PROFILE y también los fuerzan: la comparación
no depende de los defaults históricos de underclock del master.

## Decodificar sin nueva infraestructura

Desde la raíz del paquete, por ejemplo para el candidato mixto:

```sh
python3 scripts/hw_profile_report.py mixed.sra --snapshot-output mixed-samples.bin --json-output mixed-hardware.json
python3 scripts/profile_report.py mixed-samples.bin qualified/hw-profile/build/sodium64.elf --map qualified/hw-profile/build/sodium64.map --json-output mixed-profile.json
```

Para el baseline, usar **su** ELF/map en `qualified/baseline-hw-profile/build/`.
No intercambiar símbolos entre builds. `profile_report.py` requiere GNU `nm`
con soporte para el ELF MIPS; admite `--nm` para elegirlo. Guardar también el
SHA256 del save original, no sólo el JSON decodificado.

## Decisión que desbloquea la etapa 2

- Imagen: ventana y composición correctas, sin corrupción en el área declarada.
- Propiedad/sincronización: estabilidad de la publicación tras SyncFull; un
  bloqueo o imagen parcial en N64 invalida la conclusión de laboratorio.
- Trabajo y rendimiento: comparar los cinco presupuestos guest/60 VI del mismo
  workload entre baseline y candidato. 60/60 en las cinco ventanas es el
  objetivo de throughput; vídeo/audio aportan evidencia separada de presentación.
- Audio: voces activas y señal estable, conservando full-rate. Sonido audible o
  throughput correcto no prueban fidelidad PCM exhaustiva ni deriva a largo plazo.

La etapa 1 prepara y valida este paquete en laboratorio. La etapa 2 obtiene la
autoridad de N64 real. Este resultado no demuestra compatibilidad comercial,
coste de composición a pantalla completa ni cierre de Gate C.
