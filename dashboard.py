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
from data_analyzer import DataAnalyzer

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
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')

def currency(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"€ {integer_part},{decimal_part}"
    return formatted_value

def percentage(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"{integer_part},{decimal_part}%"
    return formatted_value

def thousand_0(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"{integer_part}"
    return formatted_value

def thousand_2(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"{integer_part},{decimal_part}"
    return formatted_value

def get_metric_delta(current, previous):
    if previous == 0:
        return "-"
    return percentage((current - previous) / previous * 100)

# Data retrieving
# ------------------------------
def api_retrieving(data_source, fields, start_date, end_date):
    url = st.secrets.source + data_source + "?api_key=" + st.secrets.api_key + "&date_from=" + str(start_date) + "&date_to=" + str(end_date) + "&fields=" + fields + "&_renderer=json"
    response = urlopen(url)
    data_json = json.loads(response.read())
    return pd.json_normalize(data_json, record_path=["data"])

def opp_retrieving(pool, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    query = f"""
                SELECT
                    o.createdAt,
                    o.lastStageChangeAt,
                    o.monetaryValue,
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

def lead_retrieving(pool, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    query = f"""
                SELECT
                    contacts.email,
                    sub_account_custom_fields.name AS custom_field_name,
                    FROM_UNIXTIME(contact_custom_fields.value / 1000, '%d/%m/%Y') AS custom_field_value,
                    additional_custom_field.value AS additional_custom_field_value,
                    opportunity_pipeline_stages.name AS pipeline_stage_name
                FROM
                    contacts
                    JOIN contact_custom_fields ON contacts.id = contact_custom_fields.contactId
                    JOIN sub_account_custom_fields ON contact_custom_fields.id = sub_account_custom_fields.id
                    LEFT JOIN contact_custom_fields AS additional_custom_field
                        ON contacts.id = additional_custom_field.contactId
                        AND additional_custom_field.id = 'UiALy82OthZAitbSZTOU'
                    LEFT JOIN opportunities ON contacts.id = opportunities.contactId
                    LEFT JOIN opportunity_pipeline_stages ON opportunities.pipelineStageId = opportunity_pipeline_stages.id
                WHERE
                    sub_account_custom_fields.locationId = '{st.secrets.id_cliente}'
                    AND sub_account_custom_fields.id = 'ok7yK4uSS6wh0S2DnZrz'
                    AND FROM_UNIXTIME(contact_custom_fields.value / 1000, '%Y-%m-%d') BETWEEN {start_date} AND {end_date};
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
        spesa_totale_delta = get_metric_delta(df["spend"].sum(), df_comp["spend"].sum())
        st.metric("Spesa totale", currency(df["spend"].sum()), spesa_totale_delta)

        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            campagne_attive_delta = get_metric_delta(df["campaign"].nunique(), df_comp["campaign"].nunique())
            st.metric("Campagne attive", df["campaign"].nunique(), campagne_attive_delta)

            cpm_current = df["spend"].sum() / df["impressions"].sum() * 1000 if df["impressions"].sum() != 0 else 0
            cpm_comp = df_comp["spend"].sum() / df_comp["impressions"].sum() * 1000 if df_comp["impressions"].sum() != 0 else 0
            cpm_delta = get_metric_delta(cpm_current, cpm_comp)
            st.metric("CPM", currency(cpm_current) if cpm_current != 0 else "-", cpm_delta, delta_color="inverse")
        with col1_2:
            impression_delta = get_metric_delta(df["impressions"].sum(), df_comp["impressions"].sum())
            st.metric("Impression", thousand_0(df["impressions"].sum()), impression_delta)

            ctr_current = (df["outbound_clicks_outbound_click"].sum() / df["impressions"].sum()) * 100 if df["impressions"].sum() != 0 else 0
            ctr_comp = (df_comp["outbound_clicks_outbound_click"].sum() / df_comp["impressions"].sum()) * 100 if df_comp["impressions"].sum() != 0 else 0
            ctr_delta = get_metric_delta(ctr_current, ctr_comp)
            st.metric("CTR", percentage(ctr_current) if ctr_current != 0 else "-", ctr_delta)
        with col1_3:
            click_delta = get_metric_delta(df["outbound_clicks_outbound_click"].sum(), df_comp["outbound_clicks_outbound_click"].sum())
            st.metric("Click", thousand_0(df["outbound_clicks_outbound_click"].sum()), click_delta)

            cpc_current = df["outbound_clicks_outbound_click"].sum() / df["spend"].sum() if df["spend"].sum() != 0 else 0
            cpc_comp = df_comp["outbound_clicks_outbound_click"].sum() / df_comp["spend"].sum() if df_comp["spend"].sum() != 0 else 0
            cpc_delta = get_metric_delta(cpc_current, cpc_comp)
            st.metric("CPC", currency(cpc_current) if cpc_current != 0 else "-", cpc_delta, delta_color="inverse")
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
def gads_analysis(df, df_comp):
    st.title("Analisi delle campagne Google")

    col1, col2 = st.columns(2)
    with col1:
        spesaTot_delta = get_metric_delta(df["spend"].sum(), df_comp["spend"].sum())
        st.metric("Spesa totale", currency(df["spend"].sum()), spesaTot_delta)

        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            campagne_delta = get_metric_delta(df["campaign"].nunique(), df_comp["campaign"].nunique())
            st.metric("Campagne attive", df["campaign"].nunique(), campagne_delta)

            cpm_current = df["spend"].sum() / df["impressions"].sum() * 1000 if df["impressions"].sum() != 0 else 0
            cpm_comp = df_comp["spend"].sum() / df_comp["impressions"].sum() * 1000 if df_comp["impressions"].sum() != 0 else 0
            cpm_delta = get_metric_delta(cpm_current, cpm_comp)
            st.metric("CPM", currency(cpm_current) if cpm_current != 0 else "-", cpm_delta, delta_color="inverse")

        with col1_2:
            impression_delta = get_metric_delta(df["impressions"].sum(), df_comp["impressions"].sum())
            st.metric("Impression", thousand_0(df["impressions"].sum()), impression_delta)

            ctr_current = (df["clicks"].sum() / df["impressions"].sum()) * 100 if df["impressions"].sum() != 0 else 0
            ctr_comp = (df_comp["clicks"].sum() / df_comp["impressions"].sum()) * 100 if df_comp["impressions"].sum() != 0 else 0
            ctr_delta = get_metric_delta(ctr_current, ctr_comp)
            st.metric("CTR", percentage(ctr_current) if ctr_current != 0 else "-", ctr_delta)

        with col1_3:
            click_delta = get_metric_delta(df["clicks"].sum(), df_comp["clicks"].sum())
            st.metric("Click", thousand_0(df["clicks"].sum()), click_delta)

            cpc_current = df["clicks"].sum() / df["spend"].sum() if df["spend"].sum() != 0 else 0
            cpc_comp = df_comp["clicks"].sum() / df_comp["spend"].sum() if df_comp["spend"].sum() != 0 else 0
            cpc_delta = get_metric_delta(cpc_current, cpc_comp)
            st.metric("CPC", currency(cpc_current) if cpc_current != 0 else "-", cpc_delta, delta_color="inverse")
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

def ganalytics_analysis(df, df_comp):
    st.title("Analisi del traffico")

    col1, col2 = st.columns(2)
    with col1:
        active_user_delta = get_metric_delta(df["active_users"].sum(), df_comp["active_users"].sum())
        st.metric("Utenti attivi", thousand_0(df["active_users"].sum()), active_user_delta)

        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            sessioni_delta = get_metric_delta(df["sessions"].sum(), df_comp["sessions"].sum())
            st.metric("Sessioni", thousand_0(df["sessions"].sum()), sessioni_delta)

            sessions_users_current = df["sessions"].sum() / df["active_users"].sum() if df["active_users"].sum() != 0 else 0
            sessions_users_comp = df_comp["sessions"].sum() / df_comp["active_users"].sum() if df_comp["active_users"].sum() != 0 else 0
            sessions_users_delta = get_metric_delta(sessions_users_current, sessions_users_comp)
            st.metric("Sessioni per utente attivo", thousand_2(sessions_users_current) if sessions_users_current != 0 else "-", sessions_users_delta)

        with col1_2:
            sessioni_engaged_delta = get_metric_delta(df["engaged_sessions"].sum(), df_comp["engaged_sessions"].sum())
            st.metric("Sessioni con engage", thousand_0(df["engaged_sessions"].sum()), sessioni_engaged_delta)

            durata_sessione_current = df["user_engagement_duration"].sum() / df["sessions"].sum() if df["sessions"].sum() != 0 else 0
            durata_sessione_comp = df_comp["user_engagement_duration"].sum() / df_comp["sessions"].sum() if df_comp["sessions"].sum() != 0 else 0
            durata_sessione_delta = get_metric_delta(durata_sessione_current, durata_sessione_comp)
            st.metric("Durata media sessione (sec)", thousand_2(durata_sessione_current) if durata_sessione_current != 0 else "-", durata_sessione_delta)

        with col1_3:
            engage_rate_current = df["engaged_sessions"].sum() / df["sessions"].sum() if df["sessions"].sum() != 0 else 0
            engage_rate_comp = df_comp["engaged_sessions"].sum() / df_comp["sessions"].sum() if df_comp["sessions"].sum() != 0 else 0
            engage_delta = get_metric_delta(engage_rate_current, engage_rate_comp)
            st.metric("Tasso di engage", percentage(engage_rate_current) if engage_rate_current != 0 else "-", engage_delta)

            tempo_user_current = df["user_engagement_duration"].sum() / df["active_users"].sum() if df["active_users"].sum() != 0 else 0
            tempo_user_comp = df_comp["user_engagement_duration"].sum() / df_comp["active_users"].sum() if df_comp["active_users"].sum() != 0 else 0
            tempo_user_delta = get_metric_delta(tempo_user_current, tempo_user_comp)
            st.metric("Tempo per utente (sec)", thousand_2(tempo_user_current) if tempo_user_current != 0 else "-", tempo_user_delta)
    with col2:
        df.loc[:, 'date'] = pd.to_datetime(df['date']).dt.date
        daily_users_current = df.groupby('date')['active_users'].sum().reset_index()

        df_comp.loc[:, 'date'] = pd.to_datetime(df_comp['date']).dt.date
        daily_users_comp = df_comp.groupby('date')['active_users'].sum().reset_index()

        daily_users_current['day'] = (daily_users_current['date'] - daily_users_current['date'].min()).apply(lambda x: x.days)
        daily_users_comp['day'] = (daily_users_comp['date'] - daily_users_comp['date'].min()).apply(lambda x: x.days)

        daily_users_current['period'] = 'Periodo Corrente'
        daily_users_comp['period'] = 'Periodo Precedente'

        combined_users = pd.concat([daily_users_comp, daily_users_current])

        color_map = {
            'Periodo Corrente': '#b12b94',
            'Periodo Precedente': '#eb94d8'
        }

        hover_data = {
            'period': True,
            'date': '|%d/%m/%Y',
            'active_users': ':.0f',
            'day': False
        }

        fig_spend = px.line(combined_users, x='day', y='active_users', color='period',
                    title='Utenti attivi',
                    markers=True,
                    labels={'day': 'Giorno relativo al periodo', 'active_users': 'Utenti attivi', 'period': 'Periodo', 'date': 'Data'},
                    color_discrete_map=color_map,
                    hover_data=hover_data)

        fig_spend.update_traces(mode='lines+markers')
        fig_spend.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
        fig_spend.update_traces(
            hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Utenti attivi: %{y:.0f}<extra></extra>'
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

    st.title("Analisi del traffico")

    col3, col4 = st.columns(2)

    with col3:
        google = df[df['source'].str.contains('google') & ~df['source'].str.contains('googleads')]
        google_ads = df[df['source'].str.contains('googleads')]
        meta_ads = df[df['source'].str.contains('facebook|instagram')]
        youtube = df[df['source'].str.contains('youtube')]
        traffico_diretto = df[df['source'].str.contains(r'\(direct\)')]
        fonti_sconosciute = df[df['source'].str.contains(r'\(not set\)')]
        altre_fonti = df[~df['source'].str.contains('google|googleads|facebook|instagram|youtube|\\(direct\\)|\\(not set\\)')]

        session_groups = {
            "google": google['sessions'].sum(),
            "google_ads": google_ads['sessions'].sum(),
            "meta_ads": meta_ads['sessions'].sum(),
            "youtube": youtube['sessions'].sum(),
            "traffico diretto": traffico_diretto['sessions'].sum(),
            "fonti sconosciute": fonti_sconosciute['sessions'].sum(),
            "altre fonti": altre_fonti['sessions'].sum()
        }

        session_df = pd.DataFrame(list(session_groups.items()), columns=['source_group', 'sessions'])

        total_sessions = session_df['sessions'].sum()
        if total_sessions == 0:
            session_df['percentage'] = 0.00
        else:
            session_df['percentage'] = (session_df['sessions'] / total_sessions) * 100

        source_session_soglia = 3.00
        main_groups = session_df[session_df['percentage'] >= source_session_soglia].copy()

        fig_session_pie = px.pie(main_groups, values='sessions', names='source_group', title='Distribuzione delle sessioni per fonte')

        fig_session_pie.update_traces(
            hovertemplate='Fonte: %{label}<br>Sessioni: %{value}<extra></extra>'
        )

        st.plotly_chart(fig_session_pie)
        st.write(f'Valore di soglia: {source_session_soglia}%')
    with col4:
        campaign_sessions = df.groupby('campaign')['sessions'].sum().reset_index()

        total_campaign_sessions = campaign_sessions['sessions'].sum()
        if total_campaign_sessions == 0:
            campaign_sessions['percentage'] = 0.00
        else:
            campaign_sessions['percentage'] = (campaign_sessions['sessions'] / total_campaign_sessions) * 100

        campaign_session_soglia = 3.00
        main_groups = campaign_sessions[campaign_sessions['percentage'] >= campaign_session_soglia].copy()

        fig_campaign = px.pie(main_groups, values='sessions', names='campaign', title='Distribuzione delle sessioni per campagna')

        fig_campaign.update_traces(
            hovertemplate='Campagna: %{label}<br>Sessioni: %{value}<extra></extra>'
        )

        st.plotly_chart(fig_campaign)
        st.write(f'Valore di soglia: {campaign_session_soglia}%')

# Database
# ------------------------------
def opportunities(df, df_comp):
    st.title("Stato dei lead")

    col1, col2 = st.columns(2)
    with col1:
        leadDaQualificare_delta = get_metric_delta(df[df['stage'].isin(STAGES['daQualificare'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['daQualificare'])].shape[0])
        st.metric("Lead da qualificare", df[df['stage'].isin(STAGES['daQualificare'])].shape[0], leadDaQualificare_delta)
        
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            leadQualificati_delta = get_metric_delta(df[df['stage'].isin(STAGES['qualificati'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['qualificati'])].shape[0])
            st.metric("Lead qualificati", df[df['stage'].isin(STAGES['qualificati'])].shape[0], leadQualificati_delta)

            leadVinti_delta = get_metric_delta(df[df['stage'].isin(STAGES['vinti'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['vinti'])].shape[0])
            st.metric("Vendite", df[df['stage'].isin(STAGES['vinti'])].shape[0], leadVinti_delta)
        with col1_2:
            lead_qualificati_giorno = df[df['stage'].isin(STAGES['qualificati'])].shape[0] / (end_date - start_date).days
            lead_qualificati_giorno_comp = df_comp[df_comp['stage'].isin(STAGES['qualificati'])].shape[0] / (end_date - start_date).days
            leadQualificatiGiorno_delta = get_metric_delta(lead_qualificati_giorno, lead_qualificati_giorno_comp)
            st.metric("Lead qualificati al giorno", thousand_2(lead_qualificati_giorno), leadQualificatiGiorno_delta)

            vinti_per_giorno = df[df['stage'].isin(STAGES['vinti'])].shape[0] / (end_date - start_date).days
            vinti_per_giorno_comp = df_comp[df_comp['stage'].isin(STAGES['vinti'])].shape[0] / (end_date - start_date).days
            vintiPerGiorno_delta = get_metric_delta(vinti_per_giorno, vinti_per_giorno_comp)
            st.metric("Vendite al giorno", thousand_2(vinti_per_giorno), vintiPerGiorno_delta)
        with col1_3:
            tasso_qualifica_corrente = df[df['stage'].isin(STAGES['qualificati'])].shape[0] / (len(df) - df[df['stage'].isin(STAGES['daQualificare'])].shape[0]) if len(df) > df[df['stage'].isin(STAGES['daQualificare'])].shape[0] else 0
            tasso_qualifica_precedente = df_comp[df_comp['stage'].isin(STAGES['qualificati'])].shape[0] / (len(df_comp) - df_comp[df_comp['stage'].isin(STAGES['daQualificare'])].shape[0]) if len(df_comp) > df_comp[df_comp['stage'].isin(STAGES['daQualificare'])].shape[0] else 0
            tassoQualifica_delta = get_metric_delta(tasso_qualifica_corrente, tasso_qualifica_precedente)
            st.metric("Tasso di qualifica", percentage(tasso_qualifica_corrente) if tasso_qualifica_corrente != 0 else "-", tassoQualifica_delta)

            tasso_vendita_corrente = df[df['stage'].isin(STAGES['vinti'])].shape[0] / df[df['stage'].isin(STAGES['qualificati'])].shape[0] if df[df['stage'].isin(STAGES['qualificati'])].shape[0] > 0 else 0
            tasso_vendita_precedente = df_comp[df_comp['stage'].isin(STAGES['vinti'])].shape[0] / df_comp[df_comp['stage'].isin(STAGES['qualificati'])].shape[0] if df_comp[df_comp['stage'].isin(STAGES['qualificati'])].shape[0] > 0 else 0
            tassoVendita_delta = get_metric_delta(tasso_vendita_corrente, tasso_vendita_precedente)
            st.metric("Tasso di vendita", percentage(tasso_vendita_corrente) if tasso_vendita_corrente != 0 else "-", tassoVendita_delta)
    with col2:
        df_qualificati = df[df['stage'].isin(STAGES['qualificati'])]
        df_qualificati_comp = df_comp[df_comp['stage'].isin(STAGES['qualificati'])]

        df_qualificati.loc[:, 'createdAt'] = pd.to_datetime(df_qualificati['createdAt']).dt.date
        df_qualificati_comp.loc[:, 'createdAt'] = pd.to_datetime(df_qualificati_comp['createdAt']).dt.date

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
        lqPerDay_delta = (lead_qualificati_giorno - lead_qualificati_giorno_comp) / lead_qualificati_giorno_comp * 100 if lead_qualificati_giorno_comp != 0 else 0
        deltaColor_lqperday = "green" if lqPerDay_delta >= 0 else "red"

        fig_lqperday = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=float(lead_qualificati_giorno)/12*100,
            number={'suffix': "%"},
            delta={'reference': lqPerDay_delta, 'relative': True, 'position': "bottom", 'valueformat': ".2f", 'increasing': {'color': deltaColor_lqperday}, 'decreasing': {'color': deltaColor_lqperday}, 'font': {'size': 16}},
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
        vintiPerDay_delta = (vinti_per_giorno - vinti_per_giorno_comp) / vinti_per_giorno_comp * 100 if vinti_per_giorno_comp != 0 else 0
        deltaColor_vintiperday = "green" if vintiPerDay_delta >= 0 else "red"

        fig_vintiperday = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=float(df[df['stage'].isin(STAGES['vinti'])].shape[0]/((end_date - start_date).days))/3*100,
            number={'suffix': "%"},
            delta={'reference': vintiPerDay_delta, 'relative': True, 'position': "bottom", 'valueformat': ".2f", 'increasing': {'color': deltaColor_vintiperday}, 'decreasing': {'color': deltaColor_vintiperday}, 'font': {'size': 16}},
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

        opportunitàPerse = STAGES['leadPersi'] + STAGES['persi']
        filtered_counts = {stage: opportunitàPerStage.get(stage, 0) for stage in opportunitàPerse}
        opportunitàPerse_df = pd.DataFrame(list(filtered_counts.items()), columns=['Stage', 'Opportunità'])
        
        st.dataframe(opportunitàPerse_df.style.hide(axis='index'))
    
    st.title("Gestione delle opportunità")

    col6, col7 = st.columns(2)
    with col6:
        opp_delta = get_metric_delta(len(df), len(df_comp))
        st.metric("Opportunità", len(df), opp_delta)
        
        col6_1, col6_2, col6_3 = st.columns(3)
        with col6_1:
            setting_delta = get_metric_delta(df[df['stage'].isin(STAGES['daQualificare'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['daQualificare'])].shape[0])
            st.metric("Setting - Da gestire", thousand_0(df[df['stage'].isin(STAGES['daQualificare'])].shape[0]), setting_delta)

            settingPersi_delta = get_metric_delta(df[df['stage'].isin(STAGES['leadPersi'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['leadPersi'])].shape[0])
            st.metric("Setting - Persi", thousand_0(df[df['stage'].isin(STAGES['leadPersi'])].shape[0]), settingPersi_delta)
        with col6_2:
            vendite_delta = get_metric_delta(df[df['stage'].isin(STAGES['venditeGestione'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['venditeGestione'])].shape[0])
            st.metric("Vendita - Da gestire", thousand_0(df[df['stage'].isin(STAGES['venditeGestione'])].shape[0]), vendite_delta)

            chiusura_delta = get_metric_delta(df[df['stage'].isin(STAGES['venditeChiusura'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['venditeChiusura'])].shape[0])
            st.metric("Vendita - Da chiudere", thousand_0(df[df['stage'].isin(STAGES['venditeChiusura'])].shape[0]), chiusura_delta)
        with col6_3:
            vinti_delta = get_metric_delta(df[df['stage'].isin(STAGES['vinti'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['vinti'])].shape[0])
            st.metric("Vinti", thousand_0(df[df['stage'].isin(STAGES['vinti'])].shape[0]), vinti_delta)

            persi_delta = get_metric_delta(df[df['stage'].isin(STAGES['persi'])].shape[0], df_comp[df_comp['stage'].isin(STAGES['persi'])].shape[0])
            st.metric("Persi", thousand_0(df[df['stage'].isin(STAGES['persi'])].shape[0]), persi_delta)
    with col7:
        df.loc[:, 'createdAt'] = pd.to_datetime(df['createdAt']).dt.date
        opp_per_giorno = df.groupby('createdAt').size().reset_index(name='conteggio')
        
        df_comp.loc[:, 'createdAt'] = pd.to_datetime(df_comp['createdAt']).dt.date
        opp_per_giorno_comp = df_comp.groupby('createdAt').size().reset_index(name='conteggio')
        
        opp_per_giorno['day'] = (opp_per_giorno['createdAt'] - opp_per_giorno['createdAt'].min()).apply(lambda x: x.days)
        opp_per_giorno_comp['day'] = (opp_per_giorno_comp['createdAt'] - opp_per_giorno_comp['createdAt'].min()).apply(lambda x: x.days)
        
        opp_per_giorno['period'] = 'Periodo Corrente'
        opp_per_giorno_comp['period'] = 'Periodo Precedente'
        
        combined_opp = pd.concat([opp_per_giorno, opp_per_giorno_comp])
        
        color_map = {
            'Periodo Corrente': '#b12b94',
            'Periodo Precedente': '#eb94d8'
        }
        
        hover_data = {
            'period': True,
            'createdAt': '|%d/%m/%Y',
            'conteggio': ':.0f',
            'day': False
        }
        
        fig_opp = px.line(combined_opp, x='day', y='conteggio', color='period',
                    title='Opportunità per giorno',
                    markers=True,
                    labels={'day': 'Giorno relativo al periodo', 'conteggio': 'Numero di Opportunità', 'period': 'Periodo', 'createdAt': 'Data'},
                    color_discrete_map=color_map,
                    hover_data=hover_data)
        
        fig_opp.update_traces(mode='lines+markers')
        fig_opp.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
        fig_opp.update_traces(
            hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Numero di Opportunità: %{y:.0f}<extra></extra>'
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

    # Data retrival
    # ------------------------------
    df_meta_raw = api_retrieving('facebook', FIELDS['meta'], comparison_start, end_date)
    df_meta_raw["date"] = pd.to_datetime(df_meta_raw["date"]).dt.date

    df_gads_raw = api_retrieving('google_ads', FIELDS['gads'], comparison_start, end_date)
    df_gads_raw["date"] = pd.to_datetime(df_gads_raw["date"]).dt.date

    df_ganalytics_raw = api_retrieving('googleanalytics4', FIELDS['ganalytics'], comparison_start, end_date)
    df_ganalytics_raw["date"] = pd.to_datetime(df_ganalytics_raw["date"]).dt.date
    
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
    df_opp_raw['lastStageChangeAt'] = pd.to_datetime(df_opp_raw['lastStageChangeAt']).dt.date
    
    # df_lead_raw = lead_retrieving(pool, comparison_start, end_date)
    # df_lead_raw['custom_field_value'] = pd.to_datetime(df_lead_raw['custom_field_value'], format='%d/%m/%Y', errors='coerce')
    
    # Data processing
    # ------------------------------
    analyzer = DataAnalyzer(start_date, end_date, comparison_start, comparison_end)

    # Meta
    df_meta = df_meta_raw.loc[
        (df_meta_raw["datasource"] == "facebook") &
        (df_meta_raw["account_name"] == st.secrets["meta_account"]) &
        (df_meta_raw["date"] >= start_date) &
        (df_meta_raw["date"] <= end_date) &
        (~df_meta_raw["campaign"].str.contains(r"\[HR\]")) &
        (~df_meta_raw["campaign"].str.contains(r"DENTALAI"))
    ]

    df_meta_comp = df_meta_raw.loc[
        (df_meta_raw["datasource"] == "facebook") &
        (df_meta_raw["account_name"] == st.secrets["meta_account"]) &
        (df_meta_raw["date"] >= comparison_start) &
        (df_meta_raw["date"] <= comparison_end) &
        (~df_meta_raw["campaign"].str.contains(r"\[HR\]")) &
        (~df_meta_raw["campaign"].str.contains(r"DENTALAI"))
    ]

    meta_results, meta_results_comp = analyzer.analyze_meta(df_meta, df_meta_comp)

    # Google ads
    df_gads = df_gads_raw.loc[
        (df_gads_raw["datasource"] == "google") &
        (df_gads_raw["account_name"] == st.secrets["gads_account"]) &
        (df_gads_raw["date"] >= start_date) &
        (df_gads_raw["date"] <= end_date)
    ]

    df_gads_comp = df_gads_raw.loc[
        (df_gads_raw["datasource"] == "google") &
        (df_gads_raw["account_name"] == st.secrets["gads_account"]) &
        (df_gads_raw["date"] >= comparison_start) &
        (df_gads_raw["date"] <= comparison_end)
    ]

    # Google Analytics 4
    df_ganalytics = df_ganalytics_raw.loc[
        (df_ganalytics_raw["datasource"] == "googleanalytics4") &
        (df_ganalytics_raw["account_name"] == st.secrets["ganalytics_account"]) &
        (df_ganalytics_raw["date"] >= start_date) &
        (df_ganalytics_raw["date"] <= end_date)
    ]

    df_ganalytics_comp = df_ganalytics_raw.loc[
        (df_ganalytics_raw["datasource"] == "googleanalytics4") &
        (df_ganalytics_raw["account_name"] == st.secrets["ganalytics_account"]) &
        (df_ganalytics_raw["date"] >= comparison_start) &
        (df_ganalytics_raw["date"] <= comparison_end)
    ]

    # Database
    df_opp = df_opp_raw.loc[
        (df_opp_raw["createdAt"] >= start_date) &
        (df_opp_raw["createdAt"] <= end_date)
    ]

    df_opp_comp = df_opp_raw.loc[
        (df_opp_raw["createdAt"] >= comparison_start) &
        (df_opp_raw["createdAt"] <= comparison_end)
    ]

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
    economics(df_opp, df_opp_comp, df_opp_stage, df_opp_stage_comp, df_meta, df_meta_comp, df_gads, df_gads_comp)

    meta_analysis(df_meta, df_meta_comp)

    gads_analysis(df_gads, df_gads_comp)

    opportunities(df_opp, df_opp_comp)

    ganalytics_analysis(df_ganalytics, df_ganalytics_comp)

    # DA FARE: analisi dei flussi dei singoli funnel
    # DA FARE: aggiunta dell'attribuzione dei lead