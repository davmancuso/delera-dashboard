import streamlit as st
import environ
from datetime import datetime, timedelta
import sqlite3
import mysql.connector

from config import STAGES, FIELDS
from db import initialize_database, delete_table, show_table_data, add_column, delete_column, delete_table_data
from data_retrieval import api_retrieve_data, opp_retrieving, attribution_retrieving, transaction_retrieving

# ------------------------------
#             SIDEBAR
# ------------------------------
st.sidebar.write("Dashboard realizzata da Brain on strategy")

# ------------------------------
#             BODY
# ------------------------------
st.title("Dashboard")

st.subheader("Gestione del database")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Inizio",
        st.session_state.get('start_date', datetime.now() - timedelta(days=14)),
        format="DD/MM/YYYY"
    )
with col2:
    end_date = st.date_input(
        "Fine",
        st.session_state.get('end_date', datetime.now() - timedelta(days=1)),
        format="DD/MM/YYYY"
    )

col3, col4 = st.columns(2)
with col3:
    opp_radio = st.radio(
        "Tipologia di aggiornamento delle opportunità",
        ["Creazione", "Lavorazione"],
        captions=[
            "Aggiorna i dati in base alla data di creazione dell'opportunità",
            "Aggiorna i dati in base alla data di cambio stage dell'opportunità"
        ],
        index=["Creazione", "Lavorazione"].index(st.session_state.get('opp_radio', 'Creazione'))
    )
with col4:
    lead_radio = st.radio(
        "Tipologia di aggiornamento dei lead",
        ["Acquisizione", "Opportunità"],
        captions=[
            "Aggiorna i dati in base alla data di acquisizione del lead",
            "Aggiorna i dati in base alla data di lavorazione dell'opportunità correlata"
        ],
        index=["Acquisizione", "Opportunità"].index(st.session_state.get('lead_radio', 'Acquisizione'))
    )

col1, col2, col3, col4 = st.columns([2,2,2,2])
with col1:
    database_inizialize = st.button("Inizializza il database", use_container_width=True)
with col2:
    database_update = st.button("Aggiorna tutte le tabelle", use_container_width=True)
with col3:
    database_delete = st.button("Elimina tutte le tabelle", use_container_width=True)
with col4:
    pass

st.subheader("Gestione delle tabelle singole")

conn = sqlite3.connect('local_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabelle = [row[0] for row in cursor.fetchall()]
conn.close()

col5, col6 = st.columns([1,1])
with col5:
    tabella_selezionata = st.selectbox("Seleziona una tabella", tabelle if tabelle else ['Database vuoto'], disabled=(not tabelle))
with col6:
    pass

col7, col8, col9, col10 = st.columns([1,1,1,1])
with col7:
    aggiorna_tabella = st.button("Aggiorna la tabella", use_container_width=True)
with col8:
    mostra_tabella = st.button("Visualizza i dati della tabella", use_container_width=True)
with col9:
    elimina_dati_tabella = st.button("Elimina i dati della tabella", use_container_width=True)
with col10:
    elimina_tabella = st.button("Elimina la tabella", use_container_width=True)

col11, col12 = st.columns([1,1])
with col11:
    column_name = st.text_input("Nome della colonna", value="")
with col12:
    column_type = st.text_input("Tipo della colonna", value="TEXT")

col13, col14, col15 = st.columns([1,1,2])
with col13:
    add_column_button = st.button("Aggiungi la colonna", use_container_width=True)
with col14:
    delete_column_button = st.button("Elimina la colonna", use_container_width=True)
with col15:
    pass

# Variabili d'ambiente
# ------------------------------
if opp_radio == "Creazione":
    update_type_opp = "createdAt"
else:
    update_type_opp = "lastStageChangeAt"

if lead_radio == "Acquisizione":
    update_type_attribution = "data_acquisizione"
else:
    update_type_attribution = update_type_opp

period = end_date - start_date + timedelta(days=1)
comparison_start = start_date - period
comparison_end = start_date -  timedelta(days=1)

# Session state update
# ------------------------------
st.session_state['start_date'] = start_date
st.session_state['end_date'] = end_date
st.session_state['opp_radio'] = opp_radio
st.session_state['lead_radio'] = lead_radio

# Database connection
# ------------------------------
env = environ.Env()
environ.Env.read_env()

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=env('host'),
    port=env('port'),
    user=env('username'),
    password=env('password'),
    database=env('database'),
    auth_plugin='caching_sha2_password')

# Data sources
# ------------------------------
data_sources = [
    ('facebook', FIELDS['facebook']),
    ('google_ads', FIELDS['google_ads']),
    ('tiktok', FIELDS['tiktok']),
    ('googleanalytics4', FIELDS['googleanalytics4']),
]

# Funzioni dei bottoni
# ------------------------------
if database_inizialize:
    try:
        initialize_database()
        st.success("Database inizializzato correttamente")
    except Exception as e:
        st.error(f"Errore durante l'inizializzazione del database: {str(e)}")

if database_update:
    if tabelle:
        for source, fields in data_sources:
            api_retrieve_data(source, fields, comparison_start, end_date)
        
        opp_retrieving(pool, update_type_opp, comparison_start, end_date)
        attribution_retrieving(pool, update_type_attribution, comparison_start, end_date)
        transaction_retrieving(pool, comparison_start, end_date)
    else:
        st.error("Inizializza il database per poter utilizzare questa funzione")

if database_delete:
    for table in tabelle:
        try:
            delete_table(table)
            st.success(f"Tabella {table} eliminata correttamente")
        except Exception as e:
            st.error(f"Errore durante l'eliminazione della tabella: {str(e)}")

if aggiorna_tabella:
    retrieval_mapping = {
        "opp_data": lambda: opp_retrieving(pool, update_type_opp, comparison_start, end_date),
        "attribution_data": lambda: attribution_retrieving(pool, update_type_attribution, comparison_start, end_date),
        "transaction_data": lambda: transaction_retrieving(pool, comparison_start, end_date)
    }

    if tabella_selezionata == "Database vuoto":
        st.error("Inizializza il database per poter utilizzare questa funzione")
    elif tabella_selezionata in retrieval_mapping:
        try:
            retrieval_mapping[tabella_selezionata]()
        except Exception as e:
            st.error(f"Errore durante l'aggiornamento della tabella: {str(e)}")
    else:
        source = tabella_selezionata.removesuffix("_data")
        fields = FIELDS[source]

        try:
            api_retrieve_data(source, fields, comparison_start, end_date)
        except Exception as e:
            st.error(f"Errore durante l'aggiornamento della tabella: {str(e)}")

if mostra_tabella:
    if tabella_selezionata == "Database vuoto":
        st.error("Inizializza il database per poter utilizzare questa funzione")
    else:
        if tabella_selezionata in ['opp_data', 'attribution_data', 'transaction_data']:
            show_table_data(tabella_selezionata, start_date, end_date, update_type_opp)
        else:
            show_table_data(tabella_selezionata, start_date, end_date)

if elimina_dati_tabella:
    if tabella_selezionata == "Database vuoto":
        st.error("Inizializza il database per poter utilizzare questa funzione")
    else:
        delete_table_data(tabella_selezionata)

if elimina_tabella:
    if tabella_selezionata == "Database vuoto":
        st.error("Inizializza il database per poter utilizzare questa funzione")
    else:
        delete_table(tabella_selezionata)

if add_column_button:
    if column_name:
        add_column(tabella_selezionata, column_name, column_type)
    else:
        st.error("Inserisci il nome della colonna da aggiungere")

if delete_column_button:
    if column_name:
        delete_column(tabella_selezionata, column_name)
    else:
        st.error("Inserisci il nome della colonna da eliminare")