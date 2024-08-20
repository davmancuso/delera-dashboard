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
st.sidebar.text("Cliente: Alpha Future Group srl\nProgetto: Delera\nWebsite: delera.io")
st.sidebar.subheader("Dati agenzia")
st.sidebar.text("Agenzia: Brain on strategy srl\nWebsite: brainonstrategy.com\nMail: info@brainonstrategy.com\nTelefono: +39 392 035 9839")

# ------------------------------
#          FUNCTIONS
# ------------------------------

# Globali
# ------------------------------
def currency(value):
    return "€ {:,.2f}".format(value)

def percentage(value):
    return "{:,.2f}%".format(value)

def thousand_0(value):
    return "{:,.0f}".format(value)

def thousand_2(value):
    return "{:,.2f}".format(value)

# Data retrieving
# ------------------------------
def api_retrieving(start_date, end_date):
    url = st.secrets.source + "?api_key=" + st.secrets.api_key + "&date_from=" + str(start_date) + "&date_to=" + str(end_date) + "&fields=" + st.secrets.fields + "&_renderer=json"
    response = urlopen(url)
    data_json = json.loads(response.read())
    return pd.json_normalize(data_json, record_path=["data"])

def opp_retrieving(pool, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    query = f"""
                SELECT
                    o.createdAt,
                    ops.name AS stage
                FROM
                    opportunities o
                JOIN opportunity_pipeline_stages ops ON o.pipelineStageId=ops.id
                WHERE
                    o.locationId='{st.secrets.id_cliente}'
                    AND ops.pipelineId='{st.secrets.pipeline_vendita}'
                    AND o.createdAt >= '{start_date}T00:00:00.000Z'
                    AND o.createdAt <= '{end_date}T23:59:59.999Z'
                ORDER BY
                    o.createdAt;
            """

    cursor.execute(query)

    df_raw = cursor.fetchall()

    cursor.close()
    conn.close()

    return pd.DataFrame(df_raw, columns=cursor.column_names)

# Meta
# ------------------------------
def meta_analysis(df, df_comp):
    st.title("Analisi delle campagne Meta")

    col1, col2 = st.columns(2)
    with col1:
        spesaTot_delta = (df["spend"].sum() - df_comp["spend"].sum()) / df_comp["spend"].sum() * 100
        st.metric("Spesa totale", currency(df["spend"].sum()), percentage(spesaTot_delta))

        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            campagne_delta = (df["campaign"].nunique() - df_comp["campaign"].nunique()) / df_comp["campaign"].nunique() * 100
            st.metric("Campagne attive", df["campaign"].nunique(), percentage(campagne_delta))

            cpm_delta = ((df["spend"].sum() / df["impressions"].sum() * 1000) - (df_comp["spend"].sum() / df_comp["impressions"].sum() * 1000)) / (df_comp["spend"].sum() / df_comp["impressions"].sum() * 1000) * 100
            st.metric("CPM", currency(df["spend"].sum() / df["impressions"].sum() * 1000), percentage(cpm_delta), delta_color="inverse")
        with col1_2:
            impression_delta = (df["impressions"].sum() - df_comp["impressions"].sum()) / df_comp["impressions"].sum() * 100
            st.metric("Impression", thousand_0(df["impressions"].sum()), percentage(impression_delta))

            ctr_delta = (((df["outbound_clicks_outbound_click"].sum() / df["impressions"].sum()) * 100) - ((df_comp["outbound_clicks_outbound_click"].sum() / df_comp["impressions"].sum()) * 100)) / ((df_comp["outbound_clicks_outbound_click"].sum() / df_comp["impressions"].sum()) * 100) * 100
            st.metric("CTR", percentage((df["outbound_clicks_outbound_click"].sum() / df["impressions"].sum()) * 100), percentage(ctr_delta))
        with col1_3:
            click_delta = (df["outbound_clicks_outbound_click"].sum() - df_comp["outbound_clicks_outbound_click"].sum()) / df_comp["outbound_clicks_outbound_click"].sum() * 100
            st.metric("Click", thousand_0(df["outbound_clicks_outbound_click"].sum()), percentage(click_delta))

            cpc_delta = (df["outbound_clicks_outbound_click"].sum() / df["spend"].sum() - df_comp["outbound_clicks_outbound_click"].sum() / df_comp["spend"].sum()) / (df_comp["outbound_clicks_outbound_click"].sum() / df_comp["spend"].sum()) * 100
            st.metric("CPC", currency(df["outbound_clicks_outbound_click"].sum() / df["spend"].sum()), percentage(cpc_delta), delta_color="inverse")
    with col2:
        df.loc[:, 'date'] = pd.to_datetime(df['date']).dt.date
        daily_spend_current = df.groupby('date')['spend'].sum().reset_index()

        df_comp.loc[:, 'date'] = pd.to_datetime(df_comp['date']).dt.date
        daily_spend_comp = df_comp.groupby('date')['spend'].sum().reset_index()

        daily_spend_current['day'] = (daily_spend_current['date'] - daily_spend_current['date'].min()).apply(lambda x: x.days)
        daily_spend_comp['day'] = (daily_spend_comp['date'] - daily_spend_comp['date'].min()).apply(lambda x: x.days)

        daily_spend_current['period'] = 'Periodo Corrente'
        daily_spend_comp['period'] = 'Periodo Precedente'

        combined_spend = pd.concat([daily_spend_comp, daily_spend_current])

        color_map = {
            'Periodo Corrente': '#b12b94',
            'Periodo Precedente': '#eb94d8'
        }

        hover_data = {
            'period': True,
            'date': '|%d/%m/%Y',
            'spend': ':.2f',
            'day': False
        }

        fig_spend = px.line(combined_spend, x='day', y='spend', color='period',
                    title='Spesa giornaliera',
                    markers=True,
                    labels={'day': 'Giorno relativo al periodo', 'spend': 'Spesa (€)', 'period': 'Periodo', 'date': 'Data'},
                    color_discrete_map=color_map,
                    hover_data=hover_data)

        fig_spend.update_traces(mode='lines+markers')
        fig_spend.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
        fig_spend.update_traces(
            hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Spesa (€): %{y:.2f}<extra></extra>'
        )
        fig_spend.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.4,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig_spend)
    
    st.title("Dettaglio delle campagne")

    dettaglioCampagne = df.groupby('campaign').agg({
        'spend': 'sum',
        'impressions': 'sum',
        'outbound_clicks_outbound_click': 'sum'
    }).reset_index()

    dettaglioCampagne.rename(columns={
        'campaign': 'Campagna',
        'spend': 'Spesa',
        'impressions': 'Impression',
        'outbound_clicks_outbound_click': 'Click'
    }, inplace=True)

    dettaglioCampagne['CTR'] = dettaglioCampagne['Click'] / dettaglioCampagne['Impression']
    dettaglioCampagne['CPC'] = dettaglioCampagne['Spesa'] / dettaglioCampagne['Click']

    dettaglioCampagne['Spesa'] = dettaglioCampagne['Spesa'].map('€ {:,.2f}'.format)
    dettaglioCampagne['CTR'] = dettaglioCampagne['CTR'].map('{:.2%}'.format)
    dettaglioCampagne['CPC'] = dettaglioCampagne['CPC'].map('€ {:,.2f}'.format)

    st.dataframe(dettaglioCampagne)

# Google
# ------------------------------
def google_analysis(df, df_comp):
    st.title("Analisi delle campagne Google")

    col1, col2 = st.columns(2)
    with col1:
        spesaTot_delta = (df["spend"].sum() - df_comp["spend"].sum()) / df_comp["spend"].sum() * 100
        st.metric("Spesa totale", currency(df["spend"].sum()), percentage(spesaTot_delta))

        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            campagne_delta = (df["campaign"].nunique() - df_comp["campaign"].nunique()) / df_comp["campaign"].nunique() * 100
            st.metric("Campagne attive", df["campaign"].nunique(), percentage(campagne_delta))

            cpm_delta = ((df["spend"].sum() / df["impressions"].sum() * 1000) - (df_comp["spend"].sum() / df_comp["impressions"].sum() * 1000)) / (df_comp["spend"].sum() / df_comp["impressions"].sum() * 1000) * 100
            st.metric("CPM", currency(df["spend"].sum() / df["impressions"].sum() * 1000), percentage(cpm_delta), delta_color="inverse")
        with col1_2:
            impression_delta = (df["impressions"].sum() - df_comp["impressions"].sum()) / df_comp["impressions"].sum() * 100
            st.metric("Impression", thousand_0(df["impressions"].sum()), percentage(impression_delta))

            ctr_delta = (((df["clicks"].sum() / df["impressions"].sum()) * 100) - ((df_comp["clicks"].sum() / df_comp["impressions"].sum()) * 100)) / ((df_comp["clicks"].sum() / df_comp["impressions"].sum()) * 100) * 100
            st.metric("CTR", percentage((df["clicks"].sum() / df["impressions"].sum()) * 100), percentage(ctr_delta))
        with col1_3:
            click_delta = (df["clicks"].sum() - df_comp["clicks"].sum()) / df_comp["clicks"].sum() * 100
            st.metric("Click", thousand_0(df["clicks"].sum()), percentage(click_delta))

            cpc_delta = (df["clicks"].sum() / df["spend"].sum() - df_comp["clicks"].sum() / df_comp["spend"].sum()) / (df_comp["clicks"].sum() / df_comp["spend"].sum()) * 100
            st.metric("CPC", currency(df["clicks"].sum() / df["spend"].sum()), percentage(cpc_delta), delta_color="inverse")
    with col2:
        df.loc[:, 'date'] = pd.to_datetime(df['date']).dt.date
        daily_spend_current = df.groupby('date')['spend'].sum().reset_index()

        df_comp.loc[:, 'date'] = pd.to_datetime(df_comp['date']).dt.date
        daily_spend_comp = df_comp.groupby('date')['spend'].sum().reset_index()

        daily_spend_current['day'] = (daily_spend_current['date'] - daily_spend_current['date'].min()).apply(lambda x: x.days)
        daily_spend_comp['day'] = (daily_spend_comp['date'] - daily_spend_comp['date'].min()).apply(lambda x: x.days)

        daily_spend_current['period'] = 'Periodo Corrente'
        daily_spend_comp['period'] = 'Periodo Precedente'

        combined_spend = pd.concat([daily_spend_comp, daily_spend_current])

        color_map = {
            'Periodo Corrente': '#b12b94',
            'Periodo Precedente': '#eb94d8'
        }

        hover_data = {
            'period': True,
            'date': '|%d/%m/%Y',
            'spend': ':.2f',
            'day': False
        }

        fig_spend = px.line(combined_spend, x='day', y='spend', color='period',
                    title='Spesa giornaliera',
                    markers=True,
                    labels={'day': 'Giorno relativo al periodo', 'spend': 'Spesa (€)', 'period': 'Periodo', 'date': 'Data'},
                    color_discrete_map=color_map,
                    hover_data=hover_data)

        fig_spend.update_traces(mode='lines+markers')
        fig_spend.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
        fig_spend.update_traces(
            hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Spesa (€): %{y:.2f}<extra></extra>'
        )
        fig_spend.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.4,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig_spend)
    
    st.title("Dettaglio delle campagne")

    dettaglioCampagne = df.groupby('campaign').agg({
        'spend': 'sum',
        'impressions': 'sum',
        'clicks': 'sum'
    }).reset_index()

    dettaglioCampagne.rename(columns={
        'campaign': 'Campagna',
        'spend': 'Spesa',
        'impressions': 'Impression',
        'clicks': 'Click'
    }, inplace=True)

    dettaglioCampagne['CTR'] = dettaglioCampagne['Click'] / dettaglioCampagne['Impression']
    dettaglioCampagne['CPC'] = dettaglioCampagne['Spesa'] / dettaglioCampagne['Click']

    dettaglioCampagne['Spesa'] = dettaglioCampagne['Spesa'].map('€ {:,.2f}'.format)
    dettaglioCampagne['CTR'] = dettaglioCampagne['CTR'].map('{:.2%}'.format)
    dettaglioCampagne['CPC'] = dettaglioCampagne['CPC'].map('€ {:,.2f}'.format)

    st.dataframe(dettaglioCampagne)

# Database
# ------------------------------
def opportunities(df, df_comp):
    stages = ['Nuova Opportunità', 'Prova Gratuita', 'Numero Non corretto flusso di email marketing', 'Senza risposta', 'Fuori target', 'App Tel Fissato', 'Risposto/Da richiamare', 'Lead Perso (10 tentativi non risp)', 'Autonomo - Call Onboarding', 'Call onboarding', 'Cancellati - Da riprogrammare', 'No Show - Ghost', 'Non Pronto (in target)', 'Seconda call / demo', 'Preventivo Mandato / Follow Up', 'Vinto Abbonamento Mensile', 'Vinto Abbonamento Annuale', 'Vinto mensile con acc.impresa', 'Vinto annuale con acc.impresa', 'Vinti generici', 'Ag.marketing/collaborazioni', 'Cliente Non vinto']
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
        leadDaQualificare_delta = (df[df['stage'].isin(daQualificare)].shape[0] - df_comp[df_comp['stage'].isin(daQualificare)].shape[0]) / df_comp[df_comp['stage'].isin(daQualificare)].shape[0] * 100
        st.metric("Lead da qualificare", df[df['stage'].isin(daQualificare)].shape[0], percentage(leadDaQualificare_delta))
        
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            leadQualificati_delta = (df[df['stage'].isin(qualificati)].shape[0] - df_comp[df_comp['stage'].isin(qualificati)].shape[0]) / df_comp[df_comp['stage'].isin(qualificati)].shape[0] * 100
            st.metric("Lead qualificati", df[df['stage'].isin(qualificati)].shape[0], percentage(leadQualificati_delta))

            leadVinti_delta = (df[df['stage'].isin(vinti)].shape[0] - df_comp[df_comp['stage'].isin(vinti)].shape[0]) / df_comp[df_comp['stage'].isin(vinti)].shape[0] * 100
            st.metric("Vendite", df[df['stage'].isin(vinti)].shape[0], percentage(leadVinti_delta))
        with col1_2:
            leadQualificatiGiorno_delta = ((df[df['stage'].isin(qualificati)].shape[0] / (end_date - start_date).days) - (df_comp[df_comp['stage'].isin(qualificati)].shape[0] / (end_date - start_date).days)) / (df_comp[df_comp['stage'].isin(qualificati)].shape[0] / (end_date - start_date).days) * 100
            st.metric("Lead qualificati al giorno", thousand_2(df[df['stage'].isin(qualificati)].shape[0] / (end_date - start_date).days), percentage(leadQualificatiGiorno_delta))

            vintiPerGiorno_delta = ((df[df['stage'].isin(vinti)].shape[0]/((end_date - start_date).days)) - (df_comp[df_comp['stage'].isin(vinti)].shape[0]/((end_date - start_date).days))) / (df_comp[df_comp['stage'].isin(vinti)].shape[0]/((end_date - start_date).days)) * 100
            st.metric("Vendite al giorno", thousand_2(df[df['stage'].isin(vinti)].shape[0]/((end_date - start_date).days)), percentage(vintiPerGiorno_delta))
        with col1_3:
            tassoQualifica_delta = ((df[df['stage'].isin(qualificati)].shape[0]/(len(df)-df[df['stage'].isin(daQualificare)].shape[0])) - (df_comp[df_comp['stage'].isin(qualificati)].shape[0]/(len(df_comp)-df_comp[df_comp['stage'].isin(daQualificare)].shape[0]))) / (df_comp[df_comp['stage'].isin(qualificati)].shape[0]/(len(df_comp)-df_comp[df_comp['stage'].isin(daQualificare)].shape[0])) * 100
            st.metric("Tasso di qualifica", percentage(df[df['stage'].isin(qualificati)].shape[0]/(len(df)-df[df['stage'].isin(daQualificare)].shape[0])), percentage(tassoQualifica_delta))

            tassoVendita_delta = ((df[df['stage'].isin(vinti)].shape[0]/df[df['stage'].isin(qualificati)].shape[0]) - (df_comp[df_comp['stage'].isin(vinti)].shape[0]/df_comp[df_comp['stage'].isin(qualificati)].shape[0])) / (df_comp[df_comp['stage'].isin(vinti)].shape[0]/df_comp[df_comp['stage'].isin(qualificati)].shape[0]) * 100
            st.metric("Tasso di vendita", percentage(df[df['stage'].isin(vinti)].shape[0]/df[df['stage'].isin(qualificati)].shape[0]), percentage(tassoVendita_delta))
    with col2:
        df_qualificati = df[df['stage'].isin(qualificati)]
        df_qualificati_comp = df_comp[df_comp['stage'].isin(qualificati)]

        df_qualificati['createdAt'] = pd.to_datetime(df_qualificati['createdAt']).dt.date
        df_qualificati_comp['createdAt'] = pd.to_datetime(df_qualificati_comp['createdAt']).dt.date

        date_range_current = pd.date_range(start=df_qualificati['createdAt'].min(), end=df_qualificati['createdAt'].max())
        date_range_comp = pd.date_range(start=df_qualificati_comp['createdAt'].min(), end=df_qualificati_comp['createdAt'].max())

        daily_qualificati = df_qualificati.groupby('createdAt').size().reset_index(name='count')
        daily_qualificati = daily_qualificati.set_index('createdAt').reindex(date_range_current, fill_value=0).reset_index()
        daily_qualificati.rename(columns={'index': 'createdAt'}, inplace=True)

        daily_qualificati_comp = df_qualificati_comp.groupby('createdAt').size().reset_index(name='count')
        daily_qualificati_comp = daily_qualificati_comp.set_index('createdAt').reindex(date_range_comp, fill_value=0).reset_index()
        daily_qualificati_comp.rename(columns={'index': 'createdAt'}, inplace=True)

        daily_qualificati['day'] = (daily_qualificati['createdAt'] - daily_qualificati['createdAt'].min()).apply(lambda x: x.days)
        daily_qualificati_comp['day'] = (daily_qualificati_comp['createdAt'] - daily_qualificati_comp['createdAt'].min()).apply(lambda x: x.days)

        daily_qualificati['period'] = 'Periodo Corrente'
        daily_qualificati_comp['period'] = 'Periodo Precedente'

        combined_daily_qualificati = pd.concat([daily_qualificati_comp, daily_qualificati])

        color_map = {
            'Periodo Corrente': '#b12b94',
            'Periodo Precedente': '#eb94d8'
        }

        hover_data = {
            'period': True,
            'createdAt': '|%d/%m/%Y',
            'count': ':.2f',
            'day': False
        }

        fig_qualificati = px.line(combined_daily_qualificati, x='day', y='count', color='period',
                                title='Lead qualificati per giorno',
                                markers=True,
                                labels={'day': 'Giorno relativo al periodo', 'spend': 'Spesa (€)', 'period': 'Periodo', 'date': 'Data'},
                                color_discrete_map=color_map,
                                hover_data=hover_data)

        fig_qualificati.update_traces(mode='lines+markers')
        fig_qualificati.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
        fig_qualificati.update_traces(
            hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Lead: %{y:.2f}<extra></extra>'
        )
        fig_qualificati.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.4,
                xanchor="center",
                x=0.5
            )
        )

        st.plotly_chart(fig_qualificati)

    col3, col4, col5 = st.columns(3)
    with col3:
        deltaColor_lqperday = "green" if vintiPerGiorno_delta >= 0 else "red"

        fig_lqperday = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=float(df[df['stage'].isin(qualificati)].shape[0] / (end_date - start_date).days)/12*100,
            number={'suffix': "%"},
            delta={'reference': leadQualificatiGiorno_delta, 'relative': True, 'position': "bottom", 'valueformat': ".2f", 'increasing': {'color': deltaColor_lqperday}, 'decreasing': {'color': deltaColor_lqperday}, 'font': {'size': 16}},
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
        deltaColor_vintiperday = "green" if vintiPerGiorno_delta >= 0 else "red"

        fig_vintiperday = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=float(df[df['stage'].isin(vinti)].shape[0]/((end_date - start_date).days))/3*100,
            number={'suffix': "%"},
            delta={'reference': vintiPerGiorno_delta, 'relative': True, 'position': "bottom", 'valueformat': ".2f", 'increasing': {'color': deltaColor_vintiperday}, 'decreasing': {'color': deltaColor_vintiperday}, 'font': {'size': 16}},
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
        st.plotly_chart(fig_vintiperday)
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
        opp_delta = (len(df) - len(df_comp)) / len(df_comp) * 100
        st.metric("Opportunità", len(df), percentage(opp_delta))
        
        col6_1, col6_2, col6_3 = st.columns(3)
        with col6_1:
            setting_delta = (df[df['stage'].isin(daQualificare)].shape[0] - df_comp[df_comp['stage'].isin(daQualificare)].shape[0]) / df_comp[df_comp['stage'].isin(daQualificare)].shape[0] * 100
            st.metric("Setting - Da gestire", thousand_0(df[df['stage'].isin(daQualificare)].shape[0]), percentage(setting_delta))

            settingPersi_delta = (df[df['stage'].isin(leadPersi)].shape[0] - df_comp[df_comp['stage'].isin(leadPersi)].shape[0]) / df_comp[df_comp['stage'].isin(leadPersi)].shape[0] * 100
            st.metric("Setting - Persi", thousand_0(df[df['stage'].isin(leadPersi)].shape[0]), percentage(settingPersi_delta))
        with col6_2:
            vendite_delta = (df[df['stage'].isin(venditeGestione)].shape[0] - df_comp[df_comp['stage'].isin(venditeGestione)].shape[0]) / df_comp[df_comp['stage'].isin(venditeGestione)].shape[0] * 100
            st.metric("Vendita - Da gestire", thousand_0(df[df['stage'].isin(venditeGestione)].shape[0]), percentage(vendite_delta))

            chiusura_delta = (df[df['stage'].isin(venditeChiusura)].shape[0] - df_comp[df_comp['stage'].isin(venditeChiusura)].shape[0]) / df_comp[df_comp['stage'].isin(venditeChiusura)].shape[0] * 100
            st.metric("Vendita - Da chiudere", thousand_0(df[df['stage'].isin(venditeChiusura)].shape[0]), percentage(chiusura_delta))
        with col6_3:
            vinti_delta = (df[df['stage'].isin(vinti)].shape[0] - df_comp[df_comp['stage'].isin(vinti)].shape[0]) / df_comp[df_comp['stage'].isin(vinti)].shape[0] * 100
            st.metric("Vinti", thousand_0(df[df['stage'].isin(vinti)].shape[0]), percentage(vinti_delta))

            persi_delta = (df[df['stage'].isin(persi)].shape[0] - df_comp[df_comp['stage'].isin(persi)].shape[0]) / df_comp[df_comp['stage'].isin(persi)].shape[0] * 100
            st.metric("Persi", thousand_0(df[df['stage'].isin(persi)].shape[0]), percentage(persi_delta))
    with col7:
        df_opp = df
        df_opp_comp = df_comp

        df_opp['createdAt'] = pd.to_datetime(df_opp['createdAt']).dt.date
        df_opp_comp['createdAt'] = pd.to_datetime(df_opp_comp['createdAt']).dt.date

        daily_opp = df_opp.groupby('createdAt').size().reset_index(name='count')
        daily_opp_comp = df_opp_comp.groupby('createdAt').size().reset_index(name='count')

        daily_opp['day'] = (daily_opp['createdAt'] - daily_opp['createdAt'].min()).apply(lambda x: x.days)
        daily_opp_comp['day'] = (daily_opp_comp['createdAt'] - daily_opp_comp['createdAt'].min()).apply(lambda x: x.days)

        daily_opp['period'] = 'Periodo Corrente'
        daily_opp_comp['period'] = 'Periodo Precedente'

        combined_daily_opp = pd.concat([daily_opp_comp, daily_opp])

        color_map_opp = {
            'Periodo Corrente': '#b12b94',
            'Periodo Precedente': '#eb94d8'
        }

        hover_data_opp = {
            'period': True,
            'createdAt': '|%d/%m/%Y',
            'count': ':.2f',
            'day': False
        }

        fig_opp = px.line(combined_daily_opp, x='day', y='count', color='period',
                                title='Opportunità per giorno',
                                markers=True,
                                labels={'day': 'Giorno relativo al periodo', 'spend': 'Spesa (€)', 'period': 'Periodo', 'date': 'Data'},
                                color_discrete_map=color_map_opp,
                                hover_data=hover_data_opp)

        fig_opp.update_traces(mode='lines+markers')
        fig_opp.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
        fig_opp.update_traces(
            hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Lead: %{y:.2f}<extra></extra>'
        )
        fig_opp.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.4,
                xanchor="center",
                x=0.5
            )
        )

        st.plotly_chart(fig_opp)

    st.title("Dettaglio degli stage di pipeline")

    df['createdAt'] = pd.to_datetime(df['createdAt'])
    df['year_month'] = df['createdAt'].dt.to_period('M')

    pivot = df.pivot_table(index='stage', columns='year_month', aggfunc='size', fill_value=0)
    pivot = pivot.reindex(stages).fillna(0)
    pivot.columns = pivot.columns.astype(str)
    pivot['Totale stage'] = pivot.sum(axis=1)

    total_month = pd.DataFrame(pivot.sum(axis=0)).T
    total_month.index = ['Totale mese']

    df_stageCount = pd.concat([pivot, total_month])
    df_stageCount = df_stageCount.reset_index().rename(columns={'index': 'Stage'})
    st.dataframe(df_stageCount)

# ------------------------------
#             BODY
# ------------------------------
st.title("Parametri della analisi")

st.subheader("Selezionare il periodo desiderato")
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Inizio", (datetime.today() - timedelta(days=14)), format="DD/MM/YYYY")
with col_date2:
    end_date = st.date_input("Fine", (datetime.today() - timedelta(days=1)), format="DD/MM/YYYY")

privacy = st.checkbox("Accetto il trattamento dei miei dati secondo le normative vigenti.", value=False)

if st.button("Scarica i dati") & privacy:
    st.cache_data.clear()

    period = end_date - start_date + timedelta(days=1)

    comparison_start = start_date - period
    comparison_end = start_date -  timedelta(days=1)

    df_adv_raw = api_retrieving(comparison_start, end_date)
    df_adv_raw["date"] = pd.to_datetime(df_adv_raw["date"]).dt.date

    # Meta
    # ------------------------------
    df_meta = df_adv_raw.loc[
        (df_adv_raw["source"] == "facebook") &
        (df_adv_raw["account_name"] == st.secrets["meta_account"]) &
        (df_adv_raw["date"] >= start_date) &
        (df_adv_raw["date"] <= end_date) &
        (~df_adv_raw["campaign"].str.contains(r"\[HR\]")) &
        (~df_adv_raw["campaign"].str.contains(r"DENTALAI"))
    ]

    df_meta_comp = df_adv_raw.loc[
        (df_adv_raw["source"] == "facebook") &
        (df_adv_raw["account_name"] == st.secrets["meta_account"]) &
        (df_adv_raw["date"] >= comparison_start) &
        (df_adv_raw["date"] <= comparison_end) &
        (~df_adv_raw["campaign"].str.contains(r"\[HR\]")) &
        (~df_adv_raw["campaign"].str.contains(r"DENTALAI"))
    ]

    meta_analysis(df_meta, df_meta_comp)

    # Google
    # ------------------------------
    df_google = df_adv_raw.loc[
        (df_adv_raw["source"] == "google") &
        (df_adv_raw["account_name"] == st.secrets["google_account"]) &
        (df_adv_raw["date"] >= start_date) &
        (df_adv_raw["date"] <= end_date)
    ]

    df_google_comp = df_adv_raw.loc[
        (df_adv_raw["source"] == "google") &
        (df_adv_raw["account_name"] == st.secrets["google_account"]) &
        (df_adv_raw["date"] >= comparison_start) &
        (df_adv_raw["date"] <= comparison_end)
    ]

    google_analysis(df_google, df_google_comp)

    # Database
    # ------------------------------
    # conn = mysql.connector.connect(
    #     host=st.secrets["host"],
    #     port=st.secrets["port"],
    #     user=st.secrets["username"],
    #     password=st.secrets["password"],
    #     database=st.secrets["database"],
    #     auth_plugin='caching_sha2_password'
    # )

    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        host=st.secrets["host"],
        port=st.secrets["port"],
        user=st.secrets["username"],
        password=st.secrets["password"],
        database=st.secrets["database"],
        auth_plugin='caching_sha2_password'
    )

    df_opp_raw = opp_retrieving(pool, comparison_start, end_date)
    df_opp_raw['createdAt'] = pd.to_datetime(df_opp_raw['createdAt']).dt.date

    df_opp = df_opp_raw.loc[
        (df_opp_raw["createdAt"] >= start_date) &
        (df_opp_raw["createdAt"] <= end_date)
    ]

    df_opp_comp = df_opp_raw.loc[
        (df_opp_raw["createdAt"] >= comparison_start) &
        (df_opp_raw["createdAt"] <= comparison_end)
    ]

    opportunities(df_opp, df_opp_comp)