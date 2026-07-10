import os


def test_db_config_for_branch():
    expected = os.environ.get('DB_MODE', 'dev')

    with open('config/settings.py') as f:
        lines = f.readlines()

    sqlite_active = None
    postgres_active = None

    for line in lines:
        s = line.strip()
        if 'django.db.backends.sqlite3' in s:
            sqlite_active = not s.startswith('#')
        if 'django.db.backends.postgresql' in s:
            postgres_active = not s.startswith('#')

    if expected == 'prod':
        assert postgres_active, (
            "На ветке main PostgreSQL должен быть активен (раскомментирован), "
            "а SQLite закомментирован"
        )
        assert not sqlite_active, (
            "На ветке main SQLite должен быть закомментирован"
        )
    else:
        assert sqlite_active, (
            "На ветке dev SQLite должен быть активен (раскомментирован), "
            "а PostgreSQL закомментирован"
        )
        assert not postgres_active, (
            "На ветке dev PostgreSQL должен быть закомментирован"
        )
