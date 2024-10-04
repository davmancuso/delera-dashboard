import streamlit as st
from datetime import datetime, timedelta
import mysql.connector

from config import STAGES, FIELDS
from db import initialize_database
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

col1, col2, col3 = st.columns([1,1,6])
with col1:
    database_inizialize = st.button("Inizializza database")
with col2:
    database_update = st.button("Aggiorna database")
with col3:
    pass

# Funzioni dei bottoni
# ------------------------------
if database_inizialize:
    try:
        initialize_database()
        st.success("Database inizializzato correttamente")
    except Exception as e:
        st.error(f"Errore durante l'inizializzazione del database: {str(e)}")

if database_update:
    # Session state update
    # ------------------------------
    st.session_state['start_date'] = start_date
    st.session_state['end_date'] = end_date
    st.session_state['opp_radio'] = opp_radio
    st.session_state['lead_radio'] = lead_radio

    # Database connection
    # ------------------------------
    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        host=st.secrets["host"],
        port=st.secrets["port"],
        user=st.secrets["username"],
        password=st.secrets["password"],
        database=st.secrets["database"],
        auth_plugin='caching_sha2_password')

    # Data retrival
    # ------------------------------
    data_sources = [
        ('facebook', FIELDS['meta'], 'df_meta_raw'),
        ('google_ads', FIELDS['gads'], 'df_gads_raw'),
        ('googleanalytics4', FIELDS['ganalytics'], 'df_ganalytics_raw'),
    ]

    for source, fields, df_name in data_sources:
        api_retrieve_data(source, fields, comparison_start, end_date)

    try:
        opp_retrieving(pool, update_type_opp, comparison_start, end_date)
    except Exception as e:
        st.warning(f"Errore nel recupero dei dati da opportunità: {str(e)}")
    
    try:
        attribution_retrieving(pool, update_type_attribution, comparison_start, end_date)
    except Exception as e:
        st.warning(f"Errore nel recupero dei dati da lead: {str(e)}")
    
    try:
        transaction_retrieving(pool, start_date, end_date)
    except Exception as e:
        st.warning(f"Errore nel recupero dei dati da transazioni: {str(e)}")