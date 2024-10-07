import pandas as pd
import streamlit as st
import datetime

from config import STAGES, COMMERCIALI
from db import get_data

class BaseAnalyzer:
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        self.start_date = start_date
        self.end_date = end_date
        self.comparison_start = comparison_start
        self.comparison_end = comparison_end

class MetaAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
    
    def clean_data(self, df):
        return df.loc[
            (df["account_id"] == st.secrets["facebook_account_id"]) &
            (~df["campaign"].str.contains(r"\[HR\]")) &
            (~df["campaign"].str.contains(r"DENTALAI"))
        ]
    
    def aggregate_results(self, df, is_comparison=False):
        aggregate_results = {
            'start_date': self.comparison_start if is_comparison else self.start_date,
            'end_date': self.comparison_end if is_comparison else self.end_date,
            'spesa_totale': df["spend"].sum(),
            'impression': df["impressions"].sum(),
            'click': df["outbound_clicks_outbound_click"].sum(),
            'campagne_attive': df["campaign"].nunique(),
            'spesa_giornaliera': df.groupby('date')['spend'].sum().reset_index(),
            'dettaglio_campagne': self.get_campaign_details(df),
            'dettaglio_ad': self.get_ad_details(df)
        }

        for r in [aggregate_results]:
            r['cpm'] = r['spesa_totale'] / r['impression'] * 1000 if r['impression'] != 0 else 0
            r['ctr'] = (r['click'] / r['impression']) * 100 if r['impression'] != 0 else 0
            r['cpc'] = r['spesa_totale'] / r['click'] if r['click'] != 0 else 0
        
        return aggregate_results

    def analyze(self):
        df_raw = get_data("facebook_data", self.start_date, self.end_date)
        df_raw_comp = get_data("facebook_data", self.comparison_start, self.comparison_end)

        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw_comp)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp, is_comparison=True)
        return results, results_comp
    
    def get_campaign_details(self, df):
        dettaglioCampagne = df.groupby('adset_name').agg({
            'campaign': lambda x: x.iloc[0],
            'adset_status': lambda x: x.iloc[0],
            'spend': 'sum',
            'impressions': 'sum',
            'outbound_clicks_outbound_click': 'sum',
            'actions_lead': 'sum',
            'actions_omni_purchase': 'sum'
        }).reset_index()

        dettaglioCampagne.rename(columns={
            'adset_name': 'Adset',
            'campaign': 'Campagna',
            'adset_status': 'Stato',
            'spend': 'Spesa',
            'impressions': 'Impression',
            'outbound_clicks_outbound_click': 'Click',
            'actions_lead': 'Lead',
            'actions_omni_purchase': 'Vendite'
        }, inplace=True)

        dettaglioCampagne['CTR'] = (dettaglioCampagne['Click'] / dettaglioCampagne['Impression'] * 100).fillna(0)
        dettaglioCampagne['CPC'] = (dettaglioCampagne['Spesa'] / dettaglioCampagne['Click']).fillna(0)
        dettaglioCampagne['CPL'] = (dettaglioCampagne['Spesa'] / dettaglioCampagne['Lead']).fillna(0)
        dettaglioCampagne['CPA'] = (dettaglioCampagne['Spesa'] / dettaglioCampagne['Vendite']).fillna(0)
        
        dettaglioCampagne = dettaglioCampagne[['Campagna', 'Adset', 'Stato', 'Spesa', 'Impression', 'Click', 'CTR', 'CPC', 'Lead', 'CPL', 'Vendite', 'CPA']]

        return dettaglioCampagne
    
    def get_ad_details(self, df):
        dettaglioAd = df.groupby('ad_name').agg({
            'campaign': lambda x: x.iloc[0],
            'adset_name': lambda x: x.iloc[0],
            'status': lambda x: x.iloc[0],
            'body': lambda x: x.iloc[0],
            'title': lambda x: x.iloc[0],
            'link': lambda x: x.iloc[0],
            'image_url': lambda x: x.iloc[0],
            'spend': 'sum',
            'impressions': 'sum',
            'outbound_clicks_outbound_click': 'sum',
            'actions_lead': 'sum',
            'actions_omni_purchase': 'sum'
        }).reset_index()

        dettaglioAd.rename(columns={
            'ad_name': 'Ad',
            'campaign': 'Campagna',
            'adset_name': 'Adset',
            'status': 'Stato',
            'body': 'Testo',
            'title': 'Titolo',
            'link': 'Link',
            'image_url': 'Immagine',
            'spend': 'Spesa',
            'impressions': 'Impression',
            'outbound_clicks_outbound_click': 'Click',
            'actions_lead': 'Lead',
            'actions_omni_purchase': 'Vendite'
        }, inplace=True)

        dettaglioAd['CTR'] = (dettaglioAd['Click'] / dettaglioAd['Impression'] * 100).fillna(0)
        dettaglioAd['CPC'] = (dettaglioAd['Spesa'] / dettaglioAd['Click']).fillna(0)
        dettaglioAd['CPL'] = (dettaglioAd['Spesa'] / dettaglioAd['Lead']).fillna(0)
        dettaglioAd['CPA'] = (dettaglioAd['Spesa'] / dettaglioAd['Vendite']).fillna(0)
        
        dettaglioAd = dettaglioAd[['Campagna', 'Adset', 'Ad', 'Stato', 'Testo', 'Titolo', 'Link', 'Immagine', 'Spesa', 'Impression', 'Click', 'CTR', 'CPC', 'Lead', 'CPL', 'Vendite', 'CPA']]

        return dettaglioAd

class GadsAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
    
    def clean_data(self, df):
        return df.loc[
            (df["account_id"] == st.secrets["google_ads_account_id"])
        ]
    
    def aggregate_results(self, df, is_comparison=False):
        aggregate_results = {
            'start_date': self.comparison_start if is_comparison else self.start_date,
            'end_date': self.comparison_end if is_comparison else self.end_date,
            'spesa_totale': df["spend"].sum(),
            'impression': df["impressions"].sum(),
            'click': df["clicks"].sum(),
            'campagne_attive': df["campaign"].nunique(),
            'spesa_giornaliera': df.groupby('date')['spend'].sum().reset_index(),
            'dettaglio_campagne': self.get_campaign_details(df),
            'dettaglio_keyword': self.get_keyword_details(df)
        }

        for r in [aggregate_results]:
            r['cpm'] = r['spesa_totale'] / r['impression'] * 1000 if r['impression'] != 0 else 0
            r['ctr'] = (r['click'] / r['impression']) * 100 if r['impression'] != 0 else 0
            r['cpc'] = r['spesa_totale'] / r['click'] if r['click'] != 0 else 0
        
        return aggregate_results

    def analyze(self):
        df_raw = get_data("google_ads_data", self.start_date, self.end_date)
        df_raw_comp = get_data("google_ads_data", self.comparison_start, self.comparison_end)
        
        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw_comp)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp, is_comparison=True)
        return results, results_comp
    
    def get_campaign_details(self, df):
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

        dettaglioCampagne['CTR'] = (dettaglioCampagne['Click'] / dettaglioCampagne['Impression'] * 100).fillna(0)
        dettaglioCampagne['CPC'] = (dettaglioCampagne['Spesa'] / dettaglioCampagne['Click']).fillna(0)

        return dettaglioCampagne

    def get_keyword_details(self, df):
        dettaglioKeyword = df.groupby('keyword_text').agg({
            'spend': 'sum',
            'impressions': 'sum',
            'clicks': 'sum'
        }).reset_index()

        dettaglioKeyword.rename(columns={
            'campaign': 'Campagna',
            'spend': 'Spesa',
            'impressions': 'Impression',
            'clicks': 'Click'
        }, inplace=True)

        dettaglioKeyword['CTR'] = (dettaglioKeyword['Click'] / dettaglioKeyword['Impression'] * 100).fillna(0)
        dettaglioKeyword['CPC'] = (dettaglioKeyword['Spesa'] / dettaglioKeyword['Click']).fillna(0)

        return dettaglioKeyword

class GanalyticsAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
    
    def clean_data(self, df):
        return df.loc[
            (df["account_id"] == st.secrets["googleanalytics4_account_id"])
        ]
    
    def aggregate_results(self, df, is_comparison=False):
        aggregate_results = {
            'start_date': self.comparison_start if is_comparison else self.start_date,
            'end_date': self.comparison_end if is_comparison else self.end_date,
            'utenti_attivi': df["active_users"].sum(),
            'sessioni': df["sessions"].sum(),
            'sessioni_con_engage': df["engaged_sessions"].sum(),
            'durata_engagement': df["user_engagement_duration"].sum(),
            'utenti_attivi_giornalieri': df.groupby('date')['active_users'].sum().reset_index(),
            'sessioni_distribuzione': self.get_session_distribution(df),
            'campagne_distribuzione': self.get_campaign_distribution(df)
        }

        for r in [aggregate_results]:
            r['sessioni_per_utente'] = r['sessioni'] / r['utenti_attivi'] if r['utenti_attivi'] != 0 else 0
            r['durata_sessioni'] = r['durata_engagement'] / r['sessioni'] if r['sessioni'] != 0 else 0
            r['tasso_engage'] = r['sessioni_con_engage'] / r['sessioni'] if r['sessioni'] != 0 else 0
            r['durata_utente'] = r['durata_engagement'] / r['utenti_attivi'] if r['utenti_attivi'] != 0 else 0
        
        return aggregate_results

    def analyze(self):
        df_raw = get_data("googleanalytics4_data", self.start_date, self.end_date)
        df_raw_comp = get_data("googleanalytics4_data", self.comparison_start, self.comparison_end)
        
        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw_comp)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp, is_comparison=True)
        return results, results_comp
    
    def get_session_distribution(self, df):
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
        session_df['percentage'] = session_df['sessions'].div(total_sessions).fillna(0).mul(100)

        return session_df
    
    def get_campaign_distribution(self, df):
        campaign_sessions = df.groupby('campaign')['sessions'].sum().reset_index()

        total_campaign_sessions = campaign_sessions['sessions'].sum()
        campaign_sessions['percentage'] = campaign_sessions['sessions'].div(total_campaign_sessions).fillna(0).mul(100)

        return campaign_sessions

class OppAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end, update_type):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
        self.update_type = update_type
    
    def clean_data(self, df, is_comparison=False):
        df[self.update_type] = pd.to_datetime(df[self.update_type])

        return df
    
    def aggregate_results(self, df, is_comparison=False):
        aggregate_results = {
            'start_date': self.comparison_start if is_comparison else self.start_date,
            'end_date': self.comparison_end if is_comparison else self.end_date,
            'totali': len(df),
            'lead_da_qualificare': df[df['stage'].isin(STAGES['daQualificare'])].shape[0],
            'lead_qualificati': df[df['stage'].isin(STAGES['qualificati'])].shape[0],
            'vendite': df[df['stage'].isin(STAGES['vinti'])].shape[0],
            'opportunità_perse': self.get_opportunità_perse(df),
            'setting_persi': df[df['stage'].isin(STAGES['leadPersi'])].shape[0],
            'vendite_gestione': df[df['stage'].isin(STAGES['venditeGestione'])].shape[0],
            'vendite_da_chiudere': df[df['stage'].isin(STAGES['venditeChiusura'])].shape[0],
            'persi': df[df['stage'].isin(STAGES['persi'])].shape[0],
            'lead_qualificati_giorno': self.lead_qualificati_giorno(df, is_comparison),
            'vinti_giorno': self.vinti_giorno(df, is_comparison),
            'opp_per_giorno': self.opp_per_giorno(df, is_comparison),
            'incasso': df[df['stage'].isin(STAGES['vinti'])]['monetaryValue'].sum(),
            'incasso_giorno': self.incasso_giorno(df, is_comparison),
            'venditori': df['venditore'].unique().tolist(),
            'vendite_venditore': self.get_vendite_per_venditore(df)
        }

        num_days = (aggregate_results['end_date'] - aggregate_results['start_date']).days

        for r in [aggregate_results]:
            r['lead_qualificati_giorno_metrics'] = r['lead_qualificati'] / num_days if num_days != 0 else 0
            r['vinti_giorno_metrics'] = r['vendite'] / num_days if num_days != 0 else 0
            r['tasso_qualifica'] = r['lead_qualificati'] / (r['totali'] - r['lead_da_qualificare']) if r['totali'] > r['lead_da_qualificare'] else 0
            r['tasso_vendita'] = r['vendite'] / r['lead_qualificati'] if r['lead_qualificati'] > 0 else 0
        
        return aggregate_results

    def analyze(self):
        df_raw = get_data("opp_data", self.start_date, self.end_date, custom_date_field=self.update_type)
        df_raw_comp = get_data("opp_data", self.comparison_start, self.comparison_end, custom_date_field=self.update_type)

        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw_comp)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp, is_comparison=True)

        return results, results_comp

    def get_opportunità_perse(self, df):
        opportunitàPerStage = df['stage'].value_counts()
        
        opportunitàPerse = STAGES['leadPersi'] + STAGES['persi']
        filtered_counts = {stage: opportunitàPerStage.get(stage, 0) for stage in opportunitàPerse}
        return pd.DataFrame(list(filtered_counts.items()), columns=['Stage', 'Opportunità'])
    
    def lead_qualificati_giorno(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date

        date_range = pd.date_range(start=start, end=end)
        lead_qualificati_giorno = pd.DataFrame({'date': date_range})

        lead_counts = df[df['stage'].isin(STAGES['qualificati'])].groupby(df[self.update_type].dt.date).size().reset_index(name='count')
        lead_counts.columns = ['date', 'count']
        lead_counts['date'] = pd.to_datetime(lead_counts['date'])

        lead_qualificati_giorno['date'] = pd.to_datetime(lead_qualificati_giorno['date'])

        lead_qualificati_giorno = lead_qualificati_giorno.merge(lead_counts, on='date', how='left')
        lead_qualificati_giorno['count'] = lead_qualificati_giorno['count'].fillna(0)

        return lead_qualificati_giorno

    def vinti_giorno(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date

        date_range = pd.date_range(start=start, end=end)
        vinti_giorno = pd.DataFrame({'date': date_range})

        vinti_counts = df[df['stage'].isin(STAGES['vinti'])].groupby(df[self.update_type].dt.date).size().reset_index(name='count')
        vinti_counts.columns = ['date', 'count']
        vinti_counts['date'] = pd.to_datetime(vinti_counts['date'])

        vinti_giorno['date'] = pd.to_datetime(vinti_giorno['date'])

        vinti_giorno = vinti_giorno.merge(vinti_counts, on='date', how='left')
        vinti_giorno['count'] = vinti_giorno['count'].fillna(0)

        return vinti_giorno
    
    def opp_per_giorno(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date

        date_range = pd.date_range(start=start, end=end)
        opp_per_giorno = pd.DataFrame({'date': date_range})

        opp_counts = df.groupby(df[self.update_type].dt.date).size().reset_index(name='count')
        opp_counts.columns = ['date', 'count']
        opp_counts['date'] = pd.to_datetime(opp_counts['date'])

        opp_per_giorno['date'] = pd.to_datetime(opp_per_giorno['date'])

        opp_per_giorno = opp_per_giorno.merge(opp_counts, on='date', how='left')
        opp_per_giorno['count'] = opp_per_giorno['count'].fillna(0)

        return opp_per_giorno

    def incasso_giorno(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date

        date_range = pd.date_range(start=start, end=end)
        incasso_giorno = pd.DataFrame({'date': date_range})

        incasso_counts = df[df['stage'].isin(STAGES['vinti'])]['monetaryValue'].groupby(df[self.update_type].dt.date).sum().reset_index(name='count')
        incasso_counts.columns = ['date', 'count']
        incasso_counts['date'] = pd.to_datetime(incasso_counts['date'])

        incasso_giorno['date'] = pd.to_datetime(incasso_giorno['date'])

        incasso_giorno = incasso_giorno.merge(incasso_counts, on='date', how='left')
        incasso_giorno['count'] = incasso_giorno['count'].fillna(0)

        return incasso_giorno

    def get_vendite_per_venditore(self, df):
        venditori = COMMERCIALI['venditori']
        vendite_venditore = pd.DataFrame(columns=['Venditore', 'Vendite', 'Fatturato totale', 'Fatturato medio'])

        for venditore in venditori:
            vendite = df[(df['stage'].isin(STAGES['vinti'])) & (df['venditore'] == venditore)]
            num_vendite = vendite.shape[0]
            valore_totale = vendite['monetaryValue'].sum()

            vendite_venditore = pd.concat([vendite_venditore, pd.DataFrame({
                'Venditore': [venditore],
                'Vendite': [num_vendite],
                'Fatturato totale': [valore_totale],
                'Fatturato medio': [valore_totale / num_vendite if num_vendite > 0 else 0]
            })], ignore_index=True)

        vendite_venditore = vendite_venditore.sort_values(by='Fatturato totale', ascending=False)

        return vendite_venditore

class AttributionAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end, update_type):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
        self.update_type = update_type
    
    def clean_data(self, df, is_comparison=False):
        df["createdAt"] = pd.to_datetime(df["createdAt"])
        df["lastStageChangeAt"] = pd.to_datetime(df["lastStageChangeAt"])
        df["data_acquisizione"] = pd.to_datetime(df["data_acquisizione"], errors='coerce')
        df["data_acquisizione"] = df["data_acquisizione"].fillna(pd.NaT)
        df["createdAt"] = df["createdAt"].dt.strftime('%d-%m-%Y')
        df["lastStageChangeAt"] = df["lastStageChangeAt"].dt.strftime('%d-%m-%Y')
        df["data_acquisizione"] = pd.to_datetime(df["data_acquisizione"]).dt.strftime('%d-%m-%Y')

        df = df.loc[
            (df['pipeline_stage_name'].isin(STAGES['stages'])) &
            (df['fonte'].notna())
        ]

        return df
    
    def aggregate_results(self, df, is_comparison=False):
        aggregate_results = {
            'start_date': self.comparison_start if is_comparison else self.start_date,
            'end_date': self.comparison_end if is_comparison else self.end_date,
            'totali': len(df),
            'lead_fonti': df['fonte'].unique().tolist(),
            **{fonte: df[df['fonte'] == fonte].shape[0] for fonte in df['fonte'].unique()},
            'lead_meta': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['stages']))].shape[0],
            'lead_meta_da_qualificare': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['daQualificare']))].shape[0],
            'lead_meta_qualificati': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['qualificati']))].shape[0],
            'lead_meta_lead_persi': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['leadPersi']))].shape[0],
            'lead_meta_vendite_gestione': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['venditeGestione']))].shape[0],
            'lead_meta_vendite_da_chiudere': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['venditeChiusura']))].shape[0],
            'lead_meta_vinti': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['vinti']))].shape[0],
            'lead_meta_persi': df[(df['fonte'] == 'Facebook Ads') & (df['pipeline_stage_name'].isin(STAGES['persi']))].shape[0],
            'lead_google': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['stages']))].shape[0],
            'lead_google_da_qualificare': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['daQualificare']))].shape[0],
            'lead_google_qualificati': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['qualificati']))].shape[0],
            'lead_google_lead_persi': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['leadPersi']))].shape[0],
            'lead_google_vendite_gestione': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['venditeGestione']))].shape[0],
            'lead_google_vendite_da_chiudere': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['venditeChiusura']))].shape[0],
            'lead_google_vinti': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['vinti']))].shape[0],
            'lead_google_persi': df[(df['fonte'] == 'Google Ads') & (df['pipeline_stage_name'].isin(STAGES['persi']))].shape[0]
        }
        
        return aggregate_results

    def analyze(self):
        df_raw = get_data("attribution_data", self.start_date, self.end_date, custom_date_field=self.update_type)
        df_raw_comp = get_data("attribution_data", self.comparison_start, self.comparison_end, custom_date_field=self.update_type)
        
        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw_comp)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp, is_comparison=True)

        return results, results_comp

class TransactionAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
    
    def clean_data(self, df, is_comparison=False):
        df["date"] = pd.to_datetime(df["date"])

        return df.loc[
            (df["status"] == "succeeded")
        ]
    
    def aggregate_results(self, df, is_comparison=False):
        aggregate_results = {
            'start_date': self.comparison_start if is_comparison else self.start_date,
            'end_date': self.comparison_end if is_comparison else self.end_date,
            'totali': len(df),
            'transazioni': df['total'].sum(),
            'prove_gratuite': df[df['total'] == 0].shape[0],
            'abbonamenti_mensili': df[(df['total'] > 0) & (df['total'] < 500)].shape[0],
            'abbonamenti_annuali': df[df['total'] > 500].shape[0],
            'incasso_giorno': self.incasso_giorno(df, is_comparison)
        }
        
        return aggregate_results

    def analyze(self):
        df_raw = get_data("transaction_data", self.start_date, self.end_date, custom_date_field="date")
        df_raw_comp = get_data("transaction_data", self.comparison_start, self.comparison_end, custom_date_field="date")

        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw_comp)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp, is_comparison=True)

        return results, results_comp
    
    def incasso_giorno(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date

        date_range = pd.date_range(start=start, end=end)
        incasso_giorno = pd.DataFrame({'date': date_range})

        incasso_counts = df['total'].groupby(df['date'].dt.date).sum().reset_index(name='count')
        incasso_counts.columns = ['date', 'count']
        incasso_counts['date'] = pd.to_datetime(incasso_counts['date'])

        incasso_giorno['date'] = pd.to_datetime(incasso_giorno['date'])

        incasso_giorno = incasso_giorno.merge(incasso_counts, on='date', how='left')
        incasso_giorno['count'] = incasso_giorno['count'].fillna(0)

        return incasso_giorno