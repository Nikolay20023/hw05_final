import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    year = datetime.datetime.today().year
    return {
        'year': int(year)
    }
