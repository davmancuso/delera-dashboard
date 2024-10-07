import streamlit as st
import numpy as np
import time
from datetime import datetime, timedelta

from data_analyzer import BaseAnalyzer, MetaAnalyzer, GadsAnalyzer, AttributionAnalyzer
from data_visualization import (
    meta_analysis, 
    gads_analysis
)

# ------------------------------
#             SIDEBAR
# ------------------------------
st.sidebar.write("Dashboard realizzata da Brain on strategy")

# ------------------------------
#             BODY
# ------------------------------
st.title("Dashboard")

st.subheader("Performance Google Ads")

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
period = end_date - start_date + timedelta(days=1)
comparison_start = start_date - period
comparison_end = start_date -  timedelta(days=1)

if opp_radio == "Creazione":
    update_type_opp = "createdAt"
else:
    update_type_opp = "lastStageChangeAt"

if lead_radio == "Acquisizione":
    update_type_attribution = "data_acquisizione"
else:
    update_type_attribution = update_type_opp

# Session state update
# ------------------------------
st.session_state['start_date'] = start_date
st.session_state['end_date'] = end_date
st.session_state['opp_radio'] = opp_radio
st.session_state['lead_radio'] = lead_radio

# Data processing
# ------------------------------
try:
    gads_analyzer = GadsAnalyzer(start_date, end_date, comparison_start, comparison_end)
    gads_results, gads_results_comp = gads_analyzer.analyze()
except Exception as e:
    st.warning(f"Errore nell'elaborazione dei dati di Google Ads: {str(e)}")
    gads_results, gads_results_comp = {}, {}

try:
    attribution_analyzer = AttributionAnalyzer(start_date, end_date, comparison_start, comparison_end, update_type_attribution)
    attribution_results, attribution_results_comp = attribution_analyzer.analyze()
except Exception as e:
    st.warning(f"Errore nell'elaborazione dei dati da attribuzione: {str(e)}")
    attribution_results, attribution_results_comp = {}, {}

# Data visualization
# ------------------------------
gads_analysis(gads_results, gads_results_comp, attribution_results, attribution_results_comp)