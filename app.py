import streamlit as st
from datetime import datetime, timedelta

# ------------------------------
#           SET PAGE
# ------------------------------
st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
#           MULTIPAGE
# ------------------------------
vendite = st.Page("mp_commerciale/vendite.py", title="Analisi vendite", icon=":material/euro:")
venditori = st.Page("mp_commerciale/venditori.py", title="Analisi venditori", icon=":material/person:")
ppc_meta = st.Page("mp_ppc/meta.py", title="Meta Ads", icon=":material/rocket_launch:")
ppc_google_ads = st.Page("mp_ppc/google_ads.py", title="Google Ads", icon=":material/rocket_launch:")
ppc_tiktok = st.Page("mp_ppc/tiktok.py", title="TikTok Ads", icon=":material/rocket_launch:")
google_analytics = st.Page("mp_traffico/google_analytics.py", title="Google Analytics", icon=":material/query_stats:")
settings_page = st.Page("mp_settings/impostazioni.py", title="Impostazioni", icon=":material/settings:")

pg = st.navigation({
    "Vendite": [vendite, venditori],
    "Marketing": [ppc_meta, ppc_google_ads, ppc_tiktok],
    "Traffico": [google_analytics],
    "Impostazioni": [settings_page]
    })

pg.run()

# ------------------------------
#         SESSION STATE
# ------------------------------
if 'start_date' not in st.session_state:
    st.session_state['start_date'] = datetime.now() - timedelta(days=14)

if 'end_date' not in st.session_state:
    st.session_state['end_date'] = datetime.now() - timedelta(days=1)

if 'opp_radio' not in st.session_state:
    st.session_state['opp_radio'] = 'Creazione'

if 'lead_radio' not in st.session_state:
    st.session_state['lead_radio'] = 'Acquisizione'

# ------------------------------
#             STYLE
# ------------------------------
st.markdown("""<style type='text/css'>
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
    </style>""", unsafe_allow_html=True)