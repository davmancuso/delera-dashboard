import locale

def currency(value):
    integer_part, decimal_part = f"{value:,.2f}".split(".")
    integer_part = integer_part.replace(",", ".")
    formatted_value = f"€ {integer_part},{decimal_part}"
    return formatted_value

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