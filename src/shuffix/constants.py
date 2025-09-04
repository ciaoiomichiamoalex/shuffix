from pathlib import Path

PATH_PRJ = Path(__file__).resolve().parents[2]
PATH_CFG = PATH_PRJ / 'config'

QUERY_CREATE_PLAYLIST = """\
    CREATE TABLE IF NOT EXISTS playlist (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        total_tracks INTEGER NOT NULL
    )
    ;
"""
QUERY_DELETE_PLAYLIST = """\
    DELETE FROM playlist
    ;
"""
QUERY_INSERT_PLAYLIST = """\
    INSERT INTO playlist (
        id,
        name,
        total_tracks
    ) VALUES (?, ?, ?)
    ;
"""

QUERY_CREATE_TRACK = """\
    CREATE TABLE IF NOT EXISTS track (
        id TEXT PRIMARY KEY,
        id_playlist TEXT,
        name TEXT NOT NULL,
        album TEXT NOT NULL,
        artists TEXT NOT NULL,
        release_date TEXT NOT NULL,
        disc_number INTEGER NOT NULL,
        track_number INTEGER NOT NULL,
        FOREIGN KEY (id_playlist) REFERENCES playlist (id)
    )
    ;
"""
QUERY_DELETE_TRACK = """\
    DELETE FROM track
    ;
"""
QUERY_GET_TRACKS = """\
    SELECT id
    FROM track
    ORDER BY %(order_by)s
    ;
"""
QUERY_INSERT_TRACK = """\
    INSERT INTO track (
        id,
        id_playlist,
        name,
        album,
        artists,
        release_date,
        disc_number,
        track_number
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ;
"""
