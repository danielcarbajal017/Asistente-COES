"""
============================================================
 CONSTRUIR ÍNDICE  (la "memoria" del agente)
============================================================
Lee TODOS los PDF de la carpeta data/ y guarda la memoria del
agente en la carpeta vector_store/.

- El cerebro de búsqueda corre en la máquina (no necesita llave para construir).
- Ejecuta este script UNA VEZ, y cada vez que agregues archivos
  nuevos a data/.

Uso:
    python construir_indice.py
============================================================
"""
import os
import sys
import time
from pathlib import Path

# Forzar UTF-8 en la salida (la consola de Windows usa cp1252 y rompe con ciertos caracteres)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from pypdf import PdfReader
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

import motor_ia

CARPETA_DATOS = "data"
CARPETA_MEMORIA = "vector_store"


def cargar_pdfs(carpeta=CARPETA_DATOS):
    """Lee todos los PDF de la carpeta, un documento por página, con su número de página."""
    documentos = []
    archivos = sorted(Path(carpeta).glob("*.pdf"))
    if not archivos:
        print(f"⚠️  No se encontraron PDF en la carpeta '{carpeta}/'.")
        return documentos
    for pdf_path in archivos:
        lector = PdfReader(str(pdf_path))
        paginas_con_texto = 0
        for num, pagina in enumerate(lector.pages, start=1):
            texto = motor_ia.limpiar_pagina(pagina.extract_text() or "")
            if texto.strip():
                documentos.append(
                    Document(
                        text=texto,
                        metadata={"file_name": pdf_path.name, "page_label": str(num)},
                    )
                )
                paginas_con_texto += 1
        print(f"   • {pdf_path.name}: {paginas_con_texto} páginas con texto")
    return documentos


def main():
    t0 = time.time()

    # Cerebro de búsqueda (corre en la máquina; no necesita llave para construir).
    Settings.embed_model = motor_ia.cargar_embeddings()
    print(f"[{time.time()-t0:.0f}s] modelo de embeddings listo")

    # 1) Leer todos los archivos
    print("\n📚 Leyendo archivos de la carpeta 'data/'...")
    documentos = cargar_pdfs()
    if not documentos:
        print("❌ No hay nada que indexar. Agrega PDF a la carpeta 'data/' y vuelve a ejecutar.")
        return
    total_chars = sum(len(d.text) for d in documentos)
    print(f"[{time.time()-t0:.0f}s] {len(documentos)} páginas en total ({total_chars:,} caracteres)")

    # 2) Construir el índice (calcula los vectores)
    #    Usamos trozos GRANDES (una página completa por trozo) para NO separar
    #    las tablas de sus títulos/cifras. Probamos trozos de 512 y empeoró:
    #    cortaba las tablas de costos y perdía los montos. Página completa
    #    (con un poco de solapamiento entre páginas) da mejores respuestas.
    print("\n🧠 Construyendo la memoria del agente (calculando vectores)...")
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
    index = VectorStoreIndex.from_documents(documentos, transformations=[splitter])
    print(f"[{time.time()-t0:.0f}s] índice construido")

    # 3) Guardar en disco (+ firma de los documentos, para la auto-reconstrucción)
    index.storage_context.persist(CARPETA_MEMORIA)
    (Path(CARPETA_MEMORIA) / "firma_datos.txt").write_text(
        motor_ia.firma_datos(CARPETA_DATOS), encoding="utf-8"
    )
    print(f"\n💾 Memoria guardada en la carpeta '{CARPETA_MEMORIA}/'.")
    print(f"[{time.time()-t0:.0f}s] LISTO. Ya puedes hacer preguntas con: python preguntar.py")


if __name__ == "__main__":
    main()
