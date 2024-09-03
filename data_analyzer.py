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

class OppCreatedAnalyzer(BaseAnalyzer):
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        super().__init__(start_date, end_date, comparison_start, comparison_end)
    
    def clean_data(self, df, is_comparison=False):
        start = self.comparison_start if is_comparison else self.start_date
        end = self.comparison_end if is_comparison else self.end_date
        
        df = df.loc[
            (df["createdAt"] >= start) &
            (df["createdAt"] <= end)
        ]

        df['createdAt'] = pd.to_datetime(df['createdAt'])

        return df
    
    def aggregate_results(self, df, is_comparison=False):
        num_days = (self.end_date - self.start_date).days

        aggregate_results = {
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
            'incasso': df[df['stage'].isin(STAGES['vinti'])]['monetaryValue'].sum()
        }

        for r in [aggregate_results]:
            r['lead_qualificati_giorno_metrics'] = r['lead_qualificati'] / num_days if num_days != 0 else 0
            r['vinti_giorno_metrics'] = r['vendite'] / num_days if num_days != 0 else 0
            r['tasso_qualifica'] = r['lead_qualificati'] / (r['totali'] - r['lead_da_qualificare']) if r['totali'] > r['lead_da_qualificare'] else 0
            r['tasso_vendita'] = r['vendite'] / r['lead_qualificati'] if r['lead_qualificati'] > 0 else 0
        
        return aggregate_results

    def analyze(self, df_raw):
        df = self.clean_data(df_raw)
        df_comp = self.clean_data(df_raw, is_comparison=True)

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

        lead_counts = df[df['stage'].isin(STAGES['qualificati'])].groupby(df['createdAt'].dt.date).size().reset_index(name='count')
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

        vinti_counts = df[df['stage'].isin(STAGES['vinti'])].groupby(df['createdAt'].dt.date).size().reset_index(name='count')
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

        opp_counts = df.groupby(df['createdAt'].dt.date).size().reset_index(name='count')
        opp_counts.columns = ['date', 'count']
        opp_counts['date'] = pd.to_datetime(opp_counts['date'])

        opp_per_giorno['date'] = pd.to_datetime(opp_per_giorno['date'])

        opp_per_giorno = opp_per_giorno.merge(opp_counts, on='date', how='left')
        opp_per_giorno['count'] = opp_per_giorno['count'].fillna(0)

        return opp_per_giorno