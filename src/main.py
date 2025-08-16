import re

from tabulate import tabulate

from shuffix import PATH_CFG, Spotify

ORDERINGS = (
    {'name': 'Album', 'order_by': 'album COLLATE NOCASE ASC, disc_number ASC, track_number ASC'},
    {'name': 'Artist', 'order_by': 'artists COLLATE NOCASE ASC, release_date ASC, album COLLATE NOCASE ASC, disc_number ASC, track_number ASC'},
    {'name': 'Random', 'order_by': 'RANDOM() ASC'},
    {'name': 'Release date', 'order_by': 'release_date DESC, album COLLATE NOCASE ASC, disc_number ASC, track_number ASC'},
    {'name': 'Track name', 'order_by': 'name COLLATE NOCASE ASC, album COLLATE NOCASE ASC'}
)

if __name__ == '__main__':
    spotify: Spotify = Spotify(PATH_CFG)

    playlists = spotify.get_playlists()
    # add user saved songs to playlists list
    playlists.insert(0, {
        'id': None,
        'name': 'Liked songs',
        'total_tracks': None
    })

    res = (
        (playlist['name'], playlist['total_tracks'])
        for playlist in playlists
    )
    print(tabulate(res, headers=('Name', 'Tracks number'), tablefmt='orgtbl', showindex=True))
    choice = int(input('\n#> choose playlist index: '))

    playlist_id = playlists[choice]['id']
    spotify.get_tracks(playlist_id)

    res = ((ordering['name'],) for ordering in ORDERINGS)
    print(f'\n{tabulate(res, headers=('Ordering',), tablefmt='orgtbl', showindex=True)}')
    choice = int(input('\n#> choose ordering index: '))
    order_by = (ORDERINGS[choice]['order_by']
                if playlist_id
                # invert ascending with descending order for user saved songs
                else re.sub(r'\b(ASC|DESC)\b',
                            lambda m: {'ASC': 'DESC', 'DESC': 'ASC'}[m.group(1).upper()],
                            ORDERINGS[choice]['order_by'],
                            flags=re.IGNORECASE)
                )

    # remove and resave all songs in the selected playlist
    print('\n#> removing tracks... ', end='')
    spotify.remove_tracks(playlist_id)
    print('ok\n#> saving tracks... ', end='')
    spotify.save_tracks(order_by, playlist_id)
    print('ok')

    del spotify
