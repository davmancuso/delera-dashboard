import streamlit as st
from datetime import datetime, timedelta
from urllib.request import urlopen
import json
import pandas as pd

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
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.1);
        padding: 5% 5% 5% 10%;
        border-radius: 5px;
        color: rgb(30, 103, 119);
        overflow-wrap: break-word;
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

@st.cache_data
def currency(value):
    return "€ {:,.2f}".format(value)

@st.cache_data
def thousand_0(value):
    return "{:,.0f}".format(value)

@st.cache_data
def thousand_2(value):
    return "{:,.2f}".format(value)

@st.cache_data(show_spinner=False)
def api_retrieving(start_date, end_date):
    url = "https://connectors.windsor.ai/all?api_key=" + st.secrets.api_key + "&date_from=" + str(start_date) + "&date_to=" + str(end_date) + "&fields=" + st.secrets.fields + "&_renderer=json"
    response = urlopen(url)
    data_json = json.loads(response.read())
    return pd.json_normalize(data_json, record_path=["data"])

@st.cache_data
def meta_analysis(df):
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

@st.cache_data(show_spinner=False)
def stato_lead(_conn, start_date, end_date):
    q_daQualificare = f"""
                        SELECT
                            o.*,
                            ops.name AS stage
                        FROM
                            opportunities o
                        JOIN opportunity_pipeline_stages ops ON o.pipelineStageId=ops.id
                        WHERE
                            o.locationId='{st.secrets.id_cliente}'
                            AND ops.pipelineId='CawDqiWkLR5Ht98b4Xgd'
                            AND ops.`name` IN('Nuova Opportunità','Prova Gratuita','Senza risposta','App Tel Fissato','Risposto/Da richiamare')
                            AND o.createdAt >= '{start_date}T00:00:00.000Z'
                            AND o.createdAt <= '{end_date}T23:59:59.999Z'
                        ORDER BY
                            o.createdAt;
                        """
    df_daQualificare = conn.query(q_daQualificare, show_spinner="Estraendo i dati dal database...", ttl=600)
    st.metric("Lead da qualificare", thousand_0(len(df_daQualificare)))

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
    df_meta = df_raw.loc[(df_raw["source"] == "facebook") & (df_raw["account_name"] == "Business 2021") & (~df_raw["campaign"].str.contains("\[HR\]"))]
    df_google = df_raw.loc[(df_raw["source"] == "google") & (df_raw["account_name"] == "Delera")]
    
    # st.dataframe(df_meta.sort_values(by="date", ascending=False))
    meta_analysis(df_meta)

    conn = st.connection('mysql', type='sql')
    stato_lead(conn, start_date, end_date)