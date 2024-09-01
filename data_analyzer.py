import pandas as pd
from config import STAGES

class BaseAnalyzer:
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        self.start_date = start_date
        self.end_date = end_date
        self.comparison_start = comparison_start
        self.comparison_end = comparison_end

class MetaAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end, meta_account):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
        self.meta_account = meta_account
    
    def clean_data(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date
        
        return df.loc[
            (df["datasource"] == "facebook") &
            (df["account_name"] == self.meta_account) &
            (df["date"] >= start) &
            (df["date"] <= end) &
            (~df["campaign"].str.contains(r"\[HR\]")) &
            (~df["campaign"].str.contains(r"DENTALAI"))
        ]
    
    def aggregate_results(self, df):
        aggregate_results = {
            'spesa_totale': df["spend"].sum(),
            'impression': df["impressions"].sum(),
            'click': df["outbound_clicks_outbound_click"].sum(),
            'campagne_attive': df["campaign"].nunique(),
            'spesa_giornaliera': df.groupby('date')['spend'].sum().reset_index(),
            'dettaglio_campagne': self.get_campaign_details(df)
        }

        for r in [aggregate_results]:
            r['cpm'] = r['spesa_totale'] / r['impression'] * 1000 if r['impression'] != 0 else 0
            r['ctr'] = (r['click'] / r['impression']) * 100 if r['impression'] != 0 else 0
            r['cpc'] = r['spesa_totale'] / r['click'] if r['click'] != 0 else 0
        
        return aggregate_results

    def analyze(self, df_raw):
        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw, is_comparison=True)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp)

        return results, results_comp
    
    def get_campaign_details(self, df):
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

        dettaglioCampagne['CTR'] = (dettaglioCampagne['Click'] / dettaglioCampagne['Impression'] * 100).fillna(0)
        dettaglioCampagne['CPC'] = (dettaglioCampagne['Spesa'] / dettaglioCampagne['Click']).fillna(0)

        return dettaglioCampagne

class GadsAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end, gads_account):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
        self.gads_account = gads_account
    
    def clean_data(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date
        
        return df.loc[
            (df["datasource"] == "google") &
            (df["account_name"] == self.gads_account) &
            (df["date"] >= start) &
            (df["date"] <= end)
        ]
    
    def aggregate_results(self, df):
        aggregate_results = {
            'spesa_totale': df["spend"].sum(),
            'impression': df["impressions"].sum(),
            'click': df["clicks"].sum(),
            'campagne_attive': df["campaign"].nunique(),
            'spesa_giornaliera': df.groupby('date')['spend'].sum().reset_index(),
            'dettaglio_campagne': self.get_campaign_details(df)
        }

        for r in [aggregate_results]:
            r['cpm'] = r['spesa_totale'] / r['impression'] * 1000 if r['impression'] != 0 else 0
            r['ctr'] = (r['click'] / r['impression']) * 100 if r['impression'] != 0 else 0
            r['cpc'] = r['spesa_totale'] / r['click'] if r['click'] != 0 else 0
        
        return aggregate_results

    def analyze(self, df_raw):
        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw, is_comparison=True)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp)

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

class GanalyticsAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end, ganalytics_account):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
        self.ganalytics_account = ganalytics_account
    
    def clean_data(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date
        
        return df.loc[
            (df["datasource"] == "googleanalytics4") &
            (df["account_name"] == self.ganalytics_account) &
            (df["date"] >= start) &
            (df["date"] <= end)
        ]
    
    def aggregate_results(self, df):
        aggregate_results = {
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

    def analyze(self, df_raw):
        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw, is_comparison=True)

        results = self.aggregate_results(df)
        results_comp = self.aggregate_results(df_comp)

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