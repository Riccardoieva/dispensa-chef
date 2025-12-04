import streamlit as st
import google.generativeai as genai
import json
import os
FILE_DATI= "dispensa.json"     #nome del file dove salvare i dati della dispensa       

# ---------------- CONFIGURAZIONE ----------------
# inserire la API key 
# 🔐 GESTIONE SICUREZZA API KEY
# L'app cercherà la chiave nel "nascondiglio" (st.secrets)
try:
    if "GEMINI_API_KEY" in st.secrets:     
        API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        # Se non la trova nei secrets, prova a cercarla nelle variabili d'ambiente (utile per il cloud)
        API_KEY = os.getenv("GEMINI_API_KEY")

    if not API_KEY:
        st.error("⛔ ERRORE: Chiave API non trovata!")
        st.stop()
except FileNotFoundError:
    st.error("⛔ Manca la cartella .streamlit o il file secrets.toml")
    st.stop()

# Configura l'IA
try:
    genai.configure(api_key=API_KEY) # attiva il collegamento con l'ai
except Exception as e:
    st.error(f"Errore Configurazione Chiave: {e}") # mostra errore a schermo

# ---------------- FUNZIONI ----------------
def salva_dati():                      #salva_dati(): Apre il quaderno (FILE_DATI) in modalità scrittura ("w") 
    with open(FILE_DATI, 'w') as f:    # e ci copia dentro (dump) tutto quello che c'è nella dispensa attuale.
        json.dump(st.session_state.dispensa, f)

def carica_dati():     #Apre il quaderno in lettura ("r") e carica i dati dentro la dispensa.
    try:
        with open(FILE_DATI, 'r') as f:
            return json.load(f)
    except FileNotFoundError:   #se il quaderno non esiste, crea una dispensa vuota.
        return []
@st.cache_data(show_spinner=False)
def is_cibo(parola):  #ho creaotro il "buttafuori", verifica che un ingrediente sia un vero alimento 
    try:    
        model = genai.GenerativeModel("models/gemini-2.5-pro")
        prompt = f"Dimmi se la seguente parola è un ingrediente alimentare o cibo: {parola}. Rispondi RIGOROSAMENTE solo con 'SI' o 'NO'."
        response = model.generate_content(prompt)
        text = response.text.strip().upper()
        return text == "SI" 
    except Exception:
      return False   

def aggiungi_ingrediente():
    nome = st.session_state.input_nome
    qta = st.session_state.input_qta
    if nome:
        with st.spinner("Verifica ingrediente..."):
            if not is_cibo(nome):
                st.error(f"⛔ '{nome}' non è un alimento!")
                st.session_state.input_nome = ""
                st.session_state.input_qta = ""
                return
        nome_pulito = nome.strip().lower()
        for item in st.session_state.dispensa:
            if item['nome'].strip().lower() == nome_pulito:
                st.warning(f"✋ {nome} è già presente!")
                return
        if len(st.session_state.dispensa) > 0:
            max_id = max([item['id'] for item in st.session_state.dispensa])
            nuovo_id = max_id + 1
        else:
            nuovo_id = 1
        st.session_state.dispensa.append({
            'id': nuovo_id, 'nome': nome, 'qta': qta, 'selezionato': True
        })
        salva_dati()
        st.session_state.input_nome = "" # pulisce i campi per quando inseriremo il prossimo ingrediente
        st.session_state.input_qta = ""               

def elimina_ingrediente(id_da_eliminare): # elimina l'igrediente e lascia in bacheca quelli con un id diverso 
    st.session_state.dispensa = [
        item for item in st.session_state.dispensa 
        if item['id'] != id_da_eliminare
    ]
    salva_dati()

# ---------------- MEMORIA ----------------
if 'dispensa' not in st.session_state: # st.session_state è una memoria che salva la lista della dispensa
    dati_salvati = carica_dati()
    if not dati_salvati: 
         st.session_state.dispensa = []
    else :
         st.session_state.dispensa = dati_salvati
 


# ---------------- INTERFACCIA GRAFICA----------------
st.title("🧑‍🍳 Dispensa AI Chef")

# SEZIONE INSERIMENTO
with st.container(border=True): # crea un riquadro per l'inserimento
    col1, col2, col3 = st.columns([3, 2, 2], vertical_alignment="bottom") # crea 3 colonne per l'inserimento con le dimensioni specificate
    with col1:
        st.text_input("Ingrediente", key="input_nome", placeholder="Es. Farina")
    with col2:
        st.text_input("Quantità", key="input_qta", placeholder="Es. 1kg")
    with col3:
        st.button("Aggiungi", on_click=aggiungi_ingrediente, use_container_width=True)

# LISTA
st.subheader("La tua dispensa")
search_query = st.text_input("🔍 Cerca nella dispensa", placeholder="Scrivi per filtrare...", label_visibility="collapsed")
if search_query:
    lista_filtrata = [item for item in st.session_state.dispensa 
                       if search_query.lower() in item['nome'].lower()
                       ]
else:
    lista_filtrata = st.session_state.dispensa                       
for item in lista_filtrata:
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