from datetime import datetime, time, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date


def parse_filter_date(value):
    value = (value or '').strip()
    if not value:
        return None

    parsed = parse_date(value)
    if parsed:
        return parsed

    for date_format in ('%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None


def local_day_bounds(selected_date):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(selected_date, time.min), tz)
    return start, start + timedelta(days=1)


def filter_by_local_date_range(queryset, field_name, start_value='', end_value=''):
    start_date = parse_filter_date(start_value)
    end_date = parse_filter_date(end_value)

    if start_date and end_date and end_date < start_date:
        return queryset.none()

    if start_date:
        start, _end = local_day_bounds(start_date)
        queryset = queryset.filter(**{f'{field_name}__gte': start})

    if end_date:
        _start, end = local_day_bounds(end_date)
        queryset = queryset.filter(**{f'{field_name}__lt': end})

    return queryset
