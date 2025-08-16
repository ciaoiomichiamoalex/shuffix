import re
import time
from pathlib import Path
from typing import Generator

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from core import LowQuerier, decode_json
from .constants import (PATH_PRJ, QUERY_CREATE_PLAYLIST, QUERY_CREATE_TRACK, QUERY_DELETE_PLAYLIST,
                        QUERY_DELETE_TRACK, QUERY_GET_TRACKS, QUERY_INSERT_PLAYLIST, QUERY_INSERT_TRACK)


class Spotify:
    """
    The Spotify object allows for manage playlist songs.
    """
    def __init__(self,
                 cfg_in: str | Path) -> None:
        """
        Read from a JSON config file your account credentials and start the connection.
        The class also open a connection to a local SQLite database in the project root folder.

        :param cfg_in: The path to the JSON file with the account credentials.
        :type cfg_in: str | Path
        """
        cfg_in = Path(cfg_in).resolve()
        # if input path is a directory search for default config filename
        if cfg_in.is_dir():
            cfg_in = cfg_in / 'shuffix.json'

        config = decode_json(cfg_in)
        self._connection = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri='https://127.0.0.1:7070/callback',
            scope=(
                'playlist-read-private',
                'playlist-read-collaborative',
                'playlist-modify-public',
                'playlist-modify-private',
                'user-library-read',
                'user-library-modify'
            )
        ))

        self._querier: LowQuerier = LowQuerier(
            conn_in=(PATH_PRJ / 'shuffix.db'),
            save_changes=True
        )
        # create database tables if their not exists
        self._querier.run(QUERY_CREATE_PLAYLIST)
        self._querier.run(QUERY_CREATE_TRACK)

    def __del__(self):
        del self._querier

    def get_playlists(self) -> list[dict]:
        """
        Return and save on the local database the list of user playlists.

        :return: The list of user playlists.
        :rtype: list[dict]
        """
        self._querier.run(QUERY_DELETE_PLAYLIST)
        offset, res = 0, []
        while True:
            # get 50 user playlist at time
            playlists = self._connection.current_user_playlists(limit=50, offset=offset)

            for playlist in playlists['items']:
                res.append({
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'total_tracks': playlist['tracks']['total']
                })
                self._querier.run(QUERY_INSERT_PLAYLIST, *res[-1].values())

            if not playlists['next']: break
            offset += 50
        return res

    def get_tracks(self,
                   playlist_id: str = None) -> list[dict]:
        """
        Return and save on the local database the list of tracks in a specific user playlist.
        If the playlist_id argument is None, will be returned the user saved tracks.

        :param playlist_id: The user playlist id, defaults to None.
        :type playlist_id: str
        :return: The list of playlist tracks.
        :rtype: list[dict]
        """
        self._querier.run(QUERY_DELETE_TRACK)
        offset, res = 0, []
        while True:
            # get 100 songs at time or 50 if it's on user saved songs
            tracks = (self._connection.playlist_items(playlist_id, limit=100, offset=offset)
                      if playlist_id
                      else self._connection.current_user_saved_tracks(limit=50, offset=offset))

            for track in tracks['items']:
                if not track['is_local']:
                    res.append({
                        'id': track['track']['id'],
                        'playlist_id': playlist_id,
                        'name': track['track']['name'],
                        'album': track['track']['album']['name'],
                        'artists': ', '.join(artist['name'] for artist in track['track']['album']['artists']),
                        'release_date': (
                            # add first of january if the date is only year
                            f"{track['track']['album']['release_date']}-01-01"
                            if re.search(r'^\d{4}$', track['track']['album']['release_date'])
                            else track['track']['album']['release_date']
                        ),
                        'disc_number': track['track']['disc_number'],
                        'track_number': track['track']['track_number']
                    })
                    self._querier.run(QUERY_INSERT_TRACK, *res[-1].values())

            if not tracks['next']: break
            offset += (100 if playlist_id else 50)
        return res

    @staticmethod
    def _chunks(items: list[str]) -> Generator[list[str]]:
        """
        Split a list of string in sub-list of 50 items each one.

        :param items: The list of string to be split.
        :type items: list[str]
        :return: The sub-list of 50 items.
        :rtype: Generator[list[str]]
        """
        for index in range(0, len(items), 50):
            yield items[index:index + 50]

    def remove_tracks(self,
                      playlist_id: str = None) -> None:
        """
        Remove all tracks saved on local database from a specific user playlist.
        If the playlist_id argument is None, will be removed from the user saved tracks.

        :param playlist_id: The user playlist id, defaults to None.
        :type playlist_id: str
        """
        tracks, items = self._querier.run(QUERY_GET_TRACKS % {'order_by': 'id'}), []
        for track in tracks:
            items.append(f"spotify:track:{track['id']}")

        for chunk in Spotify._chunks(items):
            if playlist_id: self._connection.playlist_remove_all_occurrences_of_items(playlist_id, chunk)
            else: self._connection.current_user_saved_tracks_delete(chunk)
            # max 5 call per second, to not get timeout error
            time.sleep(0.2)

    def save_tracks(self,
                    order_by: str,
                    playlist_id: str = None) -> None:
        """
        Add all tracks saved on local database to a specific user playlist.
        If the playlist_id argument is None, will be added on the user saved tracks.

        :param order_by: The sort ordering used in SQL query to retrieve the list of tracks from local database.
        :type order_by: str
        :param playlist_id: The user playlist id, defaults to None.
        :type playlist_id: str
        """
        tracks, items = self._querier.run(QUERY_GET_TRACKS % {'order_by': order_by}), []
        for track in tracks:
            items.append(f"spotify:track:{track['id']}")

        for chunk in Spotify._chunks(items):
            if playlist_id: self._connection.playlist_add_items(playlist_id, chunk)
            else: self._connection.current_user_saved_tracks_add(chunk)
            # max 5 call per second, to not get timeout error
            time.sleep(0.2)
