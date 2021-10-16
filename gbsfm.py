#!/usr/bin/env python

import MySQLdb
import config
import urllib.request
import time

#Defining database connection
db = MySQLdb.connect(host=config.mysql_dbhost, user=config.mysql_user, passwd=config.mysql_passwd, db=config.mysql_db, charset="utf8")

#Check if a string can be converted into a float
def check_float(potential_float):
    try:
        float(potential_float)
        return True
    except ValueError:
        return False

#Function to add a song to the playlist by song id. This only works for authed users
def gbsfm_addsong( userid, apikey, songid ):
    addsong_url = config.gbsfm_baseurl + "/api/add?userid=" + str(userid) + "&key=" + apikey + "&songid=" + str(songid)
    try:
        addsong_request = urllib.request.urlopen(addsong_url)
        addsong_result = addsong_request.read()
        addsong_request.close()
        addsong_result = addsong_result.decode("utf8")
        add_success = 1
        msg = "Success!"
    except urllib.error.HTTPError as error:
        errmsg = error.read()
        msg = "Sorry, " + errmsg.decode('utf-8')
        add_success = 0
    return add_success, msg

#Gets the currently playing song
def gbsfm_nowplaying():
    query = db.cursor()
    query.execute ("SELECT \
        playlist_playlistentry.song_id, \
        playlist_song.title AS songtitle, \
        playlist_artist.`name` AS artist, \
        playlist_album.`name` as album \
        FROM \
        playlist_playlistentry \
        INNER JOIN playlist_song ON playlist_playlistentry.song_id = playlist_song.id \
        INNER JOIN playlist_artist ON playlist_song.artist_id = playlist_artist.id \
        INNER JOIN playlist_album ON playlist_song.album_id = playlist_album.id \
        WHERE \
        playlist_playlistentry.playing = 1")
    db.commit()
    q_nowplaying = query.fetchone()
    return q_nowplaying[0], q_nowplaying[1], q_nowplaying[2], q_nowplaying[3]
    #Returns song_id, songtitle, artist, album

#Function to check if a user has authed. Input their long discord id
def gbsfm_isauthed( discordid_long ):
    query = db.cursor()
    query.execute ("SELECT * from discord_auth where discord_id_long = %s limit 1", (discordid_long,))
    db.commit()
    queryresult = query.fetchone()
    if queryresult is None:
        authbool = 0
        user_gbsfmid = 0
        user_apikey = 0
        user_shortuid = 0
        user_longuid = 0
        return authbool, user_gbsfmid, user_apikey, user_shortuid, user_longuid
    else:
        authbool = 1
        user_gbsfmid = str(queryresult[3])
        user_apikey = str(queryresult[2])
        user_shortuid = str(queryresult[1])
        user_longuid = str(queryresult[4])
        return authbool, user_gbsfmid, user_apikey, user_shortuid, user_longuid

#Gets user stats
def gbsfm_stoats( user_gbsfmid ):
    query = db.cursor()
    query.execute ("SELECT count(*) cnt FROM playlist_song ps LEFT OUTER JOIN playlist_oldplaylistentry ope ON ps.id = ope.song_id WHERE ps.uploader_id = %s AND ope.id IS NULL;", (user_gbsfmid,))
    q_unplayed = query.fetchone()
    str_response = "You have " + str(q_unplayed[0]) + " unplayed dongs.\n"
    query.execute ("SELECT count(*) cnt FROM playlist_song WHERE banned = 1 AND uploader_id = %s", (user_gbsfmid,))
    q_banned = query.fetchone()
    str_response = str_response + "You have " + str(q_banned[0]) + " banned dongs.\n"
    query.execute ("SELECT ps.id id, concat(pa.name, ' - ', ps.title) dong, COUNT( * ) cnt \
                    FROM playlist_song ps \
                    INNER JOIN playlist_artist pa ON ps.artist_id = pa.id \
                    INNER JOIN playlist_oldplaylistentry ope ON ope.song_id = ps.id \
                    WHERE ope.adder_id = %s \
                    GROUP BY id, dong \
                    ORDER BY cnt DESC \
                    LIMIT 0, 10;", (user_gbsfmid,))
    q_mostadded = query.fetchone()
    str_response = str_response + "__Most songs added by you:__\n"
    while q_mostadded is not None:
        str_response = str_response + str(q_mostadded[1]) + " (" + str(q_mostadded[2]) + ")\n"
        q_mostadded = query.fetchone()
    query.execute ("SELECT concat(pa.name, ' - ', ps.title) dong, au.username adder \
                    FROM playlist_song ps \
                    INNER JOIN playlist_artist pa \
                    ON ps.artist_id = pa.id \
                    INNER JOIN playlist_oldplaylistentry ope \
                    ON ps.id = ope.song_id \
                    INNER JOIN auth_user au \
                    ON au.id = ope.adder_id \
                    WHERE ps.uploader_id = %s AND ope.adder_id <> %s \
                    ORDER BY ope.addtime DESC \
                    LIMIT 0, 10", (user_gbsfmid,user_gbsfmid))
    q_addedups = query.fetchone()
    str_response = str_response + "__Most recent additions of your uploads (not by you)__\n"
    while q_addedups is not None:
        str_response = str_response + str(q_addedups[0]) + " (" + str(q_addedups[1]) + ")\n"
        q_addedups = query.fetchone()
    return str_response

#Query the database for list of songs
def gbsfm_query( query_type, user_gbsfmid, querystring ):
    #print(query_type, user_gbsfmid, querystring)
    unformatted = ['sup', 'dongid', 'dongid24no', 'user']
    if not query_type in unformatted:
        querystring = '%{}%'.format(querystring)
    query = db.cursor()
    if query_type == 'aup': #Any unplayed song
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, playlist_album.`name` \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        INNER JOIN playlist_album ON ps.album_id = playlist_album.id \
                        WHERE NOT \
                        EXISTS (SELECT * FROM playlist_oldplaylistentry \
                        WHERE song_id = ps.id) \
                        order by rand() limit 10")
    elif query_type == 'random': #Any random song
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, playlist_album.`name` \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        INNER JOIN playlist_album ON ps.album_id = playlist_album.id \
                        order by rand() limit 10")
    elif query_type == 'unplayed': #Any song uploaded by the user that is unplayed
        query.execute ("SELECT playlist_song.id, playlist_artist.`name` as artist, playlist_song.title, playlist_album.`name` as album \
                        FROM playlist_song \
                        INNER JOIN playlist_album ON playlist_song.album_id = playlist_album.id \
                        INNER JOIN playlist_artist ON playlist_song.artist_id = playlist_artist.id \
                        WHERE playlist_song.uploader_id = %s \
                        and playlist_song.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        and playlist_song.id not in (SELECT song_id FROM \
                        playlist_oldplaylistentry WHERE song_id = playlist_song.id) \
                        order by rand() limit 10", [user_gbsfmid])
    elif query_type == 'userany': #Any song uploaded by the user
        query.execute ("SELECT playlist_song.id, playlist_artist.`name` as artist, playlist_song.title, playlist_album.`name` as album \
                        FROM playlist_song \
                        INNER JOIN playlist_album ON playlist_song.album_id = playlist_album.id \
                        INNER JOIN playlist_artist ON playlist_song.artist_id = playlist_artist.id \
                        WHERE playlist_song.uploader_id = %s \
                        and playlist_song.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        order by rand() limit 10", [user_gbsfmid])
    elif query_type == 'faves': #Any favorite of the user
        query.execute ("SELECT playlist_userprofile_favourites.song_id, \
                        playlist_artist.`name`, playlist_song.title, \
                        playlist_album.`name`FROM playlist_userprofile \
                        INNER JOIN playlist_userprofile_favourites ON playlist_userprofile_favourites.userprofile_id = playlist_userprofile.id \
                        INNER JOIN playlist_song ON playlist_userprofile_favourites.song_id = playlist_song.id AND playlist_userprofile_favourites.song_id = playlist_song.id \
                        INNER JOIN playlist_artist ON playlist_song.artist_id = playlist_artist.id \
                        INNER JOIN playlist_album ON playlist_song.album_id = playlist_album.id \
                        WHERE playlist_userprofile.user_id = %s \
                        and playlist_userprofile_favourites.song_id not in \
                        (SELECT playlist_oldplaylistentry.song_id \
                        FROM playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        order by RAND()", [user_gbsfmid])
    elif query_type == 'album': #Query by album
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, pa.`name` AS album \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_album AS pa ON ps.album_id = pa.id \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        WHERE ps.album_id = pa.id and pa.name LIKE %s \
                        and ps.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        order by RAND() limit 10", (querystring,))
    elif query_type == 'artist': #Query by artist
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, pa.`name` AS album \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_album AS pa ON ps.album_id = pa.id \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        WHERE ps.album_id = pa.id and playlist_artist.name LIKE %s \
                        and ps.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        order by RAND() limit 10", (querystring,))
    elif query_type == 'title': #Query by title
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, pa.`name` AS album \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_album AS pa ON ps.album_id = pa.id \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        WHERE ps.album_id = pa.id and ps.title LIKE %s \
                        and ps.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        and ps.id not in (select song_id from playlist_playlistentry) \
                        order by RAND() limit 10", (querystring,))
    elif query_type == 'sup': #Get short dongs
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, pa.`name` AS album \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_album AS pa ON ps.album_id = pa.id \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        WHERE ps.length < %s \
                        and ps.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        and ps.id not in (select song_id from playlist_playlistentry) \
                        order by RAND() limit 10", [querystring])
    elif query_type == 'user': #Add by username
        query.execute ("SELECT playlist_song.id, playlist_song.title, playlist_artist.`name`, playlist_album.`name` as album \
                        FROM playlist_song \
                        INNER JOIN auth_user ON auth_user.id = playlist_song.uploader_id \
                        INNER JOIN playlist_artist ON playlist_song.artist_id = playlist_artist.id \
                        INNER JOIN playlist_album ON playlist_song.album_id = playlist_album.id \
                        where playlist_song.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        and auth_user.username = %s \
                        order by RAND() limit 10", [querystring])
    elif query_type == 'dongid': #Add by dong id
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, pa.`name` AS album \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_album AS pa ON ps.album_id = pa.id \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        WHERE ps.id = %s \
                        and ps.id not in (select song_id from playlist_oldplaylistentry \
                        WHERE playlist_oldplaylistentry.playtime > NOW()-INTERVAL 8*24 HOUR) \
                        limit 1", [querystring])
    elif query_type == 'dongid24no': #Add by dong id
        query.execute ("SELECT ps.id, playlist_artist.`name`, ps.title, pa.`name` AS album \
                        FROM playlist_song AS ps \
                        INNER JOIN playlist_album AS pa ON ps.album_id = pa.id \
                        INNER JOIN playlist_artist ON ps.artist_id = playlist_artist.id \
                        WHERE ps.id = %s \
                        limit 1", [querystring])
    elif query_type == 'lowrating': #Add by low rating
        query.execute ("SELECT songid, artist, title, album FROM songs_rated WHERE songs_rated.score < 2 order by rand() limit 10")
    elif query_type == 'highrating': #Add by high rating
        query.execute ("SELECT songid, artist, title, album FROM songs_rated WHERE songs_rated.score > 4.8 order by rand() limit 10")

    db.commit()
    #print(query.rowcount)
    returnlist = []
    if query.rowcount > 0:
        row = query.fetchone()
        while row is not None:
            returnlist.append(row)
            row = query.fetchone()
    else:
        print('Shiiiiiit')
    #print(returnlist)
    return returnlist #Returns (id, artist, songtitle, album) x up to 10 in a list

# -------------------------------------------------------------------

#Play
def gbsfm_play( query_type, user_gbsfmid, user_apikey, user_longuid, query_string ):
    songlist = gbsfm_query(query_type, user_gbsfmid, query_string)
    if len(songlist) > 0:
        for song in songlist:
            #Try to add the songs in the list, bail when one succeeds
            add_success, add_msg = gbsfm_addsong(user_gbsfmid, user_apikey, song[0])
            if add_success == 1:
                str_addmessage = "Added _" + song[2] + "_ by _" + song[1] + "_ from _" + song[3] + "_ for " + user_longuid
                added_songid = song[0]
                break
            if add_success == 0 and add_msg == "Sorry, you already have too many songs on the playlist":
                str_addmessage = add_msg
                added_songid = 0
                break
    else:
        add_success = 0
        str_addmessage = "Your query didn't return any results."
        added_songid = 0
    return add_success, str_addmessage, added_songid

#Adds a message to the list of botmessages one can react to
def gbsfm_add_botmessage( msgid, added_songid ):
    query = db.cursor()
    query.execute ("insert into discord_botmessages (message_id, song_id) values (%s, %s)", (msgid, added_songid))
    db.commit()

def gbsfm_auth( authid, discord_id, discord_id_long ):
    query = db.cursor()
    query.execute ("SELECT auth_user.username, playlist_userprofile.api_key, playlist_userprofile.user_id \
                    FROM auth_user INNER JOIN playlist_userprofile ON auth_user.id = playlist_userprofile.user_id \
                    WHERE playlist_userprofile.api_key = %s", (authid,))
    db.commit()
    queryresult = query.fetchone()
    if queryresult is None:
        auth_success = 0
        auth_message = "Wrong auth id!"
    else:
        sql_discord_id = str(discord_id)
        sql_api_key = str(authid)
        sql_user_id = queryresult[2]
        sql_discord_id_long = str(discord_id_long)
        query = db.cursor()
        query.execute ("insert into discord_auth (discord_id, api_key, user_id, discord_id_long) values (%s, %s, %s, %s) \
                        ON DUPLICATE KEY UPDATE discord_id=%s, api_key=%s, user_id=%s, discord_id_long=%s",(sql_discord_id,sql_api_key,sql_user_id,sql_discord_id_long,sql_discord_id,sql_api_key,sql_user_id,sql_discord_id_long))
        db.commit()
        auth_success = 1
        auth_message = "Correct auth id! You are now authed from " + str(discord_id)
    return auth_success, auth_message

#Give tokens
def gbsfm_givetokens( token_recipient, token_recipient_short, token_amount ):
    query = db.cursor()
    query.execute ("SELECT discord_auth.user_id, playlist_userprofile.tokens \
                    FROM discord_auth INNER JOIN playlist_userprofile ON \
                    discord_auth.user_id = playlist_userprofile.user_id WHERE \
                    discord_auth.discord_id = %s", (token_recipient_short,))
    q_tokens = query.fetchone()
    token_current = q_tokens[1]
    token_gbsfmid = q_tokens[0]
    token_new = int(token_amount) + int(token_current)
    query = db.cursor()
    query.execute ("update playlist_userprofile set tokens = %s where user_id = %s", (token_new, token_gbsfmid))
    token_response = "You gave <@" + str(token_recipient) + "> " + str(token_amount) + " token(s)"
    return token_response

#Check tokens
def gbsfm_gettokens( user_gbsfmid, user_longuid ):
    query = db.cursor()
    query.execute ("SELECT playlist_userprofile.tokens FROM playlist_userprofile WHERE playlist_userprofile.user_id = %s", (user_gbsfmid,))
    q_tokens = query.fetchone()
    token_response = user_longuid + " has " + str(q_tokens[0]) +" tokens\n"
    return token_response

#Play jingle
def gbsfm_jingle( user_longuid ):
    add_success, str_addmessage, added_songid = gbsfm_play('artist', config.shoes_id, config.shoes_apikey, user_longuid, 'Jingles')
    return add_success, str_addmessage, added_songid

#Check when your next dong is playing
def gbsfm_when ( user_gbsfmid ):
    query = db.cursor()
    query.execute ("SELECT playlist_playlistentry.song_id, playlist_playlistentry.adder_id, \
                    playlist_playlistentry.playtime, playlist_playlistentry.playing, \
                    playlist_song.length FROM playlist_playlistentry \
                    INNER JOIN playlist_song ON playlist_playlistentry.song_id = playlist_song.id")
    db.commit()
    playlistentries = query.fetchall()
    until_next = 0
    dongfound = 0
    result = 0
    if len(playlistentries) < 1:
        result = 1
        responsemessage = "There's only one dong in the playlist..."
    else:
        for playlistnumber in playlistentries:
            when_songid = playlistnumber[0]
            when_adder_id = playlistnumber[1]
            when_playtime = playlistnumber[2]
            when_playing = playlistnumber[3]
            when_length = playlistnumber[4]
            if str(when_adder_id) == str(user_gbsfmid) and str(when_playing) == "1":
                result = 2
                break
            if str(when_playing) == "1":
                when_playtime_current_playing = playlistnumber[4]
                when_playtime = time.mktime(when_playtime.timetuple())
                when_playtime_now = int(time.time()) - 3600 #DST bodge
                when_playtime_diff = when_playtime_now - when_playtime
                when_playtime_diff = when_length - when_playtime_diff
                if when_playtime_diff > 1:
                    until_next = until_next + when_playtime_diff
                continue
            if str(when_adder_id) == str(user_gbsfmid):
                dongfound = 1
                break
            until_next = until_next + int(when_length)
        if result == 2:
            responsemessage = "The dong currently playing is yours..."
        elif dongfound == 1 and result == 0:
            responsemessage = time.strftime('%H:%M:%S', time.gmtime(int(until_next)))
            responsemessage = "There is about " + str(responsemessage) +" until your next dong"
            result = 4
            if until_next < when_playtime_current_playing:
                result = 3
                responsemessage = "Your dong is next, hurry!" + "\n" + responsemessage
        else:
            result = 5
            responsemessage = "No song in the playlist!"
    return result, responsemessage # result = 1=only one song, 2=dong playing is mine, 3=dong is next, 4=normal, 5=no song

def gbsfm_vote ( vote, user_gbsfmid, user_apikey ):
    votesuccess = False
    extra_message = 0

    votemacrolist_5         = ["gold", "awesome", "amazing", "boners", "excellent", "lovely", ":rock:", "metal", \
                                   "smashing", "super", "great", "oldskool", "blood", "humppa", "classical"]
    votemacrolist_49        = ["eurocheese"]
    votemacrolist_48        = ["mastersord"]
    votemacrolist_42        = ["alita"]
    votemacrolist_4         = ["good"]
    votemacrolist_40        = ["nihiliste"]
    votemacrolist_39        = ["merijn"]
    votemacrolist_37        = ["icetraigh"]
    votemacrolist_3         = ["average", "ok", "mediocre", "meh"]
    votemacrolist_27        = ["e"]
    votemacrolist_2         = ["bad", "poor"]
    votemacrolist_18        = []
    votemacrolist_16        = ["phi"]
    votemacrolist_11        = ["carmi", "wynorski"]
    votemacrolist_1         = ["terrible", "awful", "dreadful", "cancer", "aids", "anime", "pepper"]
    votemacrolist_techno    = ["technotechnotechnotechno"]
    votemacrolist_buttes    = ["buttes"]
    votemacrolist_hitler    = ["hitler", "goering", "himmler", "goebbels", "aryansupremacy"]
    votemacrolist_pi        = ["pi"]
    votemacrolist_tory      = ["tory"]
    votemacrolist_weed      = ["weed"]
    votemacrolist = votemacrolist_5 + votemacrolist_49 + votemacrolist_48 + votemacrolist_42 + votemacrolist_4 \
                    + votemacrolist_40 + votemacrolist_39 + votemacrolist_37 + votemacrolist_3 + votemacrolist_27 \
                    + votemacrolist_2 + votemacrolist_18 + votemacrolist_16 + votemacrolist_11 + votemacrolist_1 \
                    + votemacrolist_techno + votemacrolist_buttes + votemacrolist_pi \
                    + votemacrolist_tory + votemacrolist_weed

    #If the length of the votesting is 1, and it's a number, it's a normal vote, no macro
    if len(vote) == 1 and check_float(vote[0]):
        votemode = 'normal'
    #If the length of the votesting is 1, and it's not a number, it's a normal vote, with macro
    elif len(vote) == 1 and not check_float(vote[0]):
        votemode = 'normal_macro'
    #If the length is 2 and the second argument is a number, it's and advanced vote, no macro
    elif len(vote) == 2 and check_float(vote[1]) and vote[0][0] == '#':
        votemode = 'advanced'
    #If the length is 2 and the second argument is not a number, it's and advanced vote, with macro
    elif len(vote) == 2 and not check_float(vote[1]):
        votemode = 'advanced_macro'
    #Vote doesn't comply, return errormessage
    else:
        print('fart')

    #Get currently playing song
    song_id, songtitle, artist, album = gbsfm_nowplaying()

    if votemode == 'normal':
        votenumber = vote[0]
        votesuccess = True
    elif votemode == 'advanced':
        votenumber = vote[1]
        song_id = vote[0][1:]
        song = gbsfm_query('dongid24no', 0, song_id)
        votesuccess = True
        vote = vote[1]
    elif votemode == 'normal_macro' or votemode == 'advanced_macro':
        if votemode == 'advanced_macro':
            song_id = vote[0][1:]
            song = gbsfm_query('dongid24no', 0, song_id)
            vote = vote[1]
        else:
            vote = vote[0]
        if any(vote == vmacro for vmacro in votemacrolist):
            if any(vote == vmacro for vmacro in votemacrolist_5):
                votenumber = 5
            elif any(vote == vmacro for vmacro in votemacrolist_49):
                votenumber = 4.9
            elif any(vote == vmacro for vmacro in votemacrolist_48):
                votenumber = 4.8
            elif any(vote == vmacro for vmacro in votemacrolist_42):
                votenumber = 4.2
            elif any(vote == vmacro for vmacro in votemacrolist_4):
                votenumber = 4
            elif any(vote == vmacro for vmacro in votemacrolist_40):
                votenumber = 4.0
            elif any(vote == vmacro for vmacro in votemacrolist_39):
                votenumber = 3.9
            elif any(vote == vmacro for vmacro in votemacrolist_37):
                votenumber = 3.8
            elif any(vote == vmacro for vmacro in votemacrolist_3):
                votenumber = 3
            elif any(vote == vmacro for vmacro in votemacrolist_27):
                votenumber = 2.7
            elif any(vote == vmacro for vmacro in votemacrolist_2):
                votenumber = 2
            elif any(vote == vmacro for vmacro in votemacrolist_18):
                votenumber = 1.8
            elif any(vote == vmacro for vmacro in votemacrolist_16):
                votenumber = 1.6
            elif any(vote == vmacro for vmacro in votemacrolist_11):
                votenumber = 1.1
            elif any(vote == vmacro for vmacro in votemacrolist_1):
                votenumber = 1
            elif any(vote == vmacro for vmacro in votemacrolist_techno):
                votenumber = 5
                extra_message = "Techno! Techno! Techno! Techno!"
            elif any(vote == vmacro for vmacro in votemacrolist_buttes):
                votenumber = 1.1
                extra_message = "Buttes."
            elif any(vote == vmacro for vmacro in votemacrolist_hitler):
                votenumber = 1.8
                extra_message = "shoes heil!"
            elif any(vote == vmacro for vmacro in votemacrolist_pi):
                voterandom = random.randint(1,101)
                if 1 <= voterandom <= 25:
                    votenumber = 3
                if 26 <= voterandom <= 50:
                    votenumber = 3.1
                if 51 <= voterandom <= 75:
                    votenumber = 3.14159
                if 76 <= voterandom <= 90:
                    votenumber = 3.2
                if 91 <= voterandom <= 100:
                    votenumber = 4
            elif any(vote == vmacro for vmacro in votemacrolist_tory):
                votenumber = 2
                extra_message = "Tory scum!"
            elif any(vote == vmacro for vmacro in votemacrolist_weed):
                votenumber = 4.20
            votesuccess = True
        else:
            returnmessage = "That's not a valid vote-macro"
    if votesuccess:
        if votemode == 'normal':
            returnmessage = "You voted "  + str(votenumber) + " on " + songtitle + " by " + artist
        if votemode == 'normal_macro':
            returnmessage = "You voted " + vote + " (" + str(votenumber) + ") " + " on " + songtitle + " by " + artist
        if votemode == 'advanced' or votemode == 'advanced_macro':
            returnmessage = "You voted " + str(vote) + " on " + song[0][2] + " by " + song[0][1]
            print(returnmessage)
        if votemode == 'advanced_macro':
            returnmessage = "You voted " + str(vote) + " (" + str(votenumber) + ") " + " on " + song[0][2] + " by " + song[0][1]
        if len(str(extra_message)) > 1:
            returnmessage = extra_message + "\n" + returnmessage
        voteurl = config.gbsfm_baseurl + '/api/vote?userid=' + str(user_gbsfmid) + '&key=' + user_apikey + '&songid=' + str(song_id) + '&vote=' + str(votenumber)
        vote_request = urllib.request.urlopen(voteurl)
        vote_request.close()
    else:
        returnmessage = "Voting failed. What did you dooooooo?!"
    return  votesuccess, returnmessage

def gbsfm_streampw( getorset ):
    if getorset == 'get':
        query = db.cursor()
        query.execute ("select `value` from playlist_settings WHERE `key`='stream_password'")
        db.commit()
        streampw = query.fetchone()
        passwordstring = 'The livestream-password is: ' + streampw[0]
    elif getorset == 'set':
        streampw = streampw.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(10))
        query = db.cursor()
        query.execute ("UPDATE playlist_settings SET `value`=%s WHERE `key`='stream_password'", (streampw,))
        db.commit()
        passwordstring = 'The livestream-password has been set to: ' + streampw
    return passwordstring

def gbsfm_reactionvote( vote_emoji, message_id, discord_userid_long ):
    votelist_1 = ["6e155540116de9dcf5f233191cce07b0"]
    votelist_2 = ["fd1e1b476fadbaa7125fa9d64b3b7629"]
    votelist_3 = ["66575d5498439e1c15cb5023c22eb808"]
    votelist_4 = ["c97aa9c5a6ba44498d146559094bb14c"]
    votelist_5 = ["736fe4cd17cf2ee08f96c6b607134342"]
    react_fav  = ["6606f5c3e3a2abce20a8e7e0b5060ae1"]
    votelist_combined = votelist_1 + votelist_2 + votelist_3 + votelist_4 + votelist_5 + react_fav
    votenumber = 0

    #Check if the message is voteable
    query = db.cursor()
    query.execute ("select * from discord_botmessages where message_id = %s limit 1", [message_id])
    db.commit()
    queryresult = query.fetchone()

    if queryresult == None:
        queryresult = 'none'
        voteresult = 'unvoteable'
        votestring = 'n/a'
    elif len(queryresult) == 3:
        if any(vote_emoji == emoji for emoji in votelist_combined):
            authbool, user_gbsfmid, user_apikey, user_shortuid, user_longuid = gbsfm_isauthed(discord_userid_long)
            if authbool == 0:
                voteresult = 'not_authed'
                votestring = 'Not authed!'
            elif authbool == 1:
                user_longuid = "<@" + str(discord_userid_long) + ">"
                if any(vote_emoji == emoji for emoji in votelist_1):
                    votenumber = 1
                if any(vote_emoji == emoji for emoji in votelist_2):
                    votenumber = 2
                if any(vote_emoji == emoji for emoji in votelist_3):
                    votenumber = 3
                if any(vote_emoji == emoji for emoji in votelist_4):
                    votenumber = 4
                if any(vote_emoji == emoji for emoji in votelist_5):
                    votenumber = 5
                if any(vote_emoji == emoji for emoji in react_fav):
                    votenumber = 'fav'
        else:
            voteresult = 'unused_emoji'
            votestring = 'n/a'

    if not queryresult == 'none':
        song = gbsfm_query('dongid24no', 0, queryresult[2])

    if votenumber == 'fav':
        favurl = config.gbsfm_baseurl + "/api/favourite?userid=" + str(user_gbsfmid) + "&key=" + user_apikey + "&songid=" + str(queryresult[2])
        try:
            fav_request = urllib.request.urlopen(favurl)
            fav_result = fav_request.read()
            fav_request.close()
            fav_result = fav_result.decode("utf8")
            voteresult = 'fav'
            votestring = user_longuid + ' added ' + song[0][2] + ' by ' + song[0][2] + ' to favourites'
        except urllib.error.HTTPError as error:
            print(error.code)
            print(error.read())
            voteresult = 'error'
            votestring = 'Something went wrong'
    elif votenumber > 0:
        voteurl = config.gbsfm_baseurl + "/api/vote?userid=" + str(user_gbsfmid) + "&key=" + user_apikey + "&songid=" + str(queryresult[2]) + "&vote=" + str(votenumber)
        try:
            vote_request = urllib.request.urlopen(voteurl)
            vote_result = vote_request.read()
            vote_request.close()
            vote_result = vote_result.decode("utf8")
            query = db.cursor()
            query.execute ("SELECT SQL_NO_CACHE cast(avg(score) AS decimal(5,2)) from playlist_rating where song_id = %s", [queryresult[2]])
            db.commit()
            avgvote = query.fetchone()
            print(avgvote[0])
            voteresult = 'vote'
            votestring = user_longuid + ' voted ' + str(votenumber) + ' on ' + song[0][2] + ' by ' + song[0][2] + '. It now has an average vote of ' + str(avgvote[0])
        except urllib.error.HTTPError as error:
            print(error.code)
            print(error.read())
            voteresult = 'error'
            votestring = 'Something went wrong'

    return voteresult, votestring
