import pandas as pd
from config import STAGES

class DataAnalyzer:
    def __init__(self, start_date, end_date, comparison_start, comparison_end):
        self.start_date = start_date
        self.end_date = end_date
        self.comparison_start = comparison_start
        self.comparison_end = comparison_end

    def analyze_meta(self, df_meta, df_meta_comp):
        results = {
            'spesa_totale': df_meta["spend"].sum(),
            'impression': df_meta["impressions"].sum(),
            'click': df_meta["outbound_clicks_outbound_click"].sum(),
            'campagne_attive': df_meta["campaign"].nunique()
        }
        
        results_comp = {
            'spesa_totale': df_meta_comp["spend"].sum(),
            'impression': df_meta_comp["impressions"].sum(),
            'click': df_meta_comp["outbound_clicks_outbound_click"].sum(),
            'campagne_attive': df_meta_comp["campaign"].nunique()
        }
        
        for r in [results, results_comp]:
            r['cpm'] = r['spesa_totale'] / r['impression'] * 1000 if r['impression'] != 0 else 0
            r['ctr'] = (r['click'] / r['impression']) * 100 if r['impression'] != 0 else 0
            r['cpc'] = r['spesa_totale'] / r['click'] if r['click'] != 0 else 0

        return results, results_comp

    def analyze_gads(self, df_gads, df_gads_comp):
        # Implementa l'analisi di Google Ads qui
        pass

    def analyze_opportunities(self, df_opp, df_opp_comp):
        results = {
            'lead_da_qualificare': df_opp[df_opp['stage'].isin(STAGES['daQualificare'])].shape[0],
            'lead_da_qualificare_comp': df_opp_comp[df_opp_comp['stage'].isin(STAGES['daQualificare'])].shape[0],
            'lead_qualificati': df_opp[df_opp['stage'].isin(STAGES['qualificati'])].shape[0],
            'lead_qualificati_comp': df_opp_comp[df_opp_comp['stage'].isin(STAGES['qualificati'])].shape[0],
            'vendite': df_opp[df_opp['stage'].isin(STAGES['vinti'])].shape[0],
            'vendite_comp': df_opp_comp[df_opp_comp['stage'].isin(STAGES['vinti'])].shape[0]
        }
        
        period_days = (self.end_date - self.start_date).days
        results['lead_qualificati_giorno'] = results['lead_qualificati'] / period_days
        results['lead_qualificati_giorno_comp'] = results['lead_qualificati_comp'] / period_days
        
        results['vendite_giorno'] = results['vendite'] / period_days
        results['vendite_giorno_comp'] = results['vendite_comp'] / period_days

        return results

    def analyze_economics(self, df_opp, df_opp_comp, df_meta, df_meta_comp, df_gads, df_gads_comp):
        # Implementa l'analisi economica qui
        pass