import streamlit as st
import mysql.connector
from datetime import datetime, timedelta
from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
st.sidebar.text("Cliente: Alpha Group stl\nProgetto: Delera\nWebsite: delera.io")
st.sidebar.subheader("Dati agenzia")
st.sidebar.text("Agenzia: Brain on strategy srl\nWebsite: brainonstrategy.com\nMail: info@brainonstrategy.com\nTelefono: +39 392 035 9839")

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
def opportunities(_conn, start_date, end_date):
    cursor = conn.cursor()
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

    cursor.execute(query)
    df_raw = cursor.fetchall()

    cursor.close()
    conn.close()

    df = pd.DataFrame(df_raw, columns=cursor.column_names)

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
    leadPersi = ['Numero Non corretto flusso di email marketing ',
                'Fuori target',
                'Lead Perso ( 10 tentativi non risp)']
    vinti = ['Vinto Abbonamento Mensile',
            'Vinto Abbonamento Annuale',
            'Vinto mensile con acc.impresa',
            'Vinto annuale con acc.impresa',
            'Vinti generici']
    persi = ['Non Pronto (in target)',
            'Cliente Non vinto ']
    venditeGestione = ['Autonomo - Call Onboarding',
                    'Call onboarding',
                    'Cancellati - Da riprogrammare',
                    'No Show - Ghost']
    venditeChiusura = ['Seconda call / demo',
                    'Preventivo Mandato / Follow Up']

    st.title("Stato dei lead")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <hr style="height:0px;border-width: 0px;;margin-top:5px;">
        """, unsafe_allow_html=True)

        lead_daQualificare = thousand_0(df[df['stage'].isin(daQualificare)].shape[0])
        st.metric("Lead da qualificare", lead_daQualificare)
        
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            lead_qualificati= thousand_0(df[df['stage'].isin(qualificati)].shape[0])
            st.metric("Lead qualificati", lead_qualificati)

            lead_vinti= thousand_0(df[df['stage'].isin(vinti)].shape[0])
            st.metric("Vendite", lead_vinti)
        with col1_2:
            lead_qualificatiPerGiorno = thousand_2(df[df['stage'].isin(qualificati)].shape[0]/((end_date - start_date).days))
            st.metric("Lead qualificati al giorno", lead_qualificatiPerGiorno)

            lead_vintiPerGiorno = thousand_2(df[df['stage'].isin(vinti)].shape[0]/((end_date - start_date).days))
            st.metric("Vendite al giorno", lead_vintiPerGiorno)
        with col1_3:
            lead_tassoQualifica = percentage(df[df['stage'].isin(qualificati)].shape[0]/(len(df)-df[df['stage'].isin(daQualificare)].shape[0]))
            st.metric("Tasso di qualifica", lead_tassoQualifica)

            lead_tassoVendita = percentage(df[df['stage'].isin(vinti)].shape[0]/df[df['stage'].isin(qualificati)].shape[0])
            st.metric("Tasso di vendita", lead_tassoVendita)
    with col2:
        df_qualificati = df[df['stage'].isin(qualificati)]

        date_range = pd.date_range(start=start_date, end=end_date)
        df_qualificati['date'] = pd.to_datetime(df_qualificati['createdAt']).dt.date
        date_counts = df_qualificati.groupby('date').size().reindex(date_range.date, fill_value=0)

        df_qualificati_graph = pd.DataFrame({'date': date_range.date, 'count': date_counts.values})
        fig_lq = px.line(df_qualificati_graph, x='date', y='count', title='Conteggio giornaliero dei lead qualificati', markers=True)
        fig_lq.update_layout(
            xaxis=dict(
                tickformat='%d/%m/%Y'
            ),
            xaxis_title="Data",
            yaxis_title="Numero di Lead Qualificati"
        )
        fig_lq.update_traces(line=dict(color='#b12b94'))
        st.plotly_chart(fig_lq)

    col3, col4, col5 = st.columns(3)
    with col3:
        fig_lqperday = go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(lead_qualificatiPerGiorno)/12*100,
            number={'suffix': "%"},
            title={'text': "Lead qualificati al giorno: 12"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#b12b94"},
                'steps': [
                    {'range': [0, 25], 'color': '#f0f2f6'},
                    {'range': [25, 50], 'color': '#f0f2f6'},
                    {'range': [50, 75], 'color': '#f0f2f6'},
                    {'range': [75, 100], 'color': '#f0f2f6'}
                ],
                'threshold': {
                    'line': {'color': "#1a1e1c", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        st.plotly_chart(fig_lqperday)
    with col4:
        fig_lqperday = go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(lead_vintiPerGiorno)/3*100,
            number={'suffix': "%"},
            title={'text': "Vendite al giorno: 3"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#b12b94"},
                'steps': [
                    {'range': [0, 25], 'color': '#f0f2f6'},
                    {'range': [25, 50], 'color': '#f0f2f6'},
                    {'range': [50, 75], 'color': '#f0f2f6'},
                    {'range': [75, 100], 'color': '#f0f2f6'}
                ],
                'threshold': {
                    'line': {'color': "#1a1e1c", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        st.plotly_chart(fig_lqperday)
    with col5:
        st.markdown("""
        <hr style="height:0px;border-width: 0px;;margin-top:35px;">
        """, unsafe_allow_html=True)

        st.subheader("Bleed out dei lead")

        opportunitàPerStage = df['stage'].value_counts()

        opportunitàPerse = leadPersi + persi
        filtered_counts = {stage: opportunitàPerStage.get(stage, 0) for stage in opportunitàPerse}
        opportunitàPerse_df = pd.DataFrame(list(filtered_counts.items()), columns=['Stage', 'Opportunità'])
        
        st.dataframe(opportunitàPerse_df.style.hide(axis='index'))
    
    st.title("Gestione delle opportunità")

    col6, col7 = st.columns(2)
    with col6:
        st.markdown("""
        <hr style="height:0px;border-width: 0px;;margin-top:5px;">
        """, unsafe_allow_html=True)

        opp_totale = thousand_0(len(df))
        st.metric("Opportunità", opp_totale)
        
        col6_1, col6_2, col6_3 = st.columns(3)
        with col6_1:
            opp_setting = thousand_0(df[df['stage'].isin(daQualificare)].shape[0])
            st.metric("Setting - Da gestire", opp_setting)

            opp_settingPersi = thousand_0(df[df['stage'].isin(leadPersi)].shape[0])
            st.metric("Setting - Persi", opp_settingPersi)
        with col6_2:
            opp_vendite = thousand_0(df[df['stage'].isin(venditeGestione)].shape[0])
            st.metric("Vendita - Da gestire", opp_vendite)

            opp_venditeChiusura = thousand_0(df[df['stage'].isin(venditeChiusura)].shape[0])
            st.metric("Vendita - Da chiudere", opp_venditeChiusura)
        with col6_3:
            opp_vinti = thousand_0(df[df['stage'].isin(vinti)].shape[0])
            st.metric("Vendita - Da gestire", opp_vinti)

            opp_persi = thousand_0(df[df['stage'].isin(persi)].shape[0])
            st.metric("Vendita - Da chiudere", opp_persi)
    with col7:
        df_opportunities = df
        date_range = pd.date_range(start=start_date, end=end_date)
        df_opportunities['date'] = pd.to_datetime(df_opportunities['createdAt']).dt.date
        date_counts = df_opportunities.groupby('date').size().reindex(date_range.date, fill_value=0)

        df_opportunities_graph = pd.DataFrame({'date': date_range.date, 'count': date_counts.values})
        fig_opp = px.line(df_opportunities_graph, x='date', y='count', title='Opportunità generate', markers=True)
        fig_opp.update_layout(
            xaxis=dict(
                tickformat='%d/%m/%Y'
            ),
            xaxis_title="Data",
            yaxis_title="Numero di opportunità"
        )
        fig_opp.update_traces(line=dict(color='#b12b94'))
        st.plotly_chart(fig_opp)

# ------------------------------
#             BODY
# ------------------------------
st.title("Parametri della analisi")

st.subheader("Selezionare il periodo desiderato")
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Inizio", (datetime.today() - timedelta(days=13)), format="DD/MM/YYYY")
with col_date2:
    end_date = st.date_input("Fine", (datetime.today() - timedelta(days=1)), format="DD/MM/YYYY")

privacy = st.checkbox("Accetto il trattamento dei miei dati secondo le normative vigenti.", value=False)

if st.button("Scarica i dati") & privacy:
    df_raw = api_retrieving(start_date, end_date)

    # Meta
    # ------------------------------
    df_meta = df_raw.loc[(df_raw["source"] == "facebook") & (df_raw["account_name"] == "Business 2021") & (~df_raw["campaign"].str.contains(r"\[HR\]"))]
    # meta_analysis(df_meta)

    # Google
    # ------------------------------
    df_google = df_raw.loc[(df_raw["source"] == "google") & (df_raw["account_name"] == "Delera")]

    # Database
    # ------------------------------
    conn = mysql.connector.connect(
        host=st.secrets["host"],
        port=st.secrets["port"],
        user=st.secrets["username"],
        password=st.secrets["password"],
        database=st.secrets["database"],
        auth_plugin='caching_sha2_password'
    )

    opportunities(conn, start_date, end_date)