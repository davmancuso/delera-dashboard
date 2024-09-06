import streamlit as st
import locale
import mysql.connector
from datetime import datetime, timedelta
from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import STAGES, FIELDS
from data_analyzer import BaseAnalyzer, MetaAnalyzer, GadsAnalyzer, GanalyticsAnalyzer, OppAnalyzer
from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta
from data_retrieval import api_retrieve_data, opp_retrieving, lead_retrieving
from data_visualization import meta_analysis, gads_analysis, ganalytics_analysis, lead_analysis, performance_analysis, opp_analysis, economics_analysis

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
#          FUNCTIONS
# ------------------------------
def clear_all_cache():
    st.cache_data.clear()
    st.cache_resource.clear()

# ------------------------------
#             BODY
# ------------------------------
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')

st.title("Parametri della analisi")

col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Inizio", (datetime.today() - timedelta(days=14)), format="DD/MM/YYYY")
with col_date2:
    end_date = st.date_input("Fine", (datetime.today() - timedelta(days=1)), format="DD/MM/YYYY")

update_radio = st.radio(
    "Tipologia di aggiornamento delle opportunità",
    ["Creazione", "Lavorazione"],
    captions=[
        "Aggiorna i dati in base alla data di creazione dell'opportunità",
        "Aggiorna i dati in base alla data di cambio stage dell'opportunità"
    ],
)

privacy = st.checkbox("Accetto il trattamento dei miei dati secondo le normative vigenti.", value=False)

if st.button("Scarica i dati") & privacy:
    clear_all_cache()

    period = end_date - start_date + timedelta(days=1)

    comparison_start = start_date - period
    comparison_end = start_date -  timedelta(days=1)

    if update_radio == "Creazione":
        update_type = "createdAt"
    else:
        update_type = "lastStageChangeAt"
    
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
        globals()[df_name] = api_retrieve_data(source, fields, comparison_start, end_date)

    try:
        df_opp_raw = opp_retrieving(pool, update_type, comparison_start, end_date)
    except Exception as e:
        st.warning(f"Errore nel recupero dei dati da opportunità: {str(e)}")
        df_opp_raw = pd.DataFrame()

    # Data processing
    # ------------------------------
    meta_analyzer = MetaAnalyzer(start_date, end_date, comparison_start, comparison_end, st.secrets["meta_account"])
    meta_results, meta_results_comp = meta_analyzer.analyze(df_meta_raw)

    gads_analyzer = GadsAnalyzer(start_date, end_date, comparison_start, comparison_end, st.secrets["gads_account"])
    gads_results, gads_results_comp = gads_analyzer.analyze(df_gads_raw)
    
    ganalytics_analyzer = GanalyticsAnalyzer(start_date, end_date, comparison_start, comparison_end, st.secrets["ganalytics_account"])
    ganalytics_results, ganalytics_results_comp = ganalytics_analyzer.analyze(df_ganalytics_raw)

    opp_analyzer = OppAnalyzer(start_date, end_date, comparison_start, comparison_end, update_type)
    opp_results, opp_results_comp = opp_analyzer.analyze(df_opp_raw)

    # Data visualization
    # ------------------------------
    economics_analysis(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp)
    performance_analysis(opp_results, opp_results_comp)
    meta_analysis(meta_results, meta_results_comp)
    gads_analysis(gads_results, gads_results_comp)
    lead_analysis(opp_results, opp_results_comp)
    opp_analysis(opp_results, opp_results_comp)
    ganalytics_analysis(ganalytics_results, ganalytics_results_comp)

    # DA FARE: analisi dei flussi dei singoli funnel
    # DA FARE: aggiunta dell'attribuzione dei lead