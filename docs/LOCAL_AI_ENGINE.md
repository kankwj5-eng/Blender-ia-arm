# Local AI Engine v1 — Blender ARM / Android

Estado: código integrado en el árbol fuente; pruebas host pasan. APK Android pendiente de compilar en un builder con SDK/NDK.

## Objetivo

El agente debe poder trabajar sin proveedores externos. El modelo se ejecuta en el teléfono, observa el estado real de Blender, llama herramientas estructuradas y corrige iterativamente sus resultados. Internet es opcional para descargar modelos/recursos, nunca un requisito para inferencia una vez instalado el GGUF.

## Arquitectura implementada

`AiPanel` selecciona **Modelo local** por defecto. `LocalLlamaRuntime` inicia un `llama-server` ARM64 empaquetado dentro de la APK, limitado a loopback y modo offline. `AgentSession` usa el mismo bucle de herramientas que los proveedores OpenAI-compatible, por lo que el backend local recibe escena, selección, memoria del proyecto y los schemas del `ToolRegistry`.

Flujo:

`usuario -> AgentSession -> llama.cpp localhost -> tool call -> AndroidTransport -> Bridge -> Blender main thread -> resultado -> modelo`

El proceso llama.cpp nunca llama `bpy` directamente. Toda mutación de RNA continúa ocurriendo en el hilo propietario de Blender.

## Cambios principales

- `LocalLlamaRuntime.java`: arranque/parada/health del servidor local, puerto loopback dinámico, `--offline`, sin WebUI ni herramientas internas del servidor.
- `LocalModelCatalog.java`: dos modelos GGUF curados, descarga reanudable, almacenamiento app-private y SHA-256 obligatorio.
- `AgentSession.java`: `Modelo local` usa el bucle completo de agente (24 rondas / 64 llamadas), visión opcional y herramientas reales.
- `AiPanel.java`: modelo local como opción predeterminada, ruta/contexto/hilos/capas GPU y botones de descarga.
- `build_llama_cpp_android.sh`: build ARM64 fijado a una revisión concreta de llama.cpp; CPU/KleidiAI es la ruta base compatible.
- `package.sh`: empaqueta `llama-server` como ejecutable `lib*.so`, igual que el intérprete Python que ya usa el port Android.
- `blender.python`: escape hatch aprobado por el usuario para operaciones no cubiertas por herramientas específicas. Expone `bpy`, `bmesh`, `mathutils` y `math`; bloquea imports, dunder, filesystem builtins y `while` sin cota.
- `project.memory.*`: memoria compacta persistida dentro del `.blend`; se incorpora automáticamente al contexto de cada nueva petición.

## Modelos iniciales

Los downloads están fijados por URL/revisión y SHA-256:

- Qwen3 0.6B Q4_0 — modo ligero (~429 MB).
- Qwen3 1.7B Q4_K_M — opción más capaz (~1.28 GB).

El modelo no se incluye dentro de la APK para no inflarla: se descarga una vez o el usuario selecciona cualquier GGUF compatible ya presente en el dispositivo.

## Seguridad y límites deliberados

- El servidor escucha únicamente en `127.0.0.1` y se inicia con `--offline`.
- No se habilitan `--tools`, `--agent`, MCP ni shell de llama.cpp. Las únicas acciones provienen del ToolRegistry de Blender.
- `blender.python`, borrado, guardado y Undo requieren aprobación Android antes de cruzar el bridge.
- El Python avanzado es un mecanismo de automatización de Blender, no un sandbox de seguridad general. Por eso sigue protegido por aprobación explícita.
- Las respuestas de excepciones no filtran trazas, secretos ni paths arbitrarios al proveedor.

## Verificación actual

Ejecutar desde la raíz:

```bash
python3 -m unittest discover -s tests/python/blender_ai -p 'test_*.py' -v
bash -n build_files/android/ai/build_llama_cpp_android.sh
bash -n build_files/android/apk/package.sh
```

En este punto pasan 40 tests host. Cubren bridge, concurrencia, lifecycle, controles, schema, agente local heredado, validador de Python y memoria de proyecto.

## Gates pendientes antes de llamar a esto una APK validada

1. Compilar Java contra el `android.jar` real y construir `llama-server` con el NDK configurado por el proyecto.
2. Ensamblar/firmar APK y confirmar que PackageManager extrae `libllama_server_bin.so` como ejecutable.
3. Arrancar un GGUF real en ARM64 y probar `/health`, `/v1/models` y tool calling.
4. Pruebas Mali: memoria pico, tokens/s, temperatura, pausa/stop, rotación, suspensión/reanudación y viewport Vulkan.
5. Medir 0.6B vs 1.7B en tareas Blender y ajustar contexto/prompt/tool routing.
6. Segunda ruta de aceleración: MLC/OpenCL o llama.cpp Vulkan para Mali, manteniendo CPU como fallback.
