import calendar
from datetime import date


def build_month_grid(year, month, appointments):
    # group by date so the template can index per day
    appts_by_date = {}
    for appt in appointments:
        day = appt.scheduled_at.date()
        appts_by_date.setdefault(day, []).append(appt)

    # monthdayscalendar returns weeks of 7 day numbers, 0 for padding days outside the month
    cal = calendar.Calendar(firstweekday=0)  # 0 = Monday
    weeks_raw = cal.monthdayscalendar(year, month)

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