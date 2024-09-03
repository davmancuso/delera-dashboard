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
from data_analyzer import BaseAnalyzer, MetaAnalyzer, GadsAnalyzer, GanalyticsAnalyzer, OppCreatedAnalyzer
from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta
from data_retrieval import api_retrieving, opp_created_retrieving, lead_retrieving
from data_visualization import meta_analysis, gads_analysis, ganalytics_analysis, lead_analysis, performance_analysis, opp_analysis

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

# Database
# ------------------------------
def economics(df_opp, df_opp_comp, df_opp_stage, df_opp_stage_comp, df_meta, df_meta_comp, df_gads, df_gads_comp):
    spesa_tot = df_meta["spend"].sum() + df_gads["spend"].sum()
    spesa_tot_comp = df_meta_comp["spend"].sum() + df_gads_comp["spend"].sum()
    spesa_tot_delta = (spesa_tot - spesa_tot_comp) / spesa_tot_comp * 100

    incasso = df_opp[df_opp['stage'].isin(STAGES['vinti'])]['monetaryValue'].sum()
    incasso_comp = df_opp_comp[df_opp_comp['stage'].isin(STAGES['vinti'])]['monetaryValue'].sum()
    
    incasso_stage = df_opp_stage[df_opp_stage['stage'].isin(STAGES['vinti'])]['monetaryValue'].sum()
    incasso_stage_comp = df_opp_stage_comp[df_opp_stage_comp['stage'].isin(STAGES['vinti'])]['monetaryValue'].sum()

    st.title("Performance economiche")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Per data di creazione")
        
        st.metric("Spesa pubblicitaria", currency(spesa_tot), percentage(spesa_tot_delta))
        
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            costo_per_lead = spesa_tot / len(df_opp) if len(df_opp) > 0 else 0
            costo_per_lead_comp = spesa_tot_comp / len(df_opp_comp) if len(df_opp_comp) > 0 else 0
            costo_per_lead_delta = get_metric_delta(costo_per_lead, costo_per_lead_comp)
            st.metric("Costo per lead", currency(costo_per_lead) if costo_per_lead != 0 else "-", costo_per_lead_delta)
        with col1_2:
            costo_per_lead_qual = spesa_tot / df_opp[df_opp['stage'].isin(STAGES['qualificati'])].shape[0] if df_opp[df_opp['stage'].isin(STAGES['qualificati'])].shape[0] > 0 else 0
            costo_per_lead_qual_comp = spesa_tot_comp / df_opp_comp[df_opp_comp['stage'].isin(STAGES['qualificati'])].shape[0] if df_opp_comp[df_opp_comp['stage'].isin(STAGES['qualificati'])].shape[0] > 0 else 0
            costo_per_lead_qual_delta = get_metric_delta(costo_per_lead_qual, costo_per_lead_qual_comp)
            st.metric("Costo per lead qualificato", currency(costo_per_lead_qual) if costo_per_lead_qual != 0 else "-", costo_per_lead_qual_delta)
        with col1_3:
            vendite_correnti = df_opp[df_opp['stage'].isin(STAGES['vinti'])].shape[0]
            vendite_precedenti = df_opp_comp[df_opp_comp['stage'].isin(STAGES['vinti'])].shape[0]

            costo_per_vendita = spesa_tot / vendite_correnti if vendite_correnti > 0 else 0
            costo_per_vendita_comp = spesa_tot_comp / vendite_precedenti if vendite_precedenti > 0 else 0
            costo_per_vendita_delta = get_metric_delta(costo_per_vendita, costo_per_vendita_comp)
            st.metric("Costo per vendita", currency(costo_per_vendita) if costo_per_vendita != 0 else "-", costo_per_vendita_delta)
        
        col1_4, col1_5 = st.columns(2)
        with col1_4:
            incasso_delta = get_metric_delta(incasso, incasso_comp)
            st.metric("Fatturato", currency(incasso), incasso_delta)
        with col1_5:
            roi = (incasso - spesa_tot) / spesa_tot * 100 if spesa_tot > 0 else 0
            roi_comp = (incasso_comp - spesa_tot_comp) / spesa_tot_comp * 100 if spesa_tot_comp > 0 else 0
            roi_delta = get_metric_delta(roi, roi_comp)
            st.metric("ROI", percentage(roi) if roi != 0 else "-", roi_delta)
    with col2:
        st.subheader("Per data di cambio stage")
        
        st.metric("Spesa pubblicitaria", currency(spesa_tot), percentage(spesa_tot_delta))
        
        col2_1, col2_2, col2_3 = st.columns(3)
        with col2_1:
            costo_per_lead_stage = spesa_tot / len(df_opp_stage) if len(df_opp_stage) > 0 else 0
            costo_per_lead_stage_comp = spesa_tot_comp / len(df_opp_stage_comp) if len(df_opp_stage_comp) > 0 else 0
            costo_per_lead_stage_delta = get_metric_delta(costo_per_lead_stage, costo_per_lead_stage_comp)
            st.metric("Costo per lead", currency(costo_per_lead_stage) if costo_per_lead_stage != 0 else "-", costo_per_lead_stage_delta)

        with col2_2:
            costo_per_lead_qual_stage = spesa_tot / df_opp_stage[df_opp_stage['stage'].isin(STAGES['qualificati'])].shape[0] if df_opp_stage[df_opp_stage['stage'].isin(STAGES['qualificati'])].shape[0] > 0 else 0
            costo_per_lead_qual_stage_comp = spesa_tot_comp / df_opp_stage_comp[df_opp_stage_comp['stage'].isin(STAGES['qualificati'])].shape[0] if df_opp_stage_comp[df_opp_stage_comp['stage'].isin(STAGES['qualificati'])].shape[0] > 0 else 0
            costo_per_lead_qual_stage_delta = get_metric_delta(costo_per_lead_qual_stage, costo_per_lead_qual_stage_comp)
            st.metric("Costo per lead qualificato", currency(costo_per_lead_qual_stage) if costo_per_lead_qual_stage != 0 else "-", costo_per_lead_qual_stage_delta)

        with col2_3:
            vendite_correnti_stage = df_opp_stage[df_opp_stage['stage'].isin(STAGES['vinti'])].shape[0]
            vendite_precedenti_stage = df_opp_stage_comp[df_opp_stage_comp['stage'].isin(STAGES['vinti'])].shape[0]

            costo_per_vendita_stage = spesa_tot / vendite_correnti_stage if vendite_correnti_stage > 0 else 0
            costo_per_vendita_stage_comp = spesa_tot_comp / vendite_precedenti_stage if vendite_precedenti_stage > 0 else 0
            costo_per_vendita_stage_delta = get_metric_delta(costo_per_vendita_stage, costo_per_vendita_stage_comp)
            st.metric("Costo per vendita", currency(costo_per_vendita_stage) if costo_per_vendita_stage != 0 else "-", costo_per_vendita_stage_delta)

        col2_4, col2_5 = st.columns(2)
        with col2_4:
            incasso_stage_delta = get_metric_delta(incasso_stage, incasso_stage_comp)
            st.metric("Fatturato", currency(incasso_stage), incasso_stage_delta)

        with col2_5:
            roi_stage = (incasso_stage - spesa_tot) / spesa_tot * 100 if spesa_tot > 0 else 0
            roi_stage_comp = (incasso_stage_comp - spesa_tot_comp) / spesa_tot_comp * 100 if spesa_tot_comp > 0 else 0
            roi_stage_delta = get_metric_delta(roi_stage, roi_stage_comp)
            st.metric("ROI", percentage(roi_stage) if roi_stage != 0 else "-", roi_stage_delta)

# ------------------------------
#             BODY
# ------------------------------
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')

st.title("Parametri della analisi")

st.subheader("Selezionare il periodo desiderato")
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Inizio", (datetime.today() - timedelta(days=14)), format="DD/MM/YYYY")
with col_date2:
    end_date = st.date_input("Fine", (datetime.today() - timedelta(days=1)), format="DD/MM/YYYY")

privacy = st.checkbox("Accetto il trattamento dei miei dati secondo le normative vigenti.", value=False)

if st.button("Scarica i dati") & privacy:
    clear_all_cache()

    period = end_date - start_date + timedelta(days=1)

    comparison_start = start_date - period
    comparison_end = start_date -  timedelta(days=1)

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
    df_meta_raw = api_retrieving('facebook', FIELDS['meta'], comparison_start, end_date)
    df_gads_raw = api_retrieving('google_ads', FIELDS['gads'], comparison_start, end_date)
    df_ganalytics_raw = api_retrieving('googleanalytics4', FIELDS['ganalytics'], comparison_start, end_date)
    df_opp_raw = opp_created_retrieving(pool, comparison_start, end_date)
    
    # df_lead_raw = lead_retrieving(pool, comparison_start, end_date)
    # df_lead_raw['custom_field_value'] = pd.to_datetime(df_lead_raw['custom_field_value'], format='%d/%m/%Y', errors='coerce')
    
    # Data processing
    # ------------------------------
    meta_analyzer = MetaAnalyzer(start_date, end_date, comparison_start, comparison_end, st.secrets["meta_account"])
    meta_results, meta_results_comp = meta_analyzer.analyze(df_meta_raw)

    gads_analyzer = GadsAnalyzer(start_date, end_date, comparison_start, comparison_end, st.secrets["gads_account"])
    gads_results, gads_results_comp = gads_analyzer.analyze(df_gads_raw)
    
    ganalytics_analyzer = GanalyticsAnalyzer(start_date, end_date, comparison_start, comparison_end, st.secrets["ganalytics_account"])
    ganalytics_results, ganalytics_results_comp = ganalytics_analyzer.analyze(df_ganalytics_raw)

    opp_created_analyzer = OppCreatedAnalyzer(start_date, end_date, comparison_start, comparison_end)
    opp_created_results, opp_created_results_comp = opp_created_analyzer.analyze(df_opp_raw)

    df_opp_stage = df_opp_raw.loc[
        (df_opp_raw["lastStageChangeAt"] >= start_date) &
        (df_opp_raw["lastStageChangeAt"] <= end_date)
    ]

    df_opp_stage_comp = df_opp_raw.loc[
        (df_opp_raw["lastStageChangeAt"] >= comparison_start) &
        (df_opp_raw["lastStageChangeAt"] <= comparison_end)
    ]

    # Data visualization
    # ------------------------------
    # economics(df_opp, df_opp_comp, df_opp_stage, df_opp_stage_comp, df_meta, df_meta_comp, df_gads, df_gads_comp)
    performance_analysis(opp_created_results, opp_created_results_comp)
    meta_analysis(meta_results, meta_results_comp)
    gads_analysis(gads_results, gads_results_comp)
    lead_analysis(opp_created_results, opp_created_results_comp)
    opp_analysis(opp_created_results, opp_created_results_comp)
    ganalytics_analysis(ganalytics_results, ganalytics_results_comp)

    # DA FARE: analisi dei flussi dei singoli funnel
    # DA FARE: aggiunta dell'attribuzione dei lead