import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_manipulation import currency, percentage, thousand_0, thousand_2, get_metric_delta, display_metric, process_daily_data

# ------------------------------
#             META
# ------------------------------
def meta_metrics(results, results_comp):
    spesa_totale_delta = get_metric_delta(results["spesa_totale"], results_comp["spesa_totale"])
    display_metric("Spesa totale", currency(results["spesa_totale"]), spesa_totale_delta)

    col1, col2, col3 = st.columns(3)
    with col1:
        campagne_attive_delta = get_metric_delta(results["campagne_attive"], results_comp["campagne_attive"])
        display_metric("Campagne attive", results["campagne_attive"], campagne_attive_delta)

        cpm_delta = get_metric_delta(results["cpm"], results_comp["cpm"])
        display_metric("CPM", currency(results["cpm"]) if results["cpm"] != 0 else "-", cpm_delta, is_delta_inverse=True)
    with col2:
        impression_delta = get_metric_delta(results["impression"], results_comp["impression"])
        display_metric("Impression", thousand_0(results["impression"]), impression_delta)

        ctr_delta = get_metric_delta(results["ctr"], results_comp["ctr"])
        display_metric("CTR", percentage(results["ctr"]) if results["ctr"] != 0 else "-", ctr_delta)
    with col3:
        click_delta = get_metric_delta(results["click"], results_comp["click"])
        display_metric("Click", thousand_0(results["click"]), click_delta)

        cpc_delta = get_metric_delta(results["cpc"], results_comp["cpc"])
        display_metric("CPC", currency(results["cpc"]) if results["cpc"] != 0 else "-", cpc_delta, is_delta_inverse=True)

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

    st.plotly_chart(fig_spend)

def meta_attribution_metrics(results, results_comp, attribution_results, attribution_results_comp):
    col1, col2, col3 = st.columns(3)
    with col1:
        attribution_delta = get_metric_delta(attribution_results["lead_meta"], attribution_results_comp["lead_meta"])
        display_metric("Lead Meta", attribution_results["lead_meta"], attribution_delta)

        cpl = results["spesa_totale"] / attribution_results["lead_meta"] if attribution_results["lead_meta"] != 0 else 0
        cpl_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_meta"] if attribution_results_comp["lead_meta"] != 0 else 0
        cpl_delta = get_metric_delta(cpl, cpl_comp)
        display_metric("Cpl", currency(cpl), cpl_delta, is_delta_inverse=True)
    with col2:
        attribution_qualificati_delta = get_metric_delta(attribution_results["lead_meta_qualificati"], attribution_results_comp["lead_meta_qualificati"])
        display_metric("Lead Meta Qualificati", attribution_results["lead_meta_qualificati"], attribution_qualificati_delta)

        cpl_qualificati = results["spesa_totale"] / attribution_results["lead_meta_qualificati"] if attribution_results["lead_meta_qualificati"] != 0 else 0
        cpl_qualificati_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_meta_qualificati"] if attribution_results_comp["lead_meta_qualificati"] != 0 else 0
        cpl_qualificati_delta = get_metric_delta(cpl_qualificati, cpl_qualificati_comp)
        display_metric("Cpl Qualificati", currency(cpl_qualificati), cpl_qualificati_delta, is_delta_inverse=True)
    with col3:
        attribution_vinti_delta = get_metric_delta(attribution_results["lead_meta_vinti"], attribution_results_comp["lead_meta_vinti"])
        display_metric("Lead Meta Vinti", attribution_results["lead_meta_vinti"], attribution_vinti_delta)

        cpl_vinti = results["spesa_totale"] / attribution_results["lead_meta_vinti"] if attribution_results["lead_meta_vinti"] != 0 else 0
        cpl_vinti_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_meta_vinti"] if attribution_results_comp["lead_meta_vinti"] != 0 else 0
        cpl_vinti_delta = get_metric_delta(cpl_vinti, cpl_vinti_comp)
        display_metric("Cpl Vinti", currency(cpl_vinti), cpl_vinti_delta, is_delta_inverse=True)

def meta_age_analysis(results):
    age_data = results['age_data']
    
    if age_data is None:
        st.error("Dati sull'età non disponibili.")
        return

    required_columns = ['age', 'outbound_clicks_outbound_click', 'actions_lead', 'actions_purchase']
    for col in required_columns:
        if col not in age_data.columns:
            st.error(f"Colonna mancante nei dati: {col}")
            return

    fascia_selezionata = st.selectbox("Seleziona la Fascia d'Età", age_data['age'].unique())

    dati_fascia = age_data[age_data['age'] == fascia_selezionata].iloc[0]

    fig = go.Figure(go.Funnel(
        y=["Click", "Lead", "Acquisto"],
        x=[dati_fascia['outbound_clicks_outbound_click'], dati_fascia['actions_lead'], dati_fascia['actions_purchase']],
        marker=dict(color=["#636EFA", "#EF553B", "#00CC96"]),
        textinfo="value+percent initial",
        opacity=0.9
    ))

    fig.update_layout(
        title_text=f"Funnel per Fascia d'Età: {fascia_selezionata}",
        funnelmode="stack",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

def meta_campaign_details(dettaglioCampagne):
    if dettaglioCampagne is None:
        st.error("Dati dettaglio campagne non disponibili.")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        campaigns = dettaglioCampagne['Campagna'].unique().tolist()
        campagne_campaign_filter = st.multiselect(
            "Seleziona le campagne",
            options=campaigns,
            default=[],
            key='campagne_campaign_filter',
            placeholder='Seleziona le campagne'
        )

        campaigns_selected = len(campagne_campaign_filter) > 0

        avec_col2 = col2.empty()
        avec_col3 = col3.empty()

    filtra_dettaglioCampagne = dettaglioCampagne.copy()

    if campaigns_selected:
        filtra_dettaglioCampagne = filtra_dettaglioCampagne[filtra_dettaglioCampagne['Campagna'].isin(campagne_campaign_filter)]
    
    filtra_dettaglioCampagne = filtra_dettaglioCampagne.sort_values(by='Spesa', ascending=False).reset_index(drop=True)
    
    if filtra_dettaglioCampagne.empty:
        st.warning("Nessun record trovato per i filtri selezionati.")
    else:
        st.dataframe(filtra_dettaglioCampagne,
            use_container_width=True,
            column_config={
                "Spesa": st.column_config.NumberColumn(
                    "Spesa",
                    format="€ %.2f"),
                "CTR": st.column_config.NumberColumn(
                    "CTR",
                    help="Click-Through Rate",
                    format="%.2f%%"),
                "CPC": st.column_config.NumberColumn(
                    "CPC",
                    help="Costo per click",
                    format="€ %.2f"),
                "CPL": st.column_config.NumberColumn(
                    "CPL",
                    help="Costo per lead",
                    format="€ %.2f"),
                "CPA": st.column_config.NumberColumn(
                    "CPA",
                    help="Costo per acquisizione",
                    format="€ %.2f")
            },
            column_order=[
                "Adset",
                "Stato",
                "Spesa",
                "Impression",
                "Click",
                "CTR",
                "CPC",
                "Lead",
                "CPL",
                "Vendite",
                "CPA"
            ],
            hide_index=True)

def meta_ad_details(dettaglioAd):
    if dettaglioAd is None:
        st.error("Dati dettaglio ad non disponibili.")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        campaigns = dettaglioAd['Campagna'].unique().tolist()
        campaign_filter = st.multiselect(
            "Seleziona le campagne",
            options=campaigns,
            default=[],
            key='ad_campaign_filter',
            placeholder='Seleziona le campagne'
        )

        campaigns_selected = len(campaign_filter) > 0
        if campaigns_selected:
            filtered_adsets = dettaglioAd[dettaglioAd['Campagna'].isin(campaign_filter)]['Adset'].unique().tolist()
            
            with col2:
                ad_adset_filter = st.multiselect(
                    "Seleziona gli adset",
                    options=filtered_adsets,
                    default=[],
                    key='ad_adset_filter',
                    placeholder='Seleziona gli adset'
                )
        else:
            avec_col2 = col2.empty()
            avec_col3 = col3.empty()

            ad_adset_filter = []

    filtra_dettaglioAd = dettaglioAd.copy()
    
    if campaigns_selected:
        filtra_dettaglioAd = filtra_dettaglioAd[filtra_dettaglioAd['Campagna'].isin(campaign_filter)]
    
    if 'ad_adset_filter' in locals() and len(ad_adset_filter) > 0:
        filtra_dettaglioAd = filtra_dettaglioAd[filtra_dettaglioAd['Adset'].isin(ad_adset_filter)]
    
    filtra_dettaglioAd = filtra_dettaglioAd.sort_values(by='Spesa', ascending=False).reset_index(drop=True)
    
    if filtra_dettaglioAd.empty:
        st.warning("Nessun record trovato per i filtri selezionati.")
    else:
        st.dataframe(filtra_dettaglioAd,
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link",
                    display_text="Link"
                ),
                "Spesa": st.column_config.NumberColumn(
                    "Spesa",
                    format="€ %.2f"),
                "CTR": st.column_config.NumberColumn(
                    "CTR",
                    help="Click-Through Rate",
                    format="%.2f%%"),
                "CPC": st.column_config.NumberColumn(
                    "CPC",
                    help="Costo per click",
                    format="€ %.2f"),
                "CPL": st.column_config.NumberColumn(
                    "CPL",
                    help="Costo per lead",
                    format="€ %.2f"),
                "CPA": st.column_config.NumberColumn(
                    "CPA",
                    help="Costo per acquisizione",
                    format="€ %.2f")
            },
            column_order=[
                "Ad",
                "Stato",
                "Link",
                "Spesa",
                "Impression",
                "Click",
                "CTR",
                "CPC",
                "Lead",
                "CPL",
                "Vendite",
                "CPA"
            ],
            use_container_width=True,
            hide_index=True)

def meta_analysis(results, results_comp, attribution_results, attribution_results_comp):
    st.title("Analisi delle campagne Meta")

    col1, col2 = st.columns(2)
    with col1:
        try:
            meta_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche Meta: {str(e)}")
    with col2:
        try:
            meta_spend_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico sulla spesa di Meta: {str(e)}")
    
    st.title("Analisi delle attribuzioni Meta")

    col3, col4 = st.columns(2)
    with col3:
        try:
            meta_attribution_metrics(results, results_comp, attribution_results, attribution_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche di attribuzione di Meta: {str(e)}")
    with col4:
        pass

    st.title("Analisi demografica")

    col5, col6 = st.columns(2)
    with col5:
        try:
            meta_age_analysis(results)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione dell'analisi dell'età di Meta: {str(e)}")
    with col6:
        pass

    st.title("Dettaglio delle campagne")

    try:
        meta_campaign_details(results['dettaglio_campagne'].copy())
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione delle campagne su Meta: {str(e)}")

    st.title("Dettaglio degli annunci")

    try:
        meta_ad_details(results['dettaglio_ad'].copy())
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione degli annunci su Meta: {str(e)}")

# ------------------------------
#           GOOGLE ADS
# ------------------------------
def gads_metrics(results, results_comp):
    spesaTot_delta = get_metric_delta(results["spesa_totale"], results_comp["spesa_totale"])
    display_metric("Spesa totale", currency(results["spesa_totale"]), spesaTot_delta)

    col1, col2, col3 = st.columns(3)
    with col1:
        campagne_delta = get_metric_delta(results["campagne_attive"], results_comp["campagne_attive"])
        display_metric("Campagne attive", results["campagne_attive"], campagne_delta)

        cpm_delta = get_metric_delta(results["cpm"], results_comp["cpm"])
        display_metric("CPM", currency(results["cpm"]) if results["cpm"] != 0 else "-", cpm_delta, is_delta_inverse=True)

    with col2:
        impression_delta = get_metric_delta(results["impression"], results_comp["impression"])
        display_metric("Impression", thousand_0(results["impression"]), impression_delta)

        ctr_delta = get_metric_delta(results["ctr"], results_comp["ctr"])
        display_metric("CTR", percentage(results["ctr"]) if results["ctr"] != 0 else "-", ctr_delta)

    with col3:
        click_delta = get_metric_delta(results["click"], results_comp["click"])
        display_metric("Click", thousand_0(results["click"]), click_delta)

        cpc_delta = get_metric_delta(results["cpc"], results_comp["cpc"])
        display_metric("CPC", currency(results["cpc"]) if results["cpc"] != 0 else "-", cpc_delta, is_delta_inverse=True)

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

    st.plotly_chart(fig_spend)

def gads_attribution_metrics(results, results_comp, attribution_results, attribution_results_comp):
    col1, col2, col3 = st.columns(3)
    with col1:
        attribution_delta = get_metric_delta(attribution_results["lead_google"], attribution_results_comp["lead_google"])
        display_metric("Lead Google", attribution_results["lead_google"], attribution_delta)

        cpl = results["spesa_totale"] / attribution_results["lead_google"] if attribution_results["lead_google"] != 0 else 0
        cpl_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_google"] if attribution_results_comp["lead_google"] != 0 else 0
        cpl_delta = get_metric_delta(cpl, cpl_comp)
        display_metric("Cpl", currency(cpl), cpl_delta, is_delta_inverse=True)
    with col2:
        attribution_qualificati_delta = get_metric_delta(attribution_results["lead_google_qualificati"], attribution_results_comp["lead_google_qualificati"])
        display_metric("Lead Google Qualificati", attribution_results["lead_google_qualificati"], attribution_qualificati_delta)

        cpl_qualificati = results["spesa_totale"] / attribution_results["lead_google_qualificati"] if attribution_results["lead_google_qualificati"] != 0 else 0
        cpl_qualificati_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_google_qualificati"] if attribution_results_comp["lead_google_qualificati"] != 0 else 0
        cpl_qualificati_delta = get_metric_delta(cpl_qualificati, cpl_qualificati_comp)
        display_metric("Cpl Qualificati", currency(cpl_qualificati), cpl_qualificati_delta, is_delta_inverse=True)
    with col3:
        attribution_vinti_delta = get_metric_delta(attribution_results["lead_google_vinti"], attribution_results_comp["lead_google_vinti"])
        display_metric("Lead Google Vinti", attribution_results["lead_google_vinti"], attribution_vinti_delta)

        cpl_vinti = results["spesa_totale"] / attribution_results["lead_google_vinti"] if attribution_results["lead_google_vinti"] != 0 else 0
        cpl_vinti_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_google_vinti"] if attribution_results_comp["lead_google_vinti"] != 0 else 0
        cpl_vinti_delta = get_metric_delta(cpl_vinti, cpl_vinti_comp)
        display_metric("Cpl Vinti", currency(cpl_vinti), cpl_vinti_delta, is_delta_inverse=True)

def gads_campaign_details(dettaglioCampagne):
    dettaglioCampagne = dettaglioCampagne.sort_values(by='Spesa', ascending=False).reset_index(drop=True)

    st.dataframe(dettaglioCampagne, use_container_width=True)

def gads_keyword_details(dettaglioKeyword):
    dettaglioKeyword = dettaglioKeyword.sort_values(by='Spesa', ascending=False).reset_index(drop=True)

    dettaglioKeyword['Spesa'] = dettaglioKeyword['Spesa'].apply(currency)
    dettaglioKeyword['CTR'] = dettaglioKeyword['CTR'].apply(percentage)
    dettaglioKeyword['CPC'] = dettaglioKeyword['CPC'].apply(currency)
    st.dataframe(dettaglioKeyword, use_container_width=True)

def gads_analysis(results, results_comp, attribution_results, attribution_results_comp):
    st.title("Analisi delle campagne Google")

    col1, col2 = st.columns(2)
    with col1:
        try:
            gads_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche Google Ads: {str(e)}")
    with col2:
        try:
            gads_spend_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico sulla spesa di Google Ads: {str(e)}")

    st.title("Analisi delle attribuzioni Google")

    col3, col4 = st.columns(2)
    with col3:
        try:
            gads_attribution_metrics(results, results_comp, attribution_results, attribution_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche di attribuzione di Google Ads: {str(e)}")
    with col4:
        pass
    
    st.title("Dettaglio delle campagne")

    try:
        gads_campaign_details(results['dettaglio_campagne'].copy())
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione delle campange su Google Ads: {str(e)}")

    st.title("Dettaglio delle keyword")

    try:
        gads_keyword_details(results['dettaglio_keyword'].copy())
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione delle keyword su Google Ads: {str(e)}")

# ------------------------------
#            TIKTOK
# ------------------------------
def tiktok_metrics(results, results_comp):
    spesa_totale_delta = get_metric_delta(results["spesa_totale"], results_comp["spesa_totale"])
    display_metric("Spesa totale", currency(results["spesa_totale"]), spesa_totale_delta)

    col1, col2, col3 = st.columns(3)
    with col1:
        campagne_attive_delta = get_metric_delta(results["campagne_attive"], results_comp["campagne_attive"])
        display_metric("Campagne attive", results["campagne_attive"], campagne_attive_delta)

        cpm_delta = get_metric_delta(results["cpm"], results_comp["cpm"])
        display_metric("CPM", currency(results["cpm"]) if results["cpm"] != 0 else "-", cpm_delta, is_delta_inverse=True)
    with col2:
        impression_delta = get_metric_delta(results["impression"], results_comp["impression"])
        display_metric("Impression", thousand_0(results["impression"]), impression_delta)

        ctr_delta = get_metric_delta(results["ctr"], results_comp["ctr"])
        display_metric("CTR", percentage(results["ctr"]) if results["ctr"] != 0 else "-", ctr_delta)
    with col3:
        click_delta = get_metric_delta(results["click"], results_comp["click"])
        display_metric("Click", thousand_0(results["click"]), click_delta)

        cpc_delta = get_metric_delta(results["cpc"], results_comp["cpc"])
        display_metric("CPC", currency(results["cpc"]) if results["cpc"] != 0 else "-", cpc_delta, is_delta_inverse=True)

def tiktok_spend_chart(results, results_comp):
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

    st.plotly_chart(fig_spend)

def tiktok_attribution_metrics(results, results_comp, attribution_results, attribution_results_comp):
    col1, col2, col3 = st.columns(3)
    with col1:
        attribution_delta = get_metric_delta(attribution_results["lead_tiktok"], attribution_results_comp["lead_tiktok"])
        display_metric("Lead TikTok", attribution_results["lead_tiktok"], attribution_delta)

        cpl = results["spesa_totale"] / attribution_results["lead_tiktok"] if attribution_results["lead_tiktok"] != 0 else 0
        cpl_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_tiktok"] if attribution_results_comp["lead_tiktok"] != 0 else 0
        cpl_delta = get_metric_delta(cpl, cpl_comp)
        display_metric("Cpl", currency(cpl), cpl_delta, is_delta_inverse=True)
    with col2:
        attribution_qualificati_delta = get_metric_delta(attribution_results["lead_tiktok_qualificati"], attribution_results_comp["lead_tiktok_qualificati"])
        display_metric("Lead TikTok Qualificati", attribution_results["lead_tiktok_qualificati"], attribution_qualificati_delta)

        cpl_qualificati = results["spesa_totale"] / attribution_results["lead_tiktok_qualificati"] if attribution_results["lead_tiktok_qualificati"] != 0 else 0
        cpl_qualificati_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_tiktok_qualificati"] if attribution_results_comp["lead_tiktok_qualificati"] != 0 else 0
        cpl_qualificati_delta = get_metric_delta(cpl_qualificati, cpl_qualificati_comp)
        display_metric("Cpl Qualificati", currency(cpl_qualificati), cpl_qualificati_delta, is_delta_inverse=True)
    with col3:
        attribution_vinti_delta = get_metric_delta(attribution_results["lead_tiktok_vinti"], attribution_results_comp["lead_tiktok_vinti"])
        display_metric("Lead TikTok Vinti", attribution_results["lead_tiktok_vinti"], attribution_vinti_delta)

        cpl_vinti = results["spesa_totale"] / attribution_results["lead_tiktok_vinti"] if attribution_results["lead_tiktok_vinti"] != 0 else 0
        cpl_vinti_comp = results_comp["spesa_totale"] / attribution_results_comp["lead_tiktok_vinti"] if attribution_results_comp["lead_tiktok_vinti"] != 0 else 0
        cpl_vinti_delta = get_metric_delta(cpl_vinti, cpl_vinti_comp)
        display_metric("Cpl Vinti", currency(cpl_vinti), cpl_vinti_delta, is_delta_inverse=True)

def tiktok_campaign_details(dettaglioCampagne):
    dettaglioCampagne = dettaglioCampagne.sort_values(by='Spesa', ascending=False).reset_index(drop=True)
    
    st.dataframe(dettaglioCampagne,
        use_container_width=True,
        column_config={
            "Spesa": st.column_config.NumberColumn(
                "Spesa",
                format="€ %.2f"),
            "CTR": st.column_config.NumberColumn(
                "CTR",
                help="Click-Through Rate",
                format="%.2f%%"),
            "CPC": st.column_config.NumberColumn(
                "CPC",
                help="Costo per click",
                format="€ %.2f"),
            "CPL": st.column_config.NumberColumn(
                "CPL",
                help="Costo per lead",
                format="€ %.2f"),
            "CPA": st.column_config.NumberColumn(
                "CPA",
                help="Costo per acquisizione",
                format="€ %.2f")
        },
        hide_index=True)

def tiktok_analysis(results, results_comp, attribution_results, attribution_results_comp):
    st.title("Analisi delle campagne TikTok")

    col1, col2 = st.columns(2)
    with col1:
        try:
            tiktok_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche TikTok: {str(e)}")
    with col2:
        try:
            tiktok_spend_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico sulla spesa di TikTok: {str(e)}")
    
    st.title("Analisi delle attribuzioni TikTok")

    col3, col4 = st.columns(2)
    with col3:
        try:
            tiktok_attribution_metrics(results, results_comp, attribution_results, attribution_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche di attribuzione di TikTok: {str(e)}")
    with col4:
        pass

    st.title("Dettaglio delle campagne")

    try:
        tiktok_campaign_details(results['dettaglio_campagne'].copy())
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione delle campagne su TikTok: {str(e)}")

# ------------------------------
#        GOOGLE ANALYTICS
# ------------------------------
def ganalytics_metrics(results, results_comp):
    active_user_delta = get_metric_delta(results["utenti_attivi"], results_comp["utenti_attivi"])
    display_metric("Utenti attivi", thousand_0(results["utenti_attivi"]), active_user_delta)

    col1_1, col1_2, col1_3 = st.columns(3)
    with col1_1:
        sessioni_delta = get_metric_delta(results["sessioni"], results_comp["sessioni"])
        display_metric("Sessioni", thousand_0(results["sessioni"]), sessioni_delta)

        sessions_users_delta = get_metric_delta(results["sessioni_per_utente"], results_comp["sessioni_per_utente"])
        display_metric("Sessioni per utente attivo", thousand_2(results["sessioni_per_utente"]) if results["sessioni_per_utente"] != 0 else "-", sessions_users_delta)

    with col1_2:
        sessioni_engaged_delta = get_metric_delta(results["sessioni_con_engage"], results_comp["sessioni_con_engage"])
        display_metric("Sessioni con engage", thousand_0(results["sessioni_con_engage"]), sessioni_engaged_delta)

        durata_sessione_delta = get_metric_delta(results["durata_sessioni"], results_comp["durata_sessioni"])
        display_metric("Durata media sessione (sec)", thousand_2(results["durata_sessioni"]) if results["durata_sessioni"] != 0 else "-", durata_sessione_delta)

    with col1_3:
        engage_rate_delta = get_metric_delta(results["tasso_engage"], results_comp["tasso_engage"])
        display_metric("Tasso di engage", percentage(results["tasso_engage"]) if results["tasso_engage"] != 0 else "-", engage_rate_delta)

        tempo_user_delta = get_metric_delta(results["durata_utente"], results_comp["durata_utente"])
        display_metric("Tempo per utente (sec)", thousand_2(results["durata_utente"]) if results["durata_utente"] != 0 else "-", tempo_user_delta)

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
    st.title("Analisi dell'engagement")

    col1, col2 = st.columns(2)
    with col1:
        try:
            ganalytics_metrics(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche Google Analytics: {str(e)}")
    with col2:
        try:
            ganalytics_users_chart(results, results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico degli utenti attivi su Google Analytics: {str(e)}")

    st.title("Analisi delle sessioni")

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
    display_metric("Lead da qualificare", results["lead_da_qualificare"], leadDaQualificare_delta)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        leadQualificati_delta = get_metric_delta(results["lead_qualificati"], results_comp["lead_qualificati"])
        display_metric("Lead qualificati", results["lead_qualificati"], leadQualificati_delta)

        leadVinti_delta = get_metric_delta(results["vendite"], results_comp["vendite"])
        display_metric("Vendite", results["vendite"], leadVinti_delta)
    with col2:
        leadQualificatiGiorno_delta = get_metric_delta(results["lead_qualificati_giorno_metrics"], results_comp["lead_qualificati_giorno_metrics"])
        display_metric("Lead qualificati al giorno", thousand_2(results["lead_qualificati_giorno_metrics"]), leadQualificatiGiorno_delta)

        vintiPerGiorno_delta = get_metric_delta(results["vinti_giorno_metrics"], results_comp["vinti_giorno_metrics"])
        display_metric("Vendite al giorno", thousand_2(results["vinti_giorno_metrics"]), vintiPerGiorno_delta)
    with col3:
        tassoQualifica_delta = get_metric_delta(results["tasso_qualifica"], results_comp["tasso_qualifica"])
        display_metric("Tasso di qualifica", percentage(results["tasso_qualifica"]) if results["tasso_qualifica"] != 0 else "-", tassoQualifica_delta)

        tassoVendita_delta = get_metric_delta(results["tasso_vendita"], results_comp["tasso_vendita"])
        display_metric("Tasso di vendita", percentage(results["tasso_vendita"]) if results["tasso_vendita"] != 0 else "-", tassoVendita_delta)

def lead_qualificati_chart(results, results_comp):
    daily_qualificati_current = process_daily_data(results, 'Periodo Corrente', 'lead_qualificati_giorno')
    daily_qualificati_comp = process_daily_data(results_comp, 'Periodo Precedente', 'lead_qualificati_giorno')

    daily_qualificati_current['day'] = (daily_qualificati_current['date'] - daily_qualificati_current['date'].min()).dt.days
    daily_qualificati_comp['day'] = (daily_qualificati_comp['date'] - daily_qualificati_comp['date'].min()).dt.days

    combined_qualificati = pd.concat([daily_qualificati_comp, daily_qualificati_current])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }

    hover_data = {
        'period': True,
        'date': True,
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
        pass

# ------------------------------
#         OPPORTUNITIES
# ------------------------------
def opp_metrics(results, results_comp):
    opp_delta = get_metric_delta(results["totali"], results_comp["totali"])
    display_metric("Opportunità", results["totali"], opp_delta)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        setting_delta = get_metric_delta(results["lead_da_qualificare"], results_comp["lead_da_qualificare"])
        display_metric("Setting - Da gestire", thousand_0(results["lead_da_qualificare"]), setting_delta)

        settingPersi_delta = get_metric_delta(results["setting_persi"], results_comp["setting_persi"])
        display_metric("Setting - Persi", thousand_0(results["setting_persi"]), settingPersi_delta)
    with col2:
        vendite_delta = get_metric_delta(results["vendite_gestione"], results_comp["vendite_gestione"])
        display_metric("Vendita - Da gestire", thousand_0(results["vendite_gestione"]), vendite_delta)

        chiusura_delta = get_metric_delta(results["vendite_da_chiudere"], results_comp["vendite_da_chiudere"])
        display_metric("Vendita - Da chiudere", thousand_0(results["vendite_da_chiudere"]), chiusura_delta)
    with col3:
        vinti_delta = get_metric_delta(results["vendite"], results_comp["vendite"])
        display_metric("Vinti", thousand_0(results["vendite"]), vinti_delta)

        persi_delta = get_metric_delta(results["persi"], results_comp["persi"])
        display_metric("Persi", thousand_0(results["persi"]), persi_delta)

def opp_per_giorno_chart(results, results_comp):
    daily_opp_current = process_daily_data(results, 'Periodo Corrente', 'opp_per_giorno')
    daily_opp_comp = process_daily_data(results_comp, 'Periodo Precedente', 'opp_per_giorno')

    daily_opp_current['day'] = (daily_opp_current['date'] - daily_opp_current['date'].min()).dt.days
    daily_opp_comp['day'] = (daily_opp_comp['date'] - daily_opp_comp['date'].min()).dt.days

    combined_opp = pd.concat([daily_opp_comp, daily_opp_current])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }
    
    hover_data = {
        'period': True,
        'date': True,
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
    display_metric("Spesa pubblicitaria", currency(spesa_tot), spesa_tot_delta)
    
    col1_1, col1_2, col1_3 = st.columns(3)
    with col1_1:
        costo_per_lead = spesa_tot / opp_results['totali'] if opp_results['totali'] > 0 else 0
        costo_per_lead_comp = spesa_tot_comp / opp_results_comp['totali'] if opp_results_comp['totali'] > 0 else 0
        costo_per_lead_delta = get_metric_delta(costo_per_lead, costo_per_lead_comp)
        display_metric("Costo per lead", currency(costo_per_lead) if costo_per_lead != 0 else "-", costo_per_lead_delta)
    with col1_2:
        costo_per_lead_qual = spesa_tot / opp_results['lead_qualificati'] if opp_results['lead_qualificati'] > 0 else 0
        costo_per_lead_qual_comp = spesa_tot_comp / opp_results_comp['lead_qualificati'] if opp_results_comp['lead_qualificati'] > 0 else 0
        costo_per_lead_qual_delta = get_metric_delta(costo_per_lead_qual, costo_per_lead_qual_comp)
        display_metric("Costo per lead qualificato", currency(costo_per_lead_qual) if costo_per_lead_qual != 0 else "-", costo_per_lead_qual_delta)
    with col1_3:
        costo_per_vendita = spesa_tot / opp_results['vendite'] if opp_results['vendite'] > 0 else 0
        costo_per_vendita_comp = spesa_tot_comp / opp_results_comp['vendite'] if opp_results_comp['vendite'] > 0 else 0
        costo_per_vendita_delta = get_metric_delta(costo_per_vendita, costo_per_vendita_comp)
        display_metric("Costo per vendita", currency(costo_per_vendita) if costo_per_vendita != 0 else "-", costo_per_vendita_delta)
    
    col1_4, col1_5 = st.columns(2)
    with col1_4:
        incasso = opp_results['incasso']
        incasso_comp = opp_results_comp['incasso']
        incasso_delta = get_metric_delta(incasso, incasso_comp)
        display_metric("Fatturato", currency(incasso), incasso_delta)
    with col1_5:
        roi = (incasso - spesa_tot) / spesa_tot * 100 if spesa_tot > 0 else 0
        roi_comp = (incasso_comp - spesa_tot_comp) / spesa_tot_comp * 100 if spesa_tot_comp > 0 else 0
        roi_delta = get_metric_delta(roi, roi_comp)
        display_metric("ROI", percentage(roi) if roi != 0 else "-", roi_delta)

def economics_fatturato_giornaliero_chart(results, results_comp):
    daily_fatturato_current = process_daily_data(results, 'Periodo Corrente', 'incasso_giorno')
    daily_fatturato_comp = process_daily_data(results_comp, 'Periodo Precedente', 'incasso_giorno')

    daily_fatturato_current['day'] = (daily_fatturato_current['date'] - daily_fatturato_current['date'].min()).dt.days
    daily_fatturato_comp['day'] = (daily_fatturato_comp['date'] - daily_fatturato_comp['date'].min()).dt.days

    combined_fatturato = pd.concat([daily_fatturato_comp, daily_fatturato_current])

    color_map = {
        'Periodo Corrente': '#b12b94',
        'Periodo Precedente': '#eb94d8'
    }

    hover_data = {
        'period': True,
        'date': True,
        'count': ':.2f',
        'day': False
    }

    fig_fatturato = px.line(combined_fatturato, x='day', y='count', color='period',
                title='Fatturato giornaliero',
                markers=True,
                labels={'day': 'Giorno relativo al periodo', 'count': 'Fatturato (€)', 'period': 'Periodo'},
                color_discrete_map=color_map,
                hover_data=hover_data)

    fig_fatturato.update_traces(mode='lines+markers')
    fig_fatturato.update_yaxes(range=[0, None], fixedrange=False, rangemode="tozero")
    fig_fatturato.update_xaxes(title='Giorno del periodo')
    fig_fatturato.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Data: %{customdata[1]|%d/%m/%Y}<br>Fatturato (€): %{y:.2f}<extra></extra>')
    fig_fatturato.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig_fatturato)

def economics_analysis(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp):
    st.title("Performance - Aceleratore d'impresa")

    col1, col2 = st.columns(2)
    with col1:
        try:
            economics_metrics(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche economiche: {str(e)}")
    with col2:
        try:
            economics_fatturato_giornaliero_chart(opp_results, opp_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico del fatturato giornaliero: {str(e)}")

# ------------------------------
#          ATTRIBUTION
# ------------------------------
def attribution_metrics(attribution_results, attribution_results_comp):
    attribution_fonti = [fonte for fonte in attribution_results['lead_fonti'] if fonte is not None]
    attribution_counts = {fonte: attribution_results[fonte] for fonte in sorted(attribution_fonti)}
    
    display_metric("Attribuzioni totali", attribution_results["totali"], get_metric_delta(attribution_results["totali"], attribution_results_comp["totali"]))

    cols = st.columns(3)
    for i, (fonte, count) in enumerate(attribution_counts.items()):
        count_comp = attribution_results_comp.get(fonte, 0)
        delta = get_metric_delta(count, count_comp)
        with cols[i % 3]:
            display_metric(fonte, count, delta)
        if (i + 1) % 3 == 0:
            st.write("")

def attribution_percentage_chart(opp_results, opp_results_comp, attribution_results, attribution_results_comp):
    total_attributions = attribution_results["totali"]
    total_opportunities = opp_results["totali"]

    total_attributions_comp = attribution_results_comp["totali"]
    total_opportunities_comp = opp_results_comp["totali"]

    attribution_ratio = total_attributions / total_opportunities if total_opportunities != 0 else 0
    attribution_ratio_comp = total_attributions_comp / total_opportunities_comp if total_opportunities_comp != 0 else 0

    delta = get_metric_delta(attribution_ratio, attribution_ratio_comp)

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(attribution_ratio) * 100,
        number={'suffix': "%"},
        delta={'reference': attribution_ratio_comp * 100, 'relative': True, 'position': "bottom", 'valueformat': ".2f", 'font': {'size': 16}},
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

    fig_gauge.update_layout(
        title="Percentuale di lead con attribuzione",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig_gauge)

def attribution_analysis(meta_results, meta_results_comp, gads_results, gads_results_comp, opp_results, opp_results_comp, attribution_results, attribution_results_comp):
    st.title("Attribuzione delle opportunità")

    col1, col2 = st.columns(2)
    with col1:
        try:
            attribution_metrics(attribution_results, attribution_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche di attribuzione: {str(e)}")
    with col2:
        try:
            attribution_percentage_chart(opp_results, opp_results_comp, attribution_results, attribution_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione del grafico delle percentuali di attribuzione: {str(e)}")

# ------------------------------
#          ATTRIBUTION
# ------------------------------
def transaction_metrics(transaction_results, transaction_results_comp):
    display_metric("Transazioni totali", currency(transaction_results["transazioni"]), get_metric_delta(transaction_results["transazioni"], transaction_results_comp["transazioni"]))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        display_metric("Prove gratuite", transaction_results["prove_gratuite"], get_metric_delta(transaction_results["prove_gratuite"], transaction_results_comp["prove_gratuite"]))
    with col2:
        display_metric("Abbonamenti mensili", transaction_results["abbonamenti_mensili"], get_metric_delta(transaction_results["abbonamenti_mensili"], transaction_results_comp["abbonamenti_mensili"]))
    with col3:
        display_metric("Abbonamenti annuali", transaction_results["abbonamenti_annuali"], get_metric_delta(transaction_results["abbonamenti_annuali"], transaction_results_comp["abbonamenti_annuali"]))

def transaction_analysis(transaction_results, transaction_results_comp):
    st.title("Analisi delle transazioni")

    col1, col2 = st.columns(2)
    with col1:
        try:
            transaction_metrics(transaction_results, transaction_results_comp)
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione delle metriche delle transazioni: {str(e)}")
    with col2:
        pass

# ------------------------------
#          VENDITORI
# ------------------------------
def leader_board_venditori(opp_results, opp_results_comp):
    col1, col2 = st.columns(2)
    with col1:
        maggior_fatturato = opp_results['vendite_venditore'].loc[opp_results['vendite_venditore']['Fatturato totale'].idxmax()]
        display_metric("Maggior fatturato", f"{maggior_fatturato['Venditore']} ({currency(maggior_fatturato['Fatturato totale'])})", 1)
    with col2:
        maggiori_vendite = opp_results['vendite_venditore'].loc[opp_results['vendite_venditore']['Vendite'].idxmax()]
        display_metric("Maggior numero di vendite", f"{maggiori_vendite['Venditore']} ({maggiori_vendite['Vendite']} vendite)", 1)
    
    col3, col4 = st.columns(2)
    with col3:
        maggior_vendita_media = opp_results['vendite_venditore'].loc[opp_results['vendite_venditore']['Fatturato medio'].idxmax()]
        display_metric("Maggior vendita media", f"{maggior_vendita_media['Venditore']} ({currency(maggior_vendita_media['Fatturato medio'])})", 1)
    with col4:
        display_metric("Maggior tasso di conversione", "-", 1)

    st.subheader("Performance venditori")
    
    st.dataframe(opp_results['vendite_venditore'],
        use_container_width=True,
        column_config={
            "Fatturato totale": st.column_config.NumberColumn(
                "Fatturato totale",
                format="€ %.2f"),
            "Fatturato medio": st.column_config.NumberColumn(
                "Fatturato medio",
                format="€ %.2f")
        },
        hide_index=True)

def venditori_analysis(opp_results, opp_results_comp):
    st.title("Analisi dei venditori")

    leader_board_venditori(opp_results, opp_results_comp)