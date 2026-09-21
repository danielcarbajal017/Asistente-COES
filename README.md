# ⚡ COES · Asistente del Plan de Transmisión

Asistente de IA (RAG) que responde preguntas sobre el **Plan de Transmisión 2027–2036**
del COES, **basándose únicamente en los documentos oficiales** e incluyendo las fuentes
(archivo y página) de cada respuesta.

## ¿Cómo funciona?

1. **Indexación** (`construir_indice.py`): lee todos los PDF de `data/`, los convierte en
   vectores y guarda la "memoria" en `vector_store/`.
2. **Consulta** (`app.py` / `preguntar.py`): busca en la memoria y un modelo de IA redacta
   la respuesta usando solo ese contexto.

- **Modelos (gratis, con respaldo automático):** Groq (Llama / GPT-OSS) y Google Gemini.
- **No inventa:** si el dato no está en los documentos, lo dice.

## Ejecutar en local

```bash
pip install -r requirements.txt
python construir_indice.py          # construye la memoria (una vez)
streamlit run app.py                # abre la app web
```

Necesitas las llaves en `groq_key.txt` y/o `google_key.txt` (o en variables de entorno
`GROQ_API_KEY` / `GOOGLE_API_KEY`).

## Publicar en internet (Streamlit Community Cloud, gratis)

1. Sube este repositorio a GitHub.
2. Entra a https://share.streamlit.io, inicia sesión con GitHub y elige este repo.
3. Archivo principal: `app.py`.
4. En **Settings → Secrets**, pega tus llaves (ver `.streamlit/secrets.toml.example`).

> ⚠️ Las llaves (`groq_key.txt`, `google_key.txt`) NO se suben al repositorio (ver `.gitignore`).
