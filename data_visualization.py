import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta

# ------------------------------
#             META
# ------------------------------
def meta_metrics(results, results_comp):
    spesa_totale_delta = get_metric_delta(results["spesa_totale"], results_comp["spesa_totale"])
    st.metric("Spesa totale", currency(results["spesa_totale"]), spesa_totale_delta)

    col1, col2, col3 = st.columns(3)
    with col1:
        campagne_attive_delta = get_metric_delta(results["campagne_attive"], results_comp["campagne_attive"])
        st.metric("Campagne attive", results["campagne_attive"], campagne_attive_delta)

        cpm_delta = get_metric_delta(results["cpm"], results_comp["cpm"])
        st.metric("CPM", currency(results["cpm"]) if results["cpm"] != 0 else "-", cpm_delta, delta_color="inverse")
    with col2:
        impression_delta = get_metric_delta(results["impression"], results_comp["impression"])
        st.metric("Impression", thousand_0(results["impression"]), impression_delta)

        ctr_delta = get_metric_delta(results["ctr"], results_comp["ctr"])
        st.metric("CTR", percentage(results["ctr"]) if results["ctr"] != 0 else "-", ctr_delta)
    with col3:
        click_delta = get_metric_delta(results["click"], results_comp["click"])
        st.metric("Click", thousand_0(results["click"]), click_delta)

        cpc_delta = get_metric_delta(results["cpc"], results_comp["cpc"])
        st.metric("CPC", currency(results["cpc"]) if results["cpc"] != 0 else "-", cpc_delta, delta_color="inverse")

def meta_spend_chart(results, results_comp):
    daily_spend_current = results['spesa_giornaliera']
    daily_spend_comp = results_comp['spesa_giornaliera']

    num_days = (results['spesa_giornaliera']['date'].max() - results['spesa_giornaliera']['date'].min()).days + 1

    daily_spend_current['day'] = range(num_days)
    daily_spend_comp['day'] = range(num_days)

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
                labels={'day': 'Giorno relativo al periodo', 'spend': 'Spesa (€)', 'period': 'Periodo'},
                color_discrete_map=color_map,
                hover_data=hover_data)

    fig_spend.update_traces(mode='lines+markers')
    fig_spend.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
    fig_spend.update_xaxes(title='Giorno del periodo')
    fig_spend.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Data: %{customdata[1]}<br>Spesa (€): %{y:.2f}<extra></extra>')
    fig_spend.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5
        )
    )

    return fig_spend

def meta_campaign_details(dettaglioCampagne):
    dettaglioCampagne['Spesa'] = dettaglioCampagne['Spesa'].apply(currency)
    dettaglioCampagne['CTR'] = dettaglioCampagne['CTR'].apply(percentage)
    dettaglioCampagne['CPC'] = dettaglioCampagne['CPC'].apply(currency)
    st.dataframe(dettaglioCampagne)

def meta_analysis(results, results_comp):
    st.title("Analisi delle campagne Meta")

    col1, col2 = st.columns(2)
    with col1:
        meta_metrics(results, results_comp)
    with col2:
        fig_spend = meta_spend_chart(results, results_comp)
        st.plotly_chart(fig_spend)
    
    st.title("Dettaglio delle campagne")
    meta_campaign_details(results['dettaglio_campagne'].copy())

# ------------------------------
#           GOOGLE ADS
# ------------------------------
def gads_metrics(results, results_comp):
    spesaTot_delta = get_metric_delta(results["spesa_totale"], results_comp["spesa_totale"])
    st.metric("Spesa totale", currency(results["spesa_totale"]), spesaTot_delta)

    col1, col2, col3 = st.columns(3)
    with col1:
        campagne_delta = get_metric_delta(results["campagne_attive"], results_comp["campagne_attive"])
        st.metric("Campagne attive", results["campagne_attive"], campagne_delta)

        cpm_delta = get_metric_delta(results["cpm"], results_comp["cpm"])
        st.metric("CPM", currency(results["cpm"]) if results["cpm"] != 0 else "-", cpm_delta, delta_color="inverse")

    with col2:
        impression_delta = get_metric_delta(results["impression"], results_comp["impression"])
        st.metric("Impression", thousand_0(results["impression"]), impression_delta)

        ctr_delta = get_metric_delta(results["ctr"], results_comp["ctr"])
        st.metric("CTR", percentage(results["ctr"]) if results["ctr"] != 0 else "-", ctr_delta)

    with col3:
        click_delta = get_metric_delta(results["click"], results_comp["click"])
        st.metric("Click", thousand_0(results["click"]), click_delta)

        cpc_delta = get_metric_delta(results["cpc"], results_comp["cpc"])
        st.metric("CPC", currency(results["cpc"]) if results["cpc"] != 0 else "-", cpc_delta, delta_color="inverse")

def gads_spend_chart(results, results_comp):
    daily_spend_current = results['spesa_giornaliera']
    daily_spend_comp = results_comp['spesa_giornaliera']
    
    num_days = (results['spesa_giornaliera']['date'].max() - results['spesa_giornaliera']['date'].min()).days + 1
    
    daily_spend_current['day'] = range(num_days)
    daily_spend_comp['day'] = range(num_days)

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
                labels={'day': 'Giorno relativo al periodo', 'spend': 'Spesa (€)', 'period': 'Periodo'},
                color_discrete_map=color_map,
                hover_data=hover_data)

    fig_spend.update_traces(mode='lines+markers')
    fig_spend.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
    fig_spend.update_xaxes(title='Giorno del periodo')
    fig_spend.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Data: %{customdata[1]}<br>Spesa (€): %{y:.2f}<extra></extra>')
    fig_spend.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5
        )
    )

    return fig_spend

def gads_campaign_details(dettaglioCampagne):
    dettaglioCampagne['Spesa'] = dettaglioCampagne['Spesa'].apply(currency)
    dettaglioCampagne['CTR'] = dettaglioCampagne['CTR'].apply(percentage)
    dettaglioCampagne['CPC'] = dettaglioCampagne['CPC'].apply(currency)
    st.dataframe(dettaglioCampagne)

def gads_analysis(results, results_comp):
    st.title("Analisi delle campagne Google")

    col1, col2 = st.columns(2)
    with col1:
        gads_metrics(results, results_comp)
    with col2:
        fig_spend = gads_spend_chart(results, results_comp)
        st.plotly_chart(fig_spend)
    
    st.title("Dettaglio delle campagne")
    gads_campaign_details(results['dettaglio_campagne'].copy())

# ------------------------------
#        GOOGLE ANALYTICS
# ------------------------------
def ganalytics_metrics(results, results_comp):
    active_user_delta = get_metric_delta(results["utenti_attivi"], results_comp["utenti_attivi"])
    st.metric("Utenti attivi", thousand_0(results["utenti_attivi"]), active_user_delta)

    col1_1, col1_2, col1_3 = st.columns(3)
    with col1_1:
        sessioni_delta = get_metric_delta(results["sessioni"], results_comp["sessioni"])
        st.metric("Sessioni", thousand_0(results["sessioni"]), sessioni_delta)

        sessions_users_delta = get_metric_delta(results["sessioni_per_utente"], results_comp["sessioni_per_utente"])
        st.metric("Sessioni per utente attivo", thousand_2(results["sessioni_per_utente"]) if results["sessioni_per_utente"] != 0 else "-", sessions_users_delta)

    with col1_2:
        sessioni_engaged_delta = get_metric_delta(results["sessioni_con_engage"], results_comp["sessioni_con_engage"])
        st.metric("Sessioni con engage", thousand_0(results["sessioni_con_engage"]), sessioni_engaged_delta)

        durata_sessione_delta = get_metric_delta(results["durata_sessioni"], results_comp["durata_sessioni"])
        st.metric("Durata media sessione (sec)", thousand_2(results["durata_sessioni"]) if results["durata_sessioni"] != 0 else "-", durata_sessione_delta)

    with col1_3:
        engage_rate_delta = get_metric_delta(results["tasso_engage"], results_comp["tasso_engage"])
        st.metric("Tasso di engage", percentage(results["tasso_engage"]) if results["tasso_engage"] != 0 else "-", engage_rate_delta)

        tempo_user_delta = get_metric_delta(results["durata_utente"], results_comp["durata_utente"])
        st.metric("Tempo per utente (sec)", thousand_2(results["durata_utente"]) if results["durata_utente"] != 0 else "-", tempo_user_delta)

def ganalytics_users_chart(results, results_comp):
    daily_users_current = results['utenti_attivi_giornalieri']
    daily_users_comp = results_comp['utenti_attivi_giornalieri']

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

    fig_users = px.line(combined_users, x='day', y='active_users', color='period',
                title='Utenti attivi',
                markers=True,
                labels={'day': 'Giorno relativo al periodo', 'active_users': 'Utenti attivi', 'period': 'Periodo', 'date': 'Data'},
                color_discrete_map=color_map,
                hover_data=hover_data)

    fig_users.update_traces(mode='lines+markers')
    fig_users.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
    fig_users.update_traces(
        hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Utenti attivi: %{y:.0f}<extra></extra>'
    )
    fig_users.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig_users)
    
def ganalytics_session_distribution(results):
    session_df = results['sessioni_distribuzione']
    source_session_soglia = 3.00
    main_groups = session_df[session_df['percentage'] >= source_session_soglia].copy()

    fig_session_pie = px.pie(main_groups, values='sessions', names='source_group', title='Distribuzione delle sessioni per fonte')

    fig_session_pie.update_traces(
        hovertemplate='Fonte: %{label}<br>Sessioni: %{value}<extra></extra>'
    )

    st.plotly_chart(fig_session_pie)
    st.write(f'Valore di soglia: {source_session_soglia}%')

def ganalytics_campaign_distribution(results):
    campaign_sessions = results['campagne_distribuzione']
    campaign_session_soglia = 3.00
    main_groups = campaign_sessions[campaign_sessions['percentage'] >= campaign_session_soglia].copy()

    fig_campaign = px.pie(main_groups, values='sessions', names='campaign', title='Distribuzione delle sessioni per campagna')

    fig_campaign.update_traces(
        hovertemplate='Campagna: %{label}<br>Sessioni: %{value}<extra></extra>'
    )

    st.plotly_chart(fig_campaign)
    st.write(f'Valore di soglia: {campaign_session_soglia}%')

def ganalytics_analysis(results, results_comp):
    st.title("Analisi del traffico")

    col1, col2 = st.columns(2)
    with col1:
        ganalytics_metrics(results, results_comp)
    with col2:
        fig_users = ganalytics_users_chart(results, results_comp)

    st.title("Analisi del traffico")

    col3, col4 = st.columns(2)

    with col3:
        ganalytics_session_distribution(results)
    with col4:
        ganalytics_campaign_distribution(results)