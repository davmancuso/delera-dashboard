import streamlit as st
import locale
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd

from config import STAGES, FIELDS
from db import initialize_database
from data_analyzer import BaseAnalyzer, MetaAnalyzer, GadsAnalyzer, GanalyticsAnalyzer, OppAnalyzer, AttributionAnalyzer, OrderAnalyzer
from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta
from data_retrieval import api_retrieve_data, opp_retrieving, attribution_retrieving, order_retrieving
from data_visualization import (
    meta_analysis, 
    gads_analysis, 
    ganalytics_analysis, 
    lead_analysis, 
    performance_analysis, 
    opp_analysis, 
    economics_analysis, 
    attribution_analysis
)

# ------------------------------
#             STYLE
# ------------------------------
st.set_page_config(
    page_title="Delera - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style type='text/css'>

    /* Remove sidebar X button */
    [data-testid="stSidebar"] div div button {
        display: none;
    }

    /* Remove footer */
    footer {
        display: none !important;
    }    
    
    /* Metric boxes */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #b12b94;
        border-radius: 5px;
        padding: 20px;
        overflow-wrap: break-word;
        margin: auto;
    }

    [data-testid="stMetric"] > div {
        width: fit-content;
        margin: auto;
    }

    [data-testid="stMetric"] label {
        width: fit-content;
        margin: auto;
    }

    </style>
""", unsafe_allow_html=True)

# ------------------------------
#             SIDEBAR
# ------------------------------
st.sidebar.title("Analisi dei dati")
st.sidebar.subheader("Dati cliente")
st.sidebar.text("Cliente: Alpha Future Group srl\nProgetto: Delera\nWebsite: delera.io")
st.sidebar.subheader("Dati agenzia")
st.sidebar.text("Agenzia: Brain on strategy srl\nWebsite: brainonstrategy.com\nMail: info@brainonstrategy.com\nTelefono: +39 392 035 9839")

# ------------------------------
#             BODY
# ------------------------------
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')

st.title("Parametri della analisi")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Inizio", datetime.now() - timedelta(days=14), format="DD/MM/YYYY"
    )
with col2:
    end_date = st.date_input(
        "Fine", datetime.now() - timedelta(days=1), format="DD/MM/YYYY"
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
    )
with col4:
    lead_radio = st.radio(
        "Tipologia di aggiornamento dei lead",
        ["Acquisizione", "Opportunità"],
        captions=[
            "Aggiorna i dati in base alla data di acquisizione del lead",
            "Aggiorna i dati in base alla data di lavorazione dell'opportunità correlata"
        ],
    )

col5, col6, col7, col8 = st.columns([1, 1, 1, 5])
with col5:
    database_inizialize = st.button("Inizializza database")
with col6:
    database_update = st.button("Aggiorna database")
with col7:
    dashboard = st.button("Mostra dashboard")
with col8:
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

# Funzioni dei bottoni
# ------------------------------
if database_inizialize:
    try:
        initialize_database()
        st.success("Database inizializzato correttamente")
    except Exception as e:
        st.error(f"Errore durante l'inizializzazione del database: {str(e)}")

if database_update:
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
        order_retrieving(pool, start_date, end_date)
    except Exception as e:
        st.warning(f"Errore nel recupero dei dati da ordini: {str(e)}")

if dashboard:
    # Data processing
    # ------------------------------
    try:
        meta_analyzer = MetaAnalyzer(start_date, end_date, comparison_start, comparison_end)
        meta_results, meta_results_comp = meta_analyzer.analyze()
    except Exception as e:
        st.warning(f"Errore nell'elaborazione dei dati di Meta: {str(e)}")
        meta_results, meta_results_comp = {}, {}

    try:
        gads_analyzer = GadsAnalyzer(start_date, end_date, comparison_start, comparison_end)
        gads_results, gads_results_comp = gads_analyzer.analyze()
    except Exception as e:
        st.warning(f"Errore nell'elaborazione dei dati di Google Ads: {str(e)}")
        gads_results, gads_results_comp = {}, {}

    try:
        ganalytics_analyzer = GanalyticsAnalyzer(start_date, end_date, comparison_start, comparison_end)
        ganalytics_results, ganalytics_results_comp = ganalytics_analyzer.analyze()
    except Exception as e:
        st.warning(f"Errore nell'elaborazione dei dati di Google Analytics: {str(e)}")
        ganalytics_results, ganalytics_results_comp = {}, {}

    try:
        opp_analyzer = OppAnalyzer(start_date, end_date, comparison_start, comparison_end, update_type_opp)
        opp_results, opp_results_comp = opp_analyzer.analyze()
    except Exception as e:
        st.warning(f"Errore nell'elaborazione dei dati da opportunità: {str(e)}")
        opp_results, opp_results_comp = {}, {}
    
    try:
        attribution_analyzer = AttributionAnalyzer(start_date, end_date, comparison_start, comparison_end, update_type_attribution)
        attribution_results, attribution_results_comp = attribution_analyzer.analyze()
    except Exception as e:
        st.warning(f"Errore nell'elaborazione dei dati da attribuzione: {str(e)}")
        attribution_results, attribution_results_comp = {}, {}

    try:
        order_analyzer = OrderAnalyzer(start_date, end_date, comparison_start, comparison_end)
        order_results, order_results_comp = order_analyzer.analyze()
    except Exception as e:
        st.warning(f"Errore nell'elaborazione dei dati da ordini: {str(e)}")
        order_results, order_results_comp = {}, {}

    # Data visualization
    # ------------------------------
    economics_analysis(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp)
    performance_analysis(opp_results, opp_results_comp)
    meta_analysis(meta_results, meta_results_comp, attribution_results, attribution_results_comp)
    gads_analysis(gads_results, gads_results_comp, attribution_results, attribution_results_comp)
    lead_analysis(opp_results, opp_results_comp)
    opp_analysis(opp_results, opp_results_comp)
    attribution_analysis(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp, attribution_results, attribution_results_comp)
    ganalytics_analysis(ganalytics_results, ganalytics_results_comp)

    # DA FARE: analisi dei flussi dei singoli funnel