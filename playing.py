#!/usr/bin/env python

import urllib.request
import coverpy
import musicbrainzngs
import random
import config
from gbsfm import gbsfm_nowplaying as nowplaying

dickbutts = ['dickbutt.jpeg', 'diskobees.png', 'diskobutt.png', 'dongarse.jpg', 'heisenbutt.png', 'antibutt.jpg']

def playingquestion():
    song_id, search_art_song, search_art_artist, search_art_album = nowplaying()
    #Do a musicbrainz search
    musicbrainzngs.set_useragent("cover art test script", 1.0)
    mb_searchresult = result = musicbrainzngs.search_release_groups(creditname=search_art_artist, releasegroup=search_art_album, strict=True)
    mb_releases = result['release-group-list']
    if len(mb_releases) > 0:
        try:
            artwork = musicbrainzngs.get_release_group_image_list(mb_releases[0]['id'])
            artwork = artwork['images'][0]['thumbnails']['small']
        except:
            artwork = "https://www2.almstrom.org/disc/" + random.choice(dickbutts)
    else:
        #No musicbrainz-result? Check iTunes
        cpy = coverpy.CoverPy()
        cover_limit = 1
        try:
            result = cpy.get_cover(search_art_album, cover_limit)
            # Set a size for the artwork (first parameter) and get the result url.
            artwork = result.artwork(300)
        except:
            artwork = "https://www2.almstrom.org/disc/" + random.choice(dickbutts)

    get_art = urllib.request.urlopen(artwork)
    artwork=get_art.geturl()
    textreply = search_art_artist + " (" + search_art_album + ") - " + search_art_song
    return artwork, textreply, song_id
