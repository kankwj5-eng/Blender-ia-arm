#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

def edit(rel, replacements):
    p = root / rel
    s = p.read_text()
    for old, new in replacements:
        if old in s:
            s = s.replace(old, new, 1)
            continue
        if new in s:
            continue
        raise SystemExit(f'Hotfix base mismatch: {rel}: {old[:80]!r}')
    p.write_text(s)
    print('hotfix:', rel)

runtime='build_files/android/apk/app/src/main/java/org/blender/blender/ai/LocalModelRuntime.java'
edit(runtime, [
('import android.app.Activity;\n', 'import android.app.Activity;\nimport android.app.ActivityManager;\n'),
('  public File directory(){return modelDir;}\n\n', '''  public File directory(){return modelDir;}\n\n  public long totalMemoryBytes(){\n    try{\n      ActivityManager am=(ActivityManager)activity.getSystemService(Activity.ACTIVITY_SERVICE);\n      ActivityManager.MemoryInfo info=new ActivityManager.MemoryInfo();am.getMemoryInfo(info);return info.totalMem;\n    }catch(Exception ex){return 0;}\n  }\n\n  public int recommendedContext(){\n    long gib=totalMemoryBytes()/(1024L*1024L*1024L);\n    if(gib>0&&gib<=4)return 1536;\n    if(gib<=6&&gib>0)return 2048;\n    if(gib<=8&&gib>0)return 3072;\n    return 4096;\n  }\n\n  public int recommendedThreads(){\n    int cores=Math.max(1,Runtime.getRuntime().availableProcessors());\n    if(cores<=4)return Math.max(2,cores-1);\n    return Math.min(4,Math.max(2,cores/2));\n  }\n\n  public String memoryProfile(){\n    long total=totalMemoryBytes();\n    if(total<=0)return "perfil automático";\n    return String.format(Locale.ROOT,"%.1f GB RAM · contexto recomendado %d",total/(1024.0*1024.0*1024.0),recommendedContext());\n  }\n\n'''),
('c.contextWindow>0?c.contextWindow:4096', 'c.contextWindow>0?c.contextWindow:recommendedContext()'),
('c.localThreads>0?c.localThreads:Math.max(2,Runtime.getRuntime().availableProcessors()/2)', 'c.localThreads>0?c.localThreads:recommendedThreads()'),
])

# Normalize the complete llama.cpp launch block regardless of previous tuning.
p = root / runtime
s = p.read_text()
rows = s.splitlines()
start_i = next((i for i,line in enumerate(rows) if 'Collections.addAll(cmd,server().getAbsolutePath()' in line), -1)
gpu_i = next((i for i,line in enumerate(rows) if i > start_i and 'if(gpu>0)' in line), -1)
if start_i < 0 or gpu_i < 0:
    raise SystemExit('Hotfix base mismatch: llama.cpp launch block not found')
canonical = [
'      Collections.addAll(cmd,server().getAbsolutePath(),"--model",model.getAbsolutePath(),"--alias","blender-local","--host","127.0.0.1","--port",Integer.toString(PORT),',
'        "--ctx-size",Integer.toString(context),"--threads",Integer.toString(threads),"--threads-batch",Integer.toString(threads),',
'        "--batch-size","128","--ubatch-size","64","--cache-type-k","q8_0","--cache-type-v","q8_0","--parallel","1","--jinja","--offline","--no-webui","--no-warmup","--sleep-idle-seconds","90","--api-key",apiKey);',
]
rows[start_i:gpu_i] = canonical
p.write_text('\n'.join(rows) + ('\n' if s.endswith('\n') else ''))
print('hotfix: llama.cpp low-RAM launch block')

panel='build_files/android/apk/app/src/main/java/org/blender/blender/ai/AiPanel.java'
edit(panel, [
('c.localContext=prefs.getInt("local.context",4096);c.localThreads=prefs.getInt("local.threads",Math.max(2,Math.min(4,Runtime.getRuntime().availableProcessors()/2)))', 'c.localContext=prefs.contains("local.context")?prefs.getInt("local.context",localModels.recommendedContext()):localModels.recommendedContext();c.localThreads=prefs.contains("local.threads")?prefs.getInt("local.threads",localModels.recommendedThreads()):localModels.recommendedThreads()'),
('    form.addView(label("llama.cpp ejecuta el GGUF dentro del teléfono. Tras descargar/importar el modelo, la inferencia funciona sin Internet ni API key.",12,Color.DKGRAY));\n', '    form.addView(label("llama.cpp ejecuta el GGUF dentro del teléfono. Tras descargar/importar el modelo, la inferencia funciona sin Internet ni API key.",12,Color.DKGRAY));\n    form.addView(label("Perfil automático: "+localModels.memoryProfile()+". KV cache Q8_0 para reducir RAM.",12,Color.DKGRAY));\n'),
('    EditText context=field("Contexto (tokens)",Integer.toString(prefs.getInt("local.context",4096)));context.setInputType(InputType.TYPE_CLASS_NUMBER);form.addView(context);\n    int defaultThreads=Math.max(2,Math.min(4,Runtime.getRuntime().availableProcessors()/2));EditText threads=field("Hilos CPU",Integer.toString(prefs.getInt("local.threads",defaultThreads)));threads.setInputType(InputType.TYPE_CLASS_NUMBER);form.addView(threads);', '    int defaultContext=localModels.recommendedContext();EditText context=field("Contexto (tokens)",Integer.toString(prefs.contains("local.context")?prefs.getInt("local.context",defaultContext):defaultContext));context.setInputType(InputType.TYPE_CLASS_NUMBER);form.addView(context);\n    int defaultThreads=localModels.recommendedThreads();EditText threads=field("Hilos CPU",Integer.toString(prefs.contains("local.threads")?prefs.getInt("local.threads",defaultThreads):defaultThreads));threads.setInputType(InputType.TYPE_CLASS_NUMBER);form.addView(threads);'),
('int ctx=number(context,4096,1024,32768),th=number(threads,defaultThreads,1,16)', 'int ctx=number(context,defaultContext,1024,32768),th=number(threads,defaultThreads,1,16)'),
('int ctx=number(context,4096,1024,32768),th=number(threads,defaultThreads,1,16)', 'int ctx=number(context,defaultContext,1024,32768),th=number(threads,defaultThreads,1,16)'),
])

catalog='build_files/android/apk/app/src/main/java/org/blender/blender/ai/LocalModelCatalog.java'
edit(catalog, [('Blender-ia-arm/0.4', 'Blender-ia-arm/0.5')])

packager='build_files/android/ai/package_lite_ai.py'
edit(packager, [
("node.set(android+'versionCode', '4')", "node.set(android+'versionCode', '5')"),
("node.set(android+'versionName', '0.4-local-llama-development')", "node.set(android+'versionName', '0.5-local-llama-development')"),
("app.set(android+'label', 'Blender AI Lite')", "app.set(android+'label', 'Blender IA ARM')"),
("activity.set(android+'label', 'Blender AI Lite')", "activity.set(android+'label', 'Blender IA ARM')"),
])
