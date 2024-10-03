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
homepage = st.Page("dashboard.py", title="Dashboard", icon=":material/home:")
ppc_meta = st.Page("ppc/meta.py", title="Meta Ads", icon=":material/rocket_launch:")
ppc_google_ads = st.Page("ppc/google_ads.py", title="Google Ads", icon=":material/rocket_launch:")
settings_page = st.Page("settings/impostazioni.py", title="Impostazioni", icon=":material/settings:")

pg = st.navigation({
    "Dashboard": [homepage],
    "Performance marketing": [ppc_meta, ppc_google_ads],
    "Impostazioni": [settings_page]
    })

pg.run()

# ------------------------------
#         SESSION STATE
# ------------------------------
if 'start_date' not in st.session_state:
    st.session_state['start_date'] = (datetime.now() - timedelta(days=14)).strftime('%d/%m/%Y')

if 'end_date' not in st.session_state:
    st.session_state['end_date'] = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')

if 'opp_radio' not in st.session_state:
    st.session_state['opp_radio'] = 'Creazione'

if 'lead_radio' not in st.session_state:
    st.session_state['lead_radio'] = 'Acquisizione'

# ------------------------------
#             STYLE
# ------------------------------
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