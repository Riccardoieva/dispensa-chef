import streamlit as st
import google.generativeai as genai

# ---------------- CONFIGURAZIONE ----------------
# ⚠️ INCOLLA QUI LA TUA API KEY (Dentro le virgolette!)
API_KEY = "AIzaSyCZ0A-zF7dONFvNwc4B1Q41RprKxhbtGqo"

st.set_page_config(page_title="Dispensa AI Chef", page_icon="🧑‍🍳")

# Controllo di sicurezza per la Chiave
if not API_KEY:
    st.error("⛔ STOP! Hai dimenticato di inserire la tua Chiave API alla riga 6 del file app.py")
    st.stop() # Ferma tutto finché non la inserisci

# Configura l'IA
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Errore Configurazione Chiave: {e}")

# ---------------- MEMORIA ----------------
if 'dispensa' not in st.session_state:
    st.session_state.dispensa = [
        {'id': 1, 'nome': 'Pasta', 'qta': '500g', 'selezionato': True},
        {'id': 2, 'nome': 'Uova', 'qta': '4', 'selezionato': True}
    ]

# ---------------- FUNZIONI ----------------
def aggiungi_ingrediente():
    nome = st.session_state.input_nome
    qta = st.session_state.input_qta
    if nome:
        nuovo_id = len(st.session_state.dispensa) + 100
        st.session_state.dispensa.append({
            'id': nuovo_id, 'nome': nome, 'qta': qta, 'selezionato': True
        })
        st.session_state.input_nome = ""
        st.session_state.input_qta = ""

def elimina_ingrediente(id_da_eliminare):
    st.session_state.dispensa = [
        item for item in st.session_state.dispensa 
        if item['id'] != id_da_eliminare
    ]

# ---------------- INTERFACCIA ----------------
st.title("🧑‍🍳 Dispensa AI Chef")

# SEZIONE INSERIMENTO
with st.container(border=True):
    col1, col2, col3 = st.columns([3, 2, 2], vertical_alignment="bottom")
    with col1:
        st.text_input("Ingrediente", key="input_nome", placeholder="Es. Farina")
    with col2:
        st.text_input("Quantità", key="input_qta", placeholder="Es. 1kg")
    with col3:
        st.button("Aggiungi", on_click=aggiungi_ingrediente, use_container_width=True)

# LISTA
st.subheader("La tua dispensa")
for item in st.session_state.dispensa:
    c1, c2, c3, c4 = st.columns([1, 4, 3, 1])
    with c1:
        item['selezionato'] = st.checkbox("", value=item['selezionato'], key=f"chk_{item['id']}")
    with c2:
        st.write(f"**{item['nome']}**")
    with c3:
        item['qta'] = st.text_input("", value=item['qta'], key=f"qta_{item['id']}", label_visibility="collapsed")
    with c4:
        if st.button("X", key=f"del_{item['id']}"):
            elimina_ingrediente(item['id'])
            st.rerun()

# BOTTONE IA
st.divider()
if st.button("✨ Inventa Ricetta con IA", type="primary", use_container_width=True):
    selezionati = [f"{i['nome']} ({i['qta']})" for i in st.session_state.dispensa if i['selezionato']]
    
    if not selezionati:
        st.warning("Seleziona almeno un ingrediente!")
    else:
        with st.spinner(f"lo chef sta pensando...."):
            try:
                # Usiamo il modello scelto dalla tendina
                model = genai.GenerativeModel("models/gemini-2.5-pro")
                prompt = f"Sono un cuoco amatoriale. Ho in casa: {', '.join(selezionati)}. Inventa una ricetta."
                response = model.generate_content(prompt)
                st.session_state.ricetta = response.text
            except Exception as e:
                st.error(f"Errore IA: {e}")
                st.write("Suggerimento: Prova a cambiare modello dalla tendina a sinistra! Oppure controlla la chiave API.")

if 'ricetta' in st.session_state:
    st.markdown("---")
    st.success("Ecco la tua ricetta!")
    st.markdown(st.session_state.ricetta)