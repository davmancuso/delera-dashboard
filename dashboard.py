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
from data_analyzer import BaseAnalyzer, MetaAnalyzer, GadsAnalyzer, GanalyticsAnalyzer
from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta
from data_retrieval import api_retrieving, opp_retrieving, lead_retrieving
from data_visualization import meta_analysis, gads_analysis, ganalytics_analysis

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

    # pool = mysql.connector.pooling.MySQLConnectionPool(
    #     pool_name="mypool",
    #     pool_size=5,
    #     host=st.secrets["host"],
    #     port=st.secrets["port"],
    #     user=st.secrets["username"],
    #     password=st.secrets["password"],
    #     database=st.secrets["database"],
    #     auth_plugin='caching_sha2_password'
    # )

    # Data retrival
    # ------------------------------
    df_meta_raw = api_retrieving('facebook', FIELDS['meta'], comparison_start, end_date)

    df_gads_raw = api_retrieving('google_ads', FIELDS['gads'], comparison_start, end_date)

    df_ganalytics_raw = api_retrieving('googleanalytics4', FIELDS['ganalytics'], comparison_start, end_date)
    
    # df_opp_raw = opp_retrieving(pool, comparison_start, end_date)
    # df_opp_raw['createdAt'] = pd.to_datetime(df_opp_raw['createdAt']).dt.date
    # df_opp_raw['lastStageChangeAt'] = pd.to_datetime(df_opp_raw['lastStageChangeAt']).dt.date
    
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

    # Database
    # df_opp = df_opp_raw.loc[
    #     (df_opp_raw["createdAt"] >= start_date) &
    #     (df_opp_raw["createdAt"] <= end_date)
    # ]

    # df_opp_comp = df_opp_raw.loc[
    #     (df_opp_raw["createdAt"] >= comparison_start) &
    #     (df_opp_raw["createdAt"] <= comparison_end)
    # ]

    # df_opp_stage = df_opp_raw.loc[
    #     (df_opp_raw["lastStageChangeAt"] >= start_date) &
    #     (df_opp_raw["lastStageChangeAt"] <= end_date)
    # ]

    # df_opp_stage_comp = df_opp_raw.loc[
    #     (df_opp_raw["lastStageChangeAt"] >= comparison_start) &
    #     (df_opp_raw["lastStageChangeAt"] <= comparison_end)
    # ]

    # Data visualization
    # ------------------------------
    # economics(df_opp, df_opp_comp, df_opp_stage, df_opp_stage_comp, df_meta, df_meta_comp, df_gads, df_gads_comp)

    meta_analysis(meta_results, meta_results_comp)

    gads_analysis(gads_results, gads_results_comp)

    # opportunities(df_opp, df_opp_comp)

    ganalytics_analysis(ganalytics_results, ganalytics_results_comp)

    # DA FARE: analisi dei flussi dei singoli funnel
    # DA FARE: aggiunta dell'attribuzione dei lead