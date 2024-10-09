import pandas as pd
import streamlit as st
import locale

def currency(value):
    try:
        integer_part, decimal_part = f"{value:,.2f}".split(".")
        integer_part = integer_part.replace(",", ".")
        formatted_value = f"€ {integer_part},{decimal_part}"
        return formatted_value
    except Exception as e:
        return "-"

def percentage(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"{integer_part},{decimal_part}%"
    return formatted_value

def thousand_0(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"{integer_part}"
    return formatted_value

def thousand_2(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"{integer_part},{decimal_part}"
    return formatted_value

def get_metric_delta(current, previous):
    if previous == 0:
        return "-"
    return percentage((current - previous) / previous * 100)

def display_metric(label, value, delta, is_delta_inverse=False):
    try:
        st.metric(label, value, delta, delta_color=("inverse" if is_delta_inverse else "normal"))
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione delle metriche: {str(e)}")

def process_daily_data(results, period_name, data_type):
    date_range = pd.date_range(start=results['start_date'], end=results['end_date'])
    daily_data = pd.DataFrame({'date': date_range})
    
    if data_type == 'spesa_giornaliera':
        results['spesa_giornaliera']['date'] = pd.to_datetime(results['spesa_giornaliera']['date'])
        daily_data = daily_data.merge(results['spesa_giornaliera'], on='date', how='left')
        daily_data['spend'] = daily_data['spend'].fillna(0)
        column_name = 'spend'
    elif data_type == 'utenti_attivi_giornalieri':
        results['utenti_attivi_giornalieri']['date'] = pd.to_datetime(results['utenti_attivi_giornalieri']['date'])
        daily_data = daily_data.merge(results['utenti_attivi_giornalieri'], on='date', how='left')
        daily_data['active_users'] = daily_data['active_users'].fillna(0)
        column_name = 'active_users'
    elif data_type == 'lead_qualificati_giorno':
        results['lead_qualificati_giorno']['date'] = pd.to_datetime(results['lead_qualificati_giorno']['date'])
        daily_data = daily_data.merge(results['lead_qualificati_giorno'], on='date', how='left')
        daily_data['count'] = daily_data['count'].fillna(0)
        column_name = 'count'
    elif data_type == 'opp_per_giorno':
        results['opp_per_giorno']['date'] = pd.to_datetime(results['opp_per_giorno']['date'])
        daily_data = daily_data.merge(results['opp_per_giorno'], on='date', how='left')
        daily_data['count'] = daily_data['count'].fillna(0)
        column_name = 'count'
    elif data_type == 'incasso_giorno':
        results['incasso_giorno']['date'] = pd.to_datetime(results['incasso_giorno']['date'])
        daily_data = daily_data.merge(results['incasso_giorno'], on='date', how='left')
        daily_data['count'] = daily_data['count'].fillna(0)
        column_name = 'count'
    else:
        raise ValueError("Tipo di dati non valido.")
    
    daily_data['period'] = period_name
    
    return daily_data[[('date'), (column_name), ('period')]]