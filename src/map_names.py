import tvdb_v4_official

from src.main import get_secrets, get_db, save_db


def map_names():
    secrets = get_secrets()
    db = get_db()
    tv = tvdb_v4_official.TVDB(secrets['API_KEY'], secrets['PIN'])

    for show in db['shows']:
        show['name'] = tv.get_series(show['id'])['name']

    save_db(db)

if __name__ == '__main__':
    map_names()
