"""
============================================================
 PREGUNTAR  (consola) — usa el motor con respaldo automático
============================================================
Carga la memoria (vector_store/) y responde preguntas por consola,
con respaldo entre modelos gratis y aviso si se agota la cuota.

Uso:
  python preguntar.py "¿De qué trata el informe?"   (una pregunta)
  python preguntar.py                                 (modo chat)
============================================================
"""
import os
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import motor_ia


def cargar_motor():
    from llama_index.core import Settings, StorageContext, load_index_from_storage

    if not Path(motor_ia.CARPETA_MEMORIA).exists():
        print(f"❌ No existe '{motor_ia.CARPETA_MEMORIA}/'. Ejecuta primero: python construir_indice.py")
        sys.exit(1)

    Settings.embed_model = motor_ia.cargar_embeddings()
    storage = StorageContext.from_defaults(persist_dir=motor_ia.CARPETA_MEMORIA)
    index = load_index_from_storage(storage)
    return index


def responder_consola(index, modelos, pregunta):
    nodos = index.as_retriever(similarity_top_k=motor_ia.TOP_K).retrieve(pregunta)
    resp, modelo, error = motor_ia.responder(pregunta, nodos, modelos)
    if error is None:
        print("\n🤖 RESPUESTA:\n")
        print(resp.response)
        print("\n📄 Fuentes:")
        for i, n in enumerate(resp.source_nodes, 1):
            print(f"   {i}. {n.metadata.get('file_name','?')} — página {n.metadata.get('page_label','?')} "
                  f"(relevancia {n.score:.3f})")
        print(f"\n(Respondido por: {modelo})")
    elif error["tipo"] == "cuota":
        print("\n🚫 Se agotó la cuota gratis de los modelos. Intenta más tarde.")
    else:
        print(f"\n❌ Error: {error['detalle'][:400]}")


def main():
    disponibles = motor_ia.cargar_api_keys()
    if not disponibles["groq"] and not disponibles["gemini"]:
        print("❌ Falta la API key. Crea groq_key.txt (o define GOOGLE_API_KEY).")
        sys.exit(1)

    print("⏳ Cargando la memoria del agente...")
    t0 = time.time()
    index = cargar_motor()
    modelos = motor_ia.construir_lista_modelos()
    print(f"✅ Listo en {time.time()-t0:.0f}s. Modelos: {', '.join(n for n,_ in modelos)}\n")

    if len(sys.argv) > 1:
        responder_consola(index, modelos, " ".join(sys.argv[1:]))
        return

    print("💬 Modo chat. Escribe tu pregunta ('salir' para terminar).\n")
    while True:
        try:
            q = input("Tu pregunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Chat terminado.")
            break
        if q.lower() in ("salir", "exit", "quit", ""):
            print("👋 Chat terminado.")
            break
        responder_consola(index, modelos, q)
        print("\n" + "-" * 60)


if __name__ == "__main__":
    main()
