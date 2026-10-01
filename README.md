# Blender-ia-arm

Fork experimental de Blender para Android ARM con un agente de IA local integrado.

## Estado actual

El código base completo todavía no se ha importado a este repositorio. El desarrollo parte del ZIP `blender_for_android-main(1).zip` proporcionado para el proyecto. El primer incremento reproducible está documentado como **Local AI Engine v1**.

Local AI Engine v1 añade:

- `llama.cpp`/`llama-server` ARM64 empaquetado dentro de la APK.
- proveedor **Modelo local** sin API externa; localhost + modo offline.
- descarga verificada de GGUF locales.
- bucle de agente con tool calling sobre Blender.
- `blender.python` aprobado para operaciones avanzadas con `bpy`, `bmesh` y `mathutils`.
- memoria persistente dentro del `.blend`.
- 40 pruebas host pasando.

Consulta `docs/LOCAL_AI_ENGINE.md` para arquitectura, seguridad y gates pendientes.

> Nota: todavía no se declara una APK Android validada. Falta compilar este incremento con el SDK/NDK del proyecto y probarlo en un dispositivo ARM64/Mali real.
