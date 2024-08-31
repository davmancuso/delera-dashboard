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

    def analyze(self, df_meta_raw):
        df_meta = self.clean_data(df_meta_raw)
        df_meta_comp = self.clean_data(df_meta_raw, is_comparison=True)

        results = self.aggregate_results(df_meta)
        results_comp = self.aggregate_results(df_meta_comp)

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

        dettaglioCampagne['CTR'] = dettaglioCampagne['Click'] / dettaglioCampagne['Impression'] * 100 if dettaglioCampagne['Impression'] != 0 else 0
        dettaglioCampagne['CPC'] = dettaglioCampagne['Spesa'] / dettaglioCampagne['Click'] if dettaglioCampagne['Click'] != 0 else 0

        return dettaglioCampagne