# core/calendar_helper.py
# Builds a month grid for the appointments calendar.

import calendar
from datetime import date


def build_month_grid(year, month, appointments):
    # Group appointments by date so the template can quickly look up each day.
    appts_by_date = {}
    for appt in appointments:
        day = appt.scheduled_at.date()
        appts_by_date.setdefault(day, []).append(appt)

    # calendar.monthcalendar returns a list of weeks, each week a list of 7 day numbers (0 = padding).
    cal = calendar.Calendar(firstweekday=0)  # 0 = Monday
    weeks_raw = cal.monthdayscalendar(year, month)

    # Convert each raw day number into a dict with extra context for the template.
    weeks = []
    today = date.today()
    for week in weeks_raw:
        row = []
        for day_num in week:
            if day_num == 0:
                row.append(None)
                continue
            day_date = date(year, month, day_num)
            row.append({
                'day': day_num,
                'date': day_date,
                'appointments': appts_by_date.get(day_date, []),
                'is_today': day_date == today,
            })
        weeks.append(row)

    return weeks


def get_prev_next_month(year, month):
    if month == 1:
        return (year - 1, 12), (year, 2)
    if month == 12:
        return (year, 11), (year + 1, 1)
    return (year, month - 1), (year, month + 1)