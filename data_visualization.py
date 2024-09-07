import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta, process_daily_data

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
    daily_spend_current = process_daily_data(results, 'Periodo Corrente', 'spesa_giornaliera')
    daily_spend_comp = process_daily_data(results_comp, 'Periodo Precedente', 'spesa_giornaliera')

    daily_spend_current['day'] = (daily_spend_current['date'] - daily_spend_current['date'].min()).dt.days
    daily_spend_comp['day'] = (daily_spend_comp['date'] - daily_spend_comp['date'].min()).dt.days

    combined_spend = pd.concat([daily_spend_comp, daily_spend_current])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }

    hover_data = {
        'period': True,
        'date': True,
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
    fig_spend.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Spesa (€): %{y:.2f}<extra></extra>')
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
        try:
            meta_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche Meta: {str(e)}")
    with col2:
        try:
            fig_spend = meta_spend_chart(results, results_comp)
            st.plotly_chart(fig_spend)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico sulla spesa di Meta: {str(e)}")

    st.title("Dettaglio delle campagne")

    try:
        meta_campaign_details(results['dettaglio_campagne'].copy())
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione delle campagne su Meta: {str(e)}")

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
    daily_spend_current = process_daily_data(results, 'Periodo Corrente', 'spesa_giornaliera')
    daily_spend_comp = process_daily_data(results_comp, 'Periodo Precedente', 'spesa_giornaliera')

    daily_spend_current['day'] = (daily_spend_current['date'] - daily_spend_current['date'].min()).dt.days
    daily_spend_comp['day'] = (daily_spend_comp['date'] - daily_spend_comp['date'].min()).dt.days

    combined_spend = pd.concat([daily_spend_comp, daily_spend_current])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }

    hover_data = {
        'period': True,
        'date': True,
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
    fig_spend.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Spesa (€): %{y:.2f}<extra></extra>')
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
        try:
            gads_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche Google Ads: {str(e)}")
    with col2:
        try:
            fig_spend = gads_spend_chart(results, results_comp)
            st.plotly_chart(fig_spend)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico sulla spesa di Google Ads: {str(e)}")
    
    st.title("Dettaglio delle campagne")

    try:
        gads_campaign_details(results['dettaglio_campagne'].copy())
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione delle campange su Google Ads: {str(e)}")

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
    daily_users_current = process_daily_data(results, 'Periodo Corrente', 'utenti_attivi_giornalieri')
    daily_users_comp = process_daily_data(results_comp, 'Periodo Precedente', 'utenti_attivi_giornalieri')

    daily_users_current['day'] = (daily_users_current['date'] - daily_users_current['date'].min()).dt.days
    daily_users_comp['day'] = (daily_users_comp['date'] - daily_users_comp['date'].min()).dt.days

    combined_users = pd.concat([daily_users_comp, daily_users_current])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }

    hover_data = {
        'period': True,
        'date': True,
        'active_users': ':.0f',
        'day': False
    }

    fig_users = px.line(combined_users, x='day', y='active_users', color='period',
                title='Utenti attivi giornalieri',
                markers=True,
                labels={'day': 'Giorno relativo al periodo', 'active_users': 'Utenti attivi', 'period': 'Periodo'},
                color_discrete_map=color_map,
                hover_data=hover_data)

    fig_users.update_traces(mode='lines+markers')
    fig_users.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
    fig_users.update_xaxes(title='Giorno del periodo')
    fig_users.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Utenti attivi: %{y:.0f}<extra></extra>')
    fig_users.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5
        )
    )

    return fig_users
    
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
        try:
            ganalytics_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche Google Analytics: {str(e)}")
    with col2:
        try:
            fig_users = ganalytics_users_chart(results, results_comp)
            st.plotly_chart(fig_users)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico degli utenti attivi su Google Analytics: {str(e)}")

    st.title("Analisi del traffico")

    col3, col4 = st.columns(2)

    with col3:
        try:
            ganalytics_session_distribution(results)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico della distribuzione delle sessioni su Google Analytics: {str(e)}")
    with col4:
        try:
            ganalytics_campaign_distribution(results)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico della distribuzione delle campagne su Google Analytics: {str(e)}")

# ------------------------------
#             LEAD
# ------------------------------
def lead_metrics(results, results_comp):
    leadDaQualificare_delta = get_metric_delta(results["lead_da_qualificare"], results_comp["lead_da_qualificare"])
    st.metric("Lead da qualificare", results["lead_da_qualificare"], leadDaQualificare_delta)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        leadQualificati_delta = get_metric_delta(results["lead_qualificati"], results_comp["lead_qualificati"])
        st.metric("Lead qualificati", results["lead_qualificati"], leadQualificati_delta)

        leadVinti_delta = get_metric_delta(results["vendite"], results_comp["vendite"])
        st.metric("Vendite", results["vendite"], leadVinti_delta)
    with col2:
        leadQualificatiGiorno_delta = get_metric_delta(results["lead_qualificati_giorno_metrics"], results_comp["lead_qualificati_giorno_metrics"])
        st.metric("Lead qualificati al giorno", thousand_2(results["lead_qualificati_giorno_metrics"]), leadQualificatiGiorno_delta)

        vintiPerGiorno_delta = get_metric_delta(results["vinti_giorno_metrics"], results_comp["vinti_giorno_metrics"])
        st.metric("Vendite al giorno", thousand_2(results["vinti_giorno_metrics"]), vintiPerGiorno_delta)
    with col3:
        tassoQualifica_delta = get_metric_delta(results["tasso_qualifica"], results_comp["tasso_qualifica"])
        st.metric("Tasso di qualifica", percentage(results["tasso_qualifica"]) if results["tasso_qualifica"] != 0 else "-", tassoQualifica_delta)

        tassoVendita_delta = get_metric_delta(results["tasso_vendita"], results_comp["tasso_vendita"])
        st.metric("Tasso di vendita", percentage(results["tasso_vendita"]) if results["tasso_vendita"] != 0 else "-", tassoVendita_delta)

def lead_qualificati_chart(results, results_comp):
    daily_qualificati_current = results['lead_qualificati_giorno']
    daily_qualificati_comp = results_comp['lead_qualificati_giorno']

    daily_qualificati_current['date'] = pd.to_datetime(daily_qualificati_current['date'])
    daily_qualificati_comp['date'] = pd.to_datetime(daily_qualificati_comp['date'])

    daily_qualificati_current['day'] = (daily_qualificati_current['date'] - daily_qualificati_current['date'].min()).apply(lambda x: x.days)
    daily_qualificati_comp['day'] = (daily_qualificati_comp['date'] - daily_qualificati_comp['date'].min()).apply(lambda x: x.days)

    daily_qualificati_current['period'] = 'Periodo Corrente'
    daily_qualificati_comp['period'] = 'Periodo Precedente'

    combined_qualificati = pd.concat([daily_qualificati_comp, daily_qualificati_current])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }

    hover_data = {
        'period': True,
        'date': '|%d/%m/%Y',
        'count': ':.0f',
        'day': False
    }

    fig_qualificati = px.line(combined_qualificati, x='day', y='count', color='period',
                title='Lead qualificati',
                markers=True,
                labels={'day': 'Giorno relativo al periodo', 'count': 'Lead qualificati', 'period': 'Periodo', 'date': 'Data'},
                color_discrete_map=color_map,
                hover_data=hover_data)

    fig_qualificati.update_traces(mode='lines+markers')
    fig_qualificati.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
    fig_qualificati.update_traces(
        hovertemplate='<b>Periodo: %{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Lead qualificati: %{y:.0f}<extra></extra>'
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

def lead_analysis(results, results_comp):
    st.title("Stato dei lead")

    col1, col2 = st.columns(2)
    with col1:
        try:
            lead_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche dei lead: {str(e)}")
    with col2:
        try:
            lead_qualificati_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico dei lead qualificati: {str(e)}")

# ------------------------------
#           PERFORMANCE
# ------------------------------
def performance_lead_qualificati_chart(results, results_comp):
    lqPerDay_delta = (results['lead_qualificati_giorno_metrics'] - results_comp['lead_qualificati_giorno_metrics']) / results_comp['lead_qualificati_giorno_metrics'] * 100 if results_comp['lead_qualificati_giorno_metrics'] != 0 else 0
    deltaColor_lqperday = "green" if lqPerDay_delta >= 0 else "red"

    fig_lqperday = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(results['lead_qualificati_giorno_metrics'])/12*100,
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

def performance_vendite_chart(results, results_comp):
    vintiPerDay_delta = (results["vinti_giorno_metrics"] - results_comp["vinti_giorno_metrics"]) / results_comp["vinti_giorno_metrics"] * 100 if results_comp["vinti_giorno_metrics"] != 0 else 0
    deltaColor_vintiperday = "green" if vintiPerDay_delta >= 0 else "red"

    fig_vintiperday = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(results["vinti_giorno_metrics"])/3*100,
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

def performance_bleed_out_lead(results, results_comp):
    st.subheader("Bleed out dei lead")

    opportunitàPerse_df = results['opportunità_perse']
    st.dataframe(opportunitàPerse_df.style.hide(axis='index'))

def performance_analysis(results, results_comp):
    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            performance_lead_qualificati_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico dei lead qualificati: {str(e)}")
    with col2:
        try:
            performance_vendite_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico delle vendite: {str(e)}")
    with col3:
        st.markdown("""
        <hr style="height:0px;border-width: 0px;;margin-top:35px;">
        """, unsafe_allow_html=True)

        try:
            performance_bleed_out_lead(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico dei lead persi: {str(e)}")

# ------------------------------
#         OPPORTUNITIES
# ------------------------------
def opp_metrics(results, results_comp):
    opp_delta = get_metric_delta(results["totali"], results_comp["totali"])
    st.metric("Opportunità", results["totali"], opp_delta)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        setting_delta = get_metric_delta(results["lead_da_qualificare"], results_comp["lead_da_qualificare"])
        st.metric("Setting - Da gestire", thousand_0(results["lead_da_qualificare"]), setting_delta)

        settingPersi_delta = get_metric_delta(results["setting_persi"], results_comp["setting_persi"])
        st.metric("Setting - Persi", thousand_0(results["setting_persi"]), settingPersi_delta)
    with col2:
        vendite_delta = get_metric_delta(results["vendite_gestione"], results_comp["vendite_gestione"])
        st.metric("Vendita - Da gestire", thousand_0(results["vendite_gestione"]), vendite_delta)

        chiusura_delta = get_metric_delta(results["vendite_da_chiudere"], results_comp["vendite_da_chiudere"])
        st.metric("Vendita - Da chiudere", thousand_0(results["vendite_da_chiudere"]), chiusura_delta)
    with col3:
        vinti_delta = get_metric_delta(results["vendite"], results_comp["vendite"])
        st.metric("Vinti", thousand_0(results["vendite"]), vinti_delta)

        persi_delta = get_metric_delta(results["persi"], results_comp["persi"])
        st.metric("Persi", thousand_0(results["persi"]), persi_delta)

def opp_per_giorno_chart(results, results_comp):
    opp_per_giorno = results['opp_per_giorno']
    opp_per_giorno_comp = results_comp['opp_per_giorno']

    opp_per_giorno['date'] = pd.to_datetime(opp_per_giorno['date'])
    opp_per_giorno_comp['date'] = pd.to_datetime(opp_per_giorno_comp['date'])

    opp_per_giorno['day'] = (opp_per_giorno['date'] - opp_per_giorno['date'].min()).apply(lambda x: x.days)
    opp_per_giorno_comp['day'] = (opp_per_giorno_comp['date'] - opp_per_giorno_comp['date'].min()).apply(lambda x: x.days)

    opp_per_giorno['period'] = 'Periodo Corrente'
    opp_per_giorno_comp['period'] = 'Periodo Precedente'

    combined_opp = pd.concat([opp_per_giorno, opp_per_giorno_comp])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }
    
    hover_data = {
        'period': True,
        'date': '|%d/%m/%Y',
        'count': ':.0f',
        'day': False
    }
    
    fig_opp = px.line(combined_opp, x='day', y='count', color='period',
                title='Opportunità per giorno',
                markers=True,
                labels={'day': 'Giorno relativo al periodo', 'count': 'Numero di Opportunità', 'period': 'Periodo', 'date': 'Data'},
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

def opp_analysis(results, results_comp):
    st.title("Gestione delle opportunità")

    col1, col2 = st.columns(2)
    with col1:
        try:
            opp_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche delle opportunità: {str(e)}")
    with col2:
        try:
            opp_per_giorno_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico delle opportunità per giorno: {str(e)}")

# ------------------------------
#           ECONOMICS
# ------------------------------
def economics_metrics(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp):
    spesa_tot = meta_results['spesa_totale'] + gads_results['spesa_totale']
    spesa_tot_comp = meta_results_comp['spesa_totale'] + gads_results_comp['spesa_totale']
    spesa_tot_delta = get_metric_delta(spesa_tot, spesa_tot_comp)
    st.metric("Spesa pubblicitaria", currency(spesa_tot), spesa_tot_delta)
    
    col1_1, col1_2, col1_3 = st.columns(3)
    with col1_1:
        costo_per_lead = spesa_tot / opp_results['totali'] if opp_results['totali'] > 0 else 0
        costo_per_lead_comp = spesa_tot_comp / opp_results_comp['totali'] if opp_results_comp['totali'] > 0 else 0
        costo_per_lead_delta = get_metric_delta(costo_per_lead, costo_per_lead_comp)
        st.metric("Costo per lead", currency(costo_per_lead) if costo_per_lead != 0 else "-", costo_per_lead_delta)
    with col1_2:
        costo_per_lead_qual = spesa_tot / opp_results['lead_qualificati'] if opp_results['lead_qualificati'] > 0 else 0
        costo_per_lead_qual_comp = spesa_tot_comp / opp_results_comp['lead_qualificati'] if opp_results_comp['lead_qualificati'] > 0 else 0
        costo_per_lead_qual_delta = get_metric_delta(costo_per_lead_qual, costo_per_lead_qual_comp)
        st.metric("Costo per lead qualificato", currency(costo_per_lead_qual) if costo_per_lead_qual != 0 else "-", costo_per_lead_qual_delta)
    with col1_3:
        costo_per_vendita = spesa_tot / opp_results['vendite'] if opp_results['vendite'] > 0 else 0
        costo_per_vendita_comp = spesa_tot_comp / opp_results_comp['vendite'] if opp_results_comp['vendite'] > 0 else 0
        costo_per_vendita_delta = get_metric_delta(costo_per_vendita, costo_per_vendita_comp)
        st.metric("Costo per vendita", currency(costo_per_vendita) if costo_per_vendita != 0 else "-", costo_per_vendita_delta)
    
    col1_4, col1_5 = st.columns(2)
    with col1_4:
        incasso = opp_results['incasso']
        incasso_comp = opp_results_comp['incasso']
        incasso_delta = get_metric_delta(incasso, incasso_comp)
        st.metric("Fatturato", currency(incasso), incasso_delta)
    with col1_5:
        roi = (incasso - spesa_tot) / spesa_tot * 100 if spesa_tot > 0 else 0
        roi_comp = (incasso_comp - spesa_tot_comp) / spesa_tot_comp * 100 if spesa_tot_comp > 0 else 0
        roi_delta = get_metric_delta(roi, roi_comp)
        st.metric("ROI", percentage(roi) if roi != 0 else "-", roi_delta)

def economics_analysis(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp):
    st.title("Performance economiche")

    col1, col2 = st.columns(2)
    with col1:
        try:
            economics_metrics(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche economiche: {str(e)}")
    with col2:
        a = 0
