import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta

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