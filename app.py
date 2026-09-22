"""
============================================================
 APP WEB — COES · Asistente Especializado del Plan de Transmisión
============================================================
Interfaz profesional tipo asistente de IA:
- Cabecera con marca COES + estado "en línea".
- Barra lateral con historial de conversaciones.
- Personaje/bot con saludo, chips con iconos.
- Barra de escritura con adjuntar + selector de modelo + enviar.
- Respuestas veraces (solo con los documentos) y con fuentes.
- Respaldo automático entre modelos gratis (Groq / Gemini).

Personaje: si existe 'coes_bot.png' (o .jpg) se usa como avatar central.
Logo:      si existe 'coes_logo.png' (o .jpg/.svg) se usa como logo.

Ejecutar:  streamlit run app.py
============================================================
"""
import base64
import hashlib
import io
import os

import streamlit as st

import motor_ia

st.set_page_config(page_title="COES · Asistente del Plan de Transmisión", page_icon="⚡", layout="wide")

NAVY, GOLD = "#14284B", "#F2A900"

# ==================================================================
#  MARCA / PERSONAJE (usa archivo real si existe)
# ==================================================================
LOGO_SVG = (
    '<svg width="120" height="42" viewBox="0 0 132 46" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<g stroke="#F2A900" stroke-width="3.4" stroke-linecap="round" fill="none">'
    '<path d="M23 40 C 16 30, 14 20, 20 8"/><path d="M23 40 C 30 30, 32 20, 26 8"/>'
    '<path d="M23 40 C 12 34, 7 27, 6 18"/><path d="M23 40 C 34 34, 39 27, 40 18"/>'
    '<path d="M23 40 L 23 20"/></g><circle cx="23" cy="41" r="2.6" fill="#F2A900"/>'
    '<text x="50" y="34" font-family="Inter,Arial,sans-serif" font-size="26" font-weight="800" fill="#14284B">COES</text></svg>'
)

BOT_SVG = (
    '<svg width="170" height="170" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="60" cy="60" r="58" fill="#FFF6E0"/>'
    '<rect x="34" y="40" width="52" height="42" rx="12" fill="#14284B"/>'
    '<rect x="41" y="49" width="38" height="24" rx="7" fill="#0B1730"/>'
    '<circle cx="52" cy="61" r="4.6" fill="#F2A900"/><circle cx="68" cy="61" r="4.6" fill="#F2A900"/>'
    '<rect x="57" y="28" width="6" height="12" rx="3" fill="#14284B"/><circle cx="60" cy="26" r="5" fill="#F2A900"/>'
    '<rect x="26" y="52" width="7" height="18" rx="3.5" fill="#14284B"/>'
    '<rect x="87" y="52" width="7" height="18" rx="3.5" fill="#14284B"/>'
    '<path d="M60 84 v10" stroke="#14284B" stroke-width="4" stroke-linecap="round"/></svg>'
)


def _img_datauri(nombres):
    for n in nombres:
        if os.path.exists(n):
            datos = base64.b64encode(open(n, "rb").read()).decode()
            ext = "svg+xml" if n.endswith(".svg") else n.split(".")[-1]
            return f"data:image/{ext};base64,{datos}"
    return None


def logo_html(height=40):
    uri = _img_datauri(["coes_logo.png", "coes_logo.jpg", "coes_logo.jpeg", "coes_logo.svg", "logo_coes.png"])
    return f'<img src="{uri}" style="height:{height}px">' if uri else LOGO_SVG


def personaje_html(size=170):
    uri = _img_datauri(["coes_bot.png", "coes_bot.jpg", "coes_bot.jpeg", "bot_coes.png"])
    if uri:
        return (f'<img src="{uri}" style="width:{size}px;height:{size}px;border-radius:50%;'
                f'object-fit:cover;border:5px solid #FFF3D6;box-shadow:0 8px 24px rgba(16,24,40,.12)">')
    return BOT_SVG


# ==================================================================
#  ESTILOS
# ==================================================================
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }
      [data-testid="stAppViewContainer"] {
        background: radial-gradient(1100px 480px at 72% -12%, #FFF6E0 0%, #F7F8FA 42%, #F7F8FA 100%);
      }
      [data-testid="stToolbar"], footer, #MainMenu { visibility: hidden; }
      /* Quitar la franja superior vacía de Streamlit (usamos nuestra propia cabecera) */
      [data-testid="stHeader"] { display: none; }
      /* Menos espacio arriba/abajo para que todo "encaje" */
      [data-testid="stMain"] .block-container { padding-top: 0.6rem; padding-bottom: 1.2rem; }

      /* Sidebar */
      [data-testid="stSidebar"] { background:#FFFFFF; border-right:1px solid #ECEFF3; }
      [data-testid="stSidebar"] * { color:#14284B; }
      .sb-tit { font-weight:800; font-size:.95rem; margin:2px 0 8px; }
      /* Botón "Nueva Conversación" (primer botón del sidebar) */
      [data-testid="stSidebar"] .stButton>button {
        border-radius:12px; border:1px solid #ECEFF3; background:#F7F8FA; color:#14284B;
        text-align:left; font-weight:500; font-size:.83rem; padding:9px 12px;
      }
      [data-testid="stSidebar"] .stButton>button:hover { border-color:#F2A900; }

      /* Cabecera superior FIJA (sticky) */
      .topbar { display:flex; align-items:center; gap:14px; padding:12px 18px; background:#fff;
        border:1px solid #ECEFF3; border-radius:16px; box-shadow:0 6px 18px rgba(16,24,40,.08);
        margin-bottom:16px; position:sticky; top:0; z-index:1000; }
      .topbar .tit { font-size:1.18rem; font-weight:800; color:#14284B; line-height:1.15; }
      .topbar .sub { font-size:.8rem; color:#667085; }
      .topbar .right { margin-left:auto; display:flex; align-items:center; gap:10px; }
      .ico { width:34px; height:34px; border-radius:50%; background:#F7F8FA; border:1px solid #ECEFF3;
        display:flex; align-items:center; justify-content:center; font-size:1rem; }
      .badge-ia { font-size:.72rem; font-weight:700; color:#B7791F; background:#FFF6E0;
        border:1px solid #FCE7A6; padding:5px 11px; border-radius:999px; }

      /* Hero: personaje + globo */
      .hero { display:flex; flex-direction:column; align-items:center; text-align:center; padding:8px 10px 2px; }
      .globo { background:#14284B; color:#fff; padding:9px 14px; border-radius:14px 14px 14px 4px;
        font-size:.86rem; font-weight:500; margin-bottom:12px; box-shadow:0 4px 14px rgba(20,40,75,.18); }
      .hero h1 { font-size:1.7rem; font-weight:800; color:#14284B; margin:14px 0 4px; }
      .hero p { color:#667085; margin:0 auto; max-width:600px; }

      /* Fuentes / tag */
      .fuente { background:#F7F8FA; border-left:3px solid #F2A900; padding:6px 10px;
                border-radius:8px; margin:4px 0; font-size:.83rem; color:#334155; }
      .modelo-tag { font-size:.74rem; color:#94A3B8; margin-top:4px; }

      /* Chips de sugerencias (con icono) */
      div[data-testid="column"] .stButton>button {
        width:100%; text-align:left; white-space:normal; border-radius:16px;
        border:1px solid #ECEFF3; background:#fff; color:#14284B; font-weight:500;
        padding:16px 18px; box-shadow:0 1px 4px rgba(16,24,40,.04); transition:.15s; height:100%;
      }
      div[data-testid="column"] .stButton>button:hover {
        border-color:#F2A900; box-shadow:0 4px 14px rgba(242,169,0,.18); transform:translateY(-1px);
      }

      /* Barra de entrada unificada */
      [data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) {
        background:#fff; border:1px solid #E6EAF0; border-radius:28px;
        padding:6px 10px; box-shadow:0 3px 16px rgba(16,24,40,.07); align-items:center; gap:4px;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) [data-testid="stChatInput"] {
        border:none !important; background:transparent !important; box-shadow:none !important;
      }
      [data-testid="stChatInput"] textarea { font-size:1rem; }
      /* botón enviar dorado */
      [data-testid="stChatInput"] button { background:#F2A900 !important; border-radius:12px !important; }
      [data-testid="stChatInput"] button svg { color:#fff !important; fill:#fff !important; }
      /* botón "+" adjuntar redondo */
      [data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) [data-testid="stPopover"] button {
        border-radius:50%; width:42px; height:42px; padding:0; font-size:1.1rem;
        border:1px solid #E6EAF0; background:#F7F8FA; color:#14284B;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) [data-testid="stPopover"] button:hover {
        border-color:#F2A900; color:#B7791F;
      }
      /* selector de modelo como pill */
      [data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) [data-baseweb="select"] > div {
        border-radius:999px; border:1px solid #E6EAF0; background:#F7F8FA; min-height:42px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================================
#  CARGA
# ==================================================================
@st.cache_resource(show_spinner="⏳ Cargando la memoria del asistente...")
def cargar_base():
    from llama_index.core import Settings, StorageContext, load_index_from_storage

    Settings.embed_model = motor_ia.cargar_embeddings()
    if not os.path.exists(motor_ia.CARPETA_MEMORIA):
        return None
    storage = StorageContext.from_defaults(persist_dir=motor_ia.CARPETA_MEMORIA)
    return load_index_from_storage(storage)


@st.cache_resource(show_spinner=False)
def obtener_modelos_dict():
    return dict(motor_ia.construir_lista_modelos())


@st.cache_resource(show_spinner=False)
def hashes_oficiales():
    """Huellas (hash) de los PDF que YA están en la memoria oficial (carpeta data/)."""
    huellas = {}
    if os.path.exists("data"):
        for p in Path("data").glob("*.pdf"):
            huellas[hashlib.sha1(p.read_bytes()).hexdigest()] = p.name
    return huellas


@st.cache_resource(show_spinner=False)
def indexar_pdf_cacheado(file_hash, _nombre, _contenido):
    """Procesa un PDF subido y lo deja en caché (por su huella): si se vuelve a subir
    el MISMO archivo, se reutiliza al instante en vez de reprocesarlo."""
    from pypdf import PdfReader
    from llama_index.core import Document, VectorStoreIndex

    docs = []
    for num, pagina in enumerate(PdfReader(io.BytesIO(_contenido)).pages, start=1):
        texto = pagina.extract_text() or ""
        if texto.strip():
            docs.append(Document(text=texto, metadata={"file_name": _nombre, "page_label": str(num)}))
    return VectorStoreIndex.from_documents(docs) if docs else None


def recuperar_nodos(pregunta, base_index, extra_index):
    nodos = []
    if base_index is not None:
        nodos += base_index.as_retriever(similarity_top_k=motor_ia.TOP_K).retrieve(pregunta)
    if extra_index is not None:
        nodos += extra_index.as_retriever(similarity_top_k=motor_ia.TOP_K).retrieve(pregunta)
    return sorted(nodos, key=lambda n: (n.score or 0), reverse=True)[: motor_ia.TOP_K]


# ==================================================================
#  INICIALIZACIÓN
# ==================================================================
disponibles = motor_ia.cargar_api_keys(secrets=st.secrets if hasattr(st, "secrets") else None)
if not disponibles["groq"] and not disponibles["gemini"]:
    st.error("⚠️ No hay ninguna API key configurada. Añade groq_key.txt o google_key.txt para continuar.")
    st.stop()

base_index = cargar_base()
modelos_dict = obtener_modelos_dict()
nombres_modelos = list(modelos_dict.keys())

# Conversaciones (historial en memoria de la sesión)
if "convs" not in st.session_state:
    st.session_state.convs = [{"titulo": "Nueva conversación", "mensajes": []}]
    st.session_state.actual = 0
st.session_state.setdefault("cuota_agotada", False)
st.session_state.setdefault("modelo_sel", nombres_modelos[0])
st.session_state.setdefault("extra_index", None)

conv = st.session_state.convs[st.session_state.actual]

# ==================================================================
#  BARRA LATERAL — Historial de conversaciones
# ==================================================================
with st.sidebar:
    st.markdown(logo_html(60), unsafe_allow_html=True)
    st.markdown('<div class="sb-tit">🗂️ Historial de Conversaciones</div>', unsafe_allow_html=True)
    if st.button("➕  Nueva Conversación", use_container_width=True):
        st.session_state.convs.insert(0, {"titulo": "Nueva conversación", "mensajes": []})
        st.session_state.actual = 0
        st.rerun()
    st.divider()
    for i, c in enumerate(st.session_state.convs):
        etiqueta = c["titulo"] if len(c["titulo"]) <= 42 else c["titulo"][:42] + "…"
        tipo = "primary" if i == st.session_state.actual else "secondary"
        if st.button(f"💬 {etiqueta}", key=f"conv_{i}", use_container_width=True, type=tipo):
            st.session_state.actual = i
            st.rerun()

# ==================================================================
#  CABECERA SUPERIOR
# ==================================================================
st.markdown(
    f'<div class="topbar">{logo_html(50)}'
    '<div><div class="tit">COES · Asistente Especializado del Plan de Transmisión</div>'
    '<div class="sub">Sistema Eléctrico Interconectado Nacional · COES</div></div>'
    '<div class="right"><div class="ico">👤</div><div class="ico">⚙️</div>'
    '<div class="badge-ia">● en línea</div></div></div>',
    unsafe_allow_html=True,
)

if base_index is None:
    st.error("No se encontró la memoria (`vector_store/`). Ejecuta primero `python construir_indice.py`.")
    st.stop()

if st.session_state.cuota_agotada:
    st.warning("🚫 Se agotó la cuota gratis de los modelos. Intenta más tarde.", icon="⚠️")

# ==================================================================
#  BIENVENIDA (personaje + globo + chips)
# ==================================================================
SUGERENCIAS = [
    ("🕸️", "¿Cuáles son los proyectos vinculantes del plan de transmisión?"),
    ("📈", "¿Cuál es la demanda de energía y potencia proyectada?"),
    ("📋", "¿Qué criterios y metodología se usaron para evaluar los proyectos?"),
    ("🌐", "¿Qué interconexiones internacionales se proponen y su rentabilidad?"),
]

click = None
if not conv["mensajes"]:
    st.markdown(
        f'<div class="hero">'
        f'<div class="globo">¡Hola! Estoy aquí para ayudarte 👋</div>'
        f'{personaje_html(170)}'
        f'<h1>¿En qué podemos ayudarte hoy?</h1>'
        f'<p>Accede a la base de datos oficial y completa del Plan de Transmisión 2027–2036. '
        f'Respondo con base en los documentos e incluyo las fuentes.</p></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2 = st.columns(2)
    for i, (ico, s) in enumerate(SUGERENCIAS):
        col = c1 if i % 2 == 0 else c2
        if col.button(f"{ico}  {s}", key=f"sug_{i}"):
            click = s

# ==================================================================
#  HISTORIAL DE MENSAJES
# ==================================================================
msgs = conv["mensajes"]
for m in msgs:
    avatar = "🧑‍💼" if m["role"] == "user" else "⚡"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])
        if m.get("fuentes"):
            with st.expander("📄 Ver fuentes"):
                for f in m["fuentes"]:
                    st.markdown(f'<div class="fuente">{f}</div>', unsafe_allow_html=True)
        if m.get("modelo"):
            st.markdown(f'<div class="modelo-tag">Respondido por {m["modelo"]}</div>', unsafe_allow_html=True)

# ==================================================================
#  GENERAR RESPUESTA PENDIENTE (si el último mensaje es del usuario)
#  Así la pregunta aparece al instante y se ve el indicador "Analizando...".
# ==================================================================
if msgs and msgs[-1]["role"] == "user":
    modelos_ordenados = [(st.session_state.modelo_sel, modelos_dict[st.session_state.modelo_sel])] + [
        (n, m) for n, m in modelos_dict.items() if n != st.session_state.modelo_sel
    ]
    with st.chat_message("assistant", avatar="⚡"):
        with st.spinner("🔎 Analizando los documentos..."):
            nodos = recuperar_nodos(msgs[-1]["content"], base_index, st.session_state.get("extra_index"))
            resp, modelo_usado, error = motor_ia.responder(msgs[-1]["content"], nodos, modelos_ordenados)
        if error is None:
            fuentes = [f'<b>{n.metadata.get("file_name","?")}</b> — página '
                       f'{n.metadata.get("page_label","?")} (relevancia {n.score:.2f})'
                       for n in resp.source_nodes]
            msgs.append({"role": "assistant", "content": resp.response, "fuentes": fuentes, "modelo": modelo_usado})
            st.rerun()
        elif error["tipo"] == "cuota":
            st.session_state.cuota_agotada = True
            msgs.pop()  # quitar la pregunta que no se pudo responder
            st.rerun()
        else:
            st.error(f"Ocurrió un error:\n\n{error['detalle'][:500]}")

# ==================================================================
#  BARRA DE ENTRADA UNIFICADA (adjuntar + texto + modelo)
# ==================================================================
barra = st.columns([0.6, 6.4, 2.4], vertical_alignment="center")
with barra[0]:
    with st.popover("📎", use_container_width=True):
        st.markdown("**Adjuntar un PDF**")
        st.caption("Arrastra un PDF aquí o haz clic. Podrás preguntar también sobre él.")
        subido = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
        if subido is not None:
            contenido = subido.getvalue()
            huella = hashlib.sha1(contenido).hexdigest()
            if huella in hashes_oficiales():
                # Ya está en la memoria oficial -> no reprocesar, usar la base directamente.
                st.session_state.extra_index = None
                st.info(f"📚 '{subido.name}' ya está en la base oficial. "
                        "Pregunta directamente (sin reprocesar).")
            else:
                # PDF nuevo -> se procesa (y queda en caché por si se vuelve a subir).
                with st.spinner(f"Procesando {subido.name}..."):
                    st.session_state.extra_index = indexar_pdf_cacheado(huella, subido.name, contenido)
                st.success(f"✅ '{subido.name}' añadido.") if st.session_state.get("extra_index") \
                    else st.warning("Sin texto extraíble.")
with barra[1]:
    prompt = st.chat_input("Escriba su consulta técnica sobre el Plan de Transmisión...",
                           disabled=st.session_state.cuota_agotada)
with barra[2]:
    st.session_state.modelo_sel = st.selectbox("Modelo", nombres_modelos, index=0, label_visibility="collapsed")

# ==================================================================
#  NUEVA PREGUNTA (chip o texto) -> se guarda y se responde en el siguiente ciclo
# ==================================================================
pregunta = prompt or click
if pregunta:
    if conv["titulo"] == "Nueva conversación":
        conv["titulo"] = pregunta
    msgs.append({"role": "user", "content": pregunta})
    st.rerun()
