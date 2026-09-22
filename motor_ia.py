"""
============================================================
 MOTOR IA  (lógica central compartida)
============================================================
Centraliza: modelos de IA, respaldo automático (fallback) entre
varios modelos gratis, detección de cuota agotada, y el prompt
de veracidad. Lo usan app.py (web) y preguntar.py (consola).
============================================================
"""
import os
from pathlib import Path

CARPETA_MEMORIA = "vector_store"
# Cerebro de búsqueda LOCAL-en-el-servidor (sin límite de cuota; sirve a todos los usuarios).
MODELO_EMBED = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 6  # cuántos trozos de contexto usar por pregunta

# Instrucción de VERACIDAD: el modelo responde SOLO con el contexto.
PROMPT_VERAZ = (
    "Eres un asistente experto en el Plan de Transmisión eléctrica del COES (Perú).\n"
    "Responde la pregunta del usuario USANDO ÚNICAMENTE la información del contexto de abajo.\n\n"
    "Reglas estrictas:\n"
    "- Si la respuesta NO está en el contexto, di exactamente: 'No encontré esa información en los "
    "documentos disponibles.' No inventes ni uses conocimiento externo.\n"
    "- Responde en español, de forma clara, técnica y ordenada.\n"
    "- Cuando cites cifras (MW, GWh, MVA, US$, fechas), tómalas EXACTAMENTE del contexto.\n"
    "- Sé conciso pero completo.\n\n"
    "Contexto:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Pregunta: {query_str}\n"
    "Respuesta:"
)


def _leer_archivo_key(nombre):
    f = Path(nombre)
    if f.exists():
        return f.read_text(encoding="utf-8").strip().strip('"').strip("'")
    return None


def cargar_api_keys(secrets=None):
    """Carga las API keys desde (1) secrets de Streamlit, (2) archivos locales, (3) variables de entorno.
    Devuelve un dict indicando qué proveedores quedaron disponibles."""
    # Groq
    groq = None
    if secrets is not None:
        try:
            groq = secrets["GROQ_API_KEY"]
        except Exception:
            groq = None
    groq = groq or _leer_archivo_key("groq_key.txt") or os.environ.get("GROQ_API_KEY")
    if groq:
        os.environ["GROQ_API_KEY"] = groq

    # Google Gemini (opcional, segundo proveedor gratis)
    google = None
    if secrets is not None:
        try:
            google = secrets["GOOGLE_API_KEY"]
        except Exception:
            google = None
    google = google or _leer_archivo_key("google_key.txt") or os.environ.get("GOOGLE_API_KEY")
    if google:
        os.environ["GOOGLE_API_KEY"] = google

    return {"groq": bool(groq), "gemini": bool(google)}


def firma_datos(carpeta="data"):
    """Huella del conjunto de documentos (nombre+tamaño). Si cambia, hay que reconstruir."""
    items = []
    for p in sorted(Path(carpeta).glob("*.pdf")):
        items.append(f"{p.name}:{p.stat().st_size}")
    return "|".join(items)


def cargar_embeddings():
    """Cerebro de búsqueda: FastEmbed (ONNX, liviano, sin torch). Corre en el servidor
    (sin límite de cuota), sirve a todos los usuarios y funciona en hosting gratis."""
    from llama_index.embeddings.fastembed import FastEmbedEmbedding

    return FastEmbedEmbedding(model_name=MODELO_EMBED)


def construir_lista_modelos():
    """Lista ordenada de modelos a usar (con respaldo). Se prueban en orden hasta que uno responda."""
    modelos = []
    if os.environ.get("GROQ_API_KEY"):
        from llama_index.llms.groq import Groq
        modelos.append(("Groq · gpt-oss-120b", Groq(model="openai/gpt-oss-120b")))
        modelos.append(("Groq · gpt-oss-20b", Groq(model="openai/gpt-oss-20b")))
    if os.environ.get("GOOGLE_API_KEY"):
        from llama_index.llms.google_genai import GoogleGenAI
        modelos.append(
            ("Gemini · 3.6-flash", GoogleGenAI(model="models/gemini-3.6-flash",
                                               api_key=os.environ["GOOGLE_API_KEY"]))
        )
    return modelos


def es_error_de_cuota(e):
    """Detecta si el error se debe a límite/cuota agotada del proveedor."""
    s = str(e).lower()
    señales = ["429", "rate limit", "rate_limit", "quota", "resource_exhausted",
               "too many requests", "insufficient_quota"]
    return any(x in s for x in señales)


def responder(pregunta, nodos, modelos):
    """Genera la respuesta probando los modelos en orden (respaldo automático).

    Devuelve (respuesta, nombre_modelo, error) donde:
      - error es None si todo salió bien.
      - error = {'tipo': 'cuota'|'otro', 'detalle': str} si TODOS los modelos fallaron.
    """
    from llama_index.core import Settings, PromptTemplate
    from llama_index.core.response_synthesizers import get_response_synthesizer

    if not modelos:
        return None, None, {"tipo": "otro", "detalle": "No hay ningún modelo configurado (falta API key)."}

    fallos = []
    todos_por_cuota = True
    for nombre, llm in modelos:
        try:
            Settings.llm = llm
            synth = get_response_synthesizer(text_qa_template=PromptTemplate(PROMPT_VERAZ))
            respuesta = synth.synthesize(pregunta, nodes=nodos)
            return respuesta, nombre, None
        except Exception as e:  # noqa: BLE001
            if not es_error_de_cuota(e):
                todos_por_cuota = False
            fallos.append(f"{nombre}: {e}")
            continue

    tipo = "cuota" if todos_por_cuota else "otro"
    return None, None, {"tipo": tipo, "detalle": " | ".join(fallos)}
