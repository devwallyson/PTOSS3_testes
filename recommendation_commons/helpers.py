from datetime import datetime

import numpy as np
import pandas as pd


def parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def append_dated_records(df, dates: list[str], values=None):
    valid_dates = [parse_date(date_str) for date_str in dates if parse_date(date_str) is not None]

    if not valid_dates:
        return
    if values is None:
        values = [None] * (len(df.columns) - 1)

    data = {"date": valid_dates}
    for i, col in enumerate(df.columns[1:], 1):
        val_idx = i - 1
        if val_idx < len(values):
            data[col] = [values[val_idx]] * len(valid_dates)
        else:
            data[col] = [None] * len(valid_dates)

    new_rows = pd.DataFrame(data)
    result = pd.concat([df, new_rows], ignore_index=True)
    result.replace({np.nan: None}, inplace=True)
    result.sort_values(by="date", inplace=True, ignore_index=True)

    df.drop(df.index, inplace=True)
    df._update_inplace(result)


def fill_history_with_pending_dates(consumption_history, pending_bills_dates):
    append_dated_records(consumption_history, pending_bills_dates)


def fill_with_pending_dates(recommendation, consumption_history, pending_bills_dates):
    fill_history_with_pending_dates(consumption_history, pending_bills_dates)

    peak_demand = None
    off_peak_demand = None
    if len(recommendation.frame) > 0:
        peak_demand = recommendation.frame.peak_demand_in_kw[0]
        off_peak_demand = recommendation.frame.off_peak_demand_in_kw[0]

    frame_values = [peak_demand, off_peak_demand] + [None] * (len(recommendation.frame.columns) - 3)
    append_dated_records(recommendation.frame, pending_bills_dates, frame_values)
    append_dated_records(recommendation.current_contract, pending_bills_dates)
