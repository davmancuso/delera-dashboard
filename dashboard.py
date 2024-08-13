import streamlit as st
from datetime import datetime, timedelta
from urllib.request import urlopen
import json
import pandas as pd

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
st.sidebar.text("Cliente: Alpha Group stl\nProgetto: Delera\nWebsite: https://delera.io")
st.sidebar.subheader("Dati agenzia")
st.sidebar.text("Agenzia: Brain on strategy srl\nWebsite: https://brainonstrategy.com\nMail: info@brainonstrategy.com\nTelefono: +39 392 035 9839")

# ------------------------------
#          FUNCTIONS
# ------------------------------

# Globali
# ------------------------------
@st.cache_data
def currency(value):
    return "€ {:,.2f}".format(value)

@st.cache_data
def percentage(value):
    return "{:,.2f}%".format(value)

@st.cache_data
def thousand_0(value):
    return "{:,.0f}".format(value)

@st.cache_data
def thousand_2(value):
    return "{:,.2f}".format(value)

@st.cache_data(show_spinner=False)
def api_retrieving(start_date, end_date):
    url = st.secrets.source + "?api_key=" + st.secrets.api_key + "&date_from=" + str(start_date) + "&date_to=" + str(end_date) + "&fields=" + st.secrets.fields + "&_renderer=json"
    response = urlopen(url)
    data_json = json.loads(response.read())
    return pd.json_normalize(data_json, record_path=["data"])

# Meta
# ------------------------------
@st.cache_data
def meta_analysis(df):
    st.title("Analisi delle campagne Meta")
    st.warning("Formule errate, da verificare!")

    r1_c1, r1_c2 = st.columns(2)
    with r1_c1:
        st.metric("Spesa totale", currency(df["spend"].sum()))
    with r1_c2:
        st.metric("Campagne attive", df["campaign"].nunique())
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        st.metric("Impression", thousand_0(df["impressions"].sum()))
    with r2_c2:
        st.metric("Frequenza", thousand_2(df["frequency"].mean()))
    with r2_c3:
        st.metric("CPM", currency(df["impressions"].sum() / df["spend"].sum()))
    
    r3_c1, r3_c2, r3_c3 = st.columns(3)
    with r3_c1:
        st.metric("Click", thousand_0(df["clicks"].sum()))

# Database
# ------------------------------
@st.cache_data(show_spinner=False)
def stato_lead(_conn, start_date, end_date):
    query = f"""
                        SELECT
                            o.*,
                            ops.name AS stage
                        FROM
                            opportunities o
                        JOIN opportunity_pipeline_stages ops ON o.pipelineStageId=ops.id
                        WHERE
                            o.locationId='{st.secrets.id_cliente}'
                            AND ops.pipelineId='CawDqiWkLR5Ht98b4Xgd'
                            AND o.createdAt >= '{start_date}T00:00:00.000Z'
                            AND o.createdAt <= '{end_date}T23:59:59.999Z'
                        ORDER BY
                            o.createdAt;
                        """

    df = conn.query(query, show_spinner="Estraendo i dati dal database...", ttl=600)
    
    daQualificare = ['Nuova Opportunità',
                    'Prova Gratuita',
                    'Senza risposta',
                    'App Tel Fissato',
                    'Risposto/Da richiamare']
    qualificati = ['Autonomo - Call Onboarding',
                    'Call onboarding',
                    'Cancellati - Da riprogrammare',
                    'No Show - Ghost',
                    'Non Pronto (in target)',
                    'Seconda call / demo',
                    'Preventivo Mandato / Follow Up',
                    'Vinto Abbonamento Mensile',
                    'Vinto Abbonamento Annuale',
                    'Vinto mensile con acc.impresa',
                    'Vinto annuale con acc.impresa',
                    'Vinti generici',
                    'Ag.marketing/collaborazioni',
                    'Cliente Non vinto ']
    vinti = ['Vinto Abbonamento Mensile',
            'Vinto Abbonamento Annuale',
            'Vinto mensile con acc.impresa',
            'Vinto annuale con acc.impresa',
            'Vinti generici']

    st.title("Stato dei lead")

    lead_daQualificare = thousand_0(df[df['stage'].isin(daQualificare)].shape[0])
    st.metric("Lead da qualificare", lead_daQualificare)

    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        lead_qualificati= thousand_0(df[df['stage'].isin(qualificati)].shape[0])
        st.metric("Lead qualificati", lead_qualificati)
    with r2_c2:
        lead_qualificatiPerGiorno = thousand_2(df[df['stage'].isin(qualificati)].shape[0]/((end_date - start_date).days))
        st.metric("Lead qualificati al giorno", lead_qualificatiPerGiorno)
    with r2_c3:
        lead_tassoQualifica = percentage(df[df['stage'].isin(qualificati)].shape[0]/(len(df)-df[df['stage'].isin(daQualificare)].shape[0]))
        st.metric("Tasso di qualifica", lead_tassoQualifica)
    
    r3_c1, r3_c2, r3_c3 = st.columns(3)
    with r3_c1:
        lead_vinti= thousand_0(df[df['stage'].isin(vinti)].shape[0])
        st.metric("Lead qualificati", lead_vinti)
    with r3_c2:
        lead_vintiPerGiorno = thousand_2(df[df['stage'].isin(vinti)].shape[0]/((end_date - start_date).days))
        st.metric("Lead qualificati al giorno", lead_vintiPerGiorno)
    with r3_c3:
        lead_tassoVendita = percentage(df[df['stage'].isin(vinti)].shape[0]/df[df['stage'].isin(qualificati)].shape[0])
        st.metric("Tasso di qualifica", lead_tassoVendita)
    

# ------------------------------
#             BODY
# ------------------------------
st.title("Parametri della analisi")

st.subheader("Selezionare il periodo desiderato")
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Inizio", (datetime.today() - timedelta(days=29)), format="DD/MM/YYYY")
with col_date2:
    end_date = st.date_input("Fine", (datetime.today() - timedelta(days=1)), format="DD/MM/YYYY")

privacy = st.checkbox("Accetto il trattamento dei miei dati secondo le normative vigenti.", value=False)

if st.button("Scarica i dati") & privacy:
    df_raw = api_retrieving(start_date, end_date)

    # Meta
    # ------------------------------
    df_meta = df_raw.loc[(df_raw["source"] == "facebook") & (df_raw["account_name"] == "Business 2021") & (~df_raw["campaign"].str.contains(r"\[HR\]"))]
    meta_analysis(df_meta)

    # Google
    # ------------------------------
    df_google = df_raw.loc[(df_raw["source"] == "google") & (df_raw["account_name"] == "Delera")]

    # Database
    # ------------------------------
    conn = st.connection('mysql', type='sql')
    stato_lead(conn, start_date, end_date)