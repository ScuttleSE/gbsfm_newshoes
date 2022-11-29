#!/usr/bin/env python

import config
import discord
import gbsfm
import asyncio
import hashlib
import ai
import wa
import playing
import subprocess

print(config.discord_application_id)

#Defining Discord client
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)

#Waiting for the bot to log in
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)

#Define various triggers and wordlists
#Words that are a command in and of itself
wordlist_stoat_list            = ["!stoats", "!voles", "!weasels", "!watervoles", "!otters", \
                                  "!polecats", "!badgers", "!wolverines", "!ferrets"]
wordlist_roles                 = ["!addrole", "!removerole", "!listroles"]
wordlist_tokens                = ["!givetokens", "!tokens", "!toucans"]
wordlist_jingle                = ["!jingle2"]
wordlist_when                  = ["@when"]
wordlist_system                = ["!restartbot", "!restartlinkbot", "!restartftp", "!restartirc"]
wordlist_wa                    = ["@wa"]
wordlist_vote_list             = ["@v", "@vote"]
wordlist_stream                = ["!newstreampw", "!getstreampw"]
wordlist_comment               = ["@comment"]
wordlist_hitorshit             = ["!hit", "!shit"]
wordlist_youtubedl             = ["!youtube", "!ytdl"]
wordlist_faves                 = ["@fav", "@wuv"]
wordlist_botid                 = ["<@503268924876652544>"] # Discord id for the bot

standalone_wordlist_all        = wordlist_stoat_list + wordlist_roles + wordlist_tokens + wordlist_jingle + wordlist_when + wordlist_system + wordlist_wa + wordlist_vote_list + wordlist_stream + wordlist_comment + wordlist_hitorshit + wordlist_youtubedl + wordlist_faves

#Triggerwords for add-commands
wordlist_commandtriggers       = ("@a ", "@add ")

#Add commands
wordlist_addlist_anyunplayed   = ["anyunplayed", "aup"]
wordlist_addlist_random        = ["random"]
wordlist_addlist_unplayed      = ["unplayed", "up"]
wordlist_addlist_userany       = ["me"]
wordlist_addlist_faves         = ["fav"]
wordlist_addlist_short         = ["sup"]
wordlist_addlist_genre         = ["g", "genre"]

#Various strings and stuff
string_not_authed_response     = 'Not authed!'
list_roles_give_tokens         = ['503240105776119812']
list_roles_play_jingle         = ['503240105776119812']
list_roles_system              = ['503240105776119812', '503250808503009281']
token_response_no_allowed      = 'You are not allowed to give out tokens!'
string_available_roles         = "Currently available roles:\n He/Him - he_him\nShe/Her - she_her\nThey/Them - they_them\nSyntax is \"!addrole he_him\""
string_role_added              = "Role added.\nIf you want to remove a role, use the command !removerole <role>"
string_role_removed            = "Role removed.\nIf you want to add a role, use the command !addrole <role>"
string_unknown_role            = "Unknown role\nIf it is a role you feel should be added, contact an admin"
string_jingle_deny             = "Thou shall not add jingles!"
string_restartdiscord          = "Restarting myself..."
string_restartlinkbot          = "Restarting IRC linkbot..."
string_restartftp              = "Restarting FTP..."
string_restartircbot           = "Restarting irc-bot..."
string_no_restart              = "You're not allowed to fiddle with that. Get an admin to help."
string_streampw_denied         = "You are not allowed to fiddle with the livestream password! Get an admin to help"

#Check if a string can be converted into a int
def check_int(potential_int):
    try:
        int(potential_int)
        return True
    except ValueError:
        return False

#This is a task that updates the "playing" part of the bot
async def update_playing():
    playing_now = 'NULL'
    playing_prev = 'NULL2'
    await client.wait_until_ready()
    while not client.is_closed():
        nowplaying = gbsfm.gbsfm_nowplaying()
        playing_now = nowplaying[2] + " (" + nowplaying[3] + ") - " + nowplaying[1]
        #print ("Query is: ", playing_now)
        #Unless the same song is playing as the last time we checked, change "game"
        if not playing_now == playing_prev:
            playing_prev = playing_now
            displayplaying = discord.Game(name=playing_now)
            await client.change_presence(status=discord.Status.idle, activity=displayplaying)
        #Sleep for 10 seconds, then repeat
        await asyncio.sleep(10)

# ---------- Here we start the event listener

@client.event
async def on_message(message):
    #Debug
    #print(message.content)
    if message.author == client.user: #Don't respond to my own messages
        return
    if str(message.author.id) in config.discord_ignored_ids: #Don't respond to these user ids
        return
    if str(message.channel.id) in config.discord_ignored_channel_ids: #Don't respond to these channel ids
        return

    #Here begins general commandtriggers
    if message.content.startswith(wordlist_commandtriggers):
        authbool, user_gbsfmid, user_apikey, user_shortuid, user_longuid = gbsfm.gbsfm_isauthed(message.author.id)
        if authbool == 0:
            await message.channel.send(string_not_authed_response)
            return

        #The user is eligible to run commands, set up a few things we may need
        user_longuid = "<@" + str(message.author.id) + ">"
        string_noplayable = "Sorry " + user_longuid + ", there are no playable dongs."
        add_line = message.content.split(" ", 1)
        add_command = add_line[1]

        #If we just got "@a" without anything else, just ignore it
        if add_command == None:
            return

        #Add any unplayed song
        if any(add_command == word for word in wordlist_addlist_anyunplayed):
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('aup', user_gbsfmid, user_apikey, user_longuid, 0)

        #Add song from genre
        if add_command[0] == "&":
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('genre', user_gbsfmid, user_apikey, user_longuid, add_command[1:])

        #Add any random song
        if any(add_command == word for word in wordlist_addlist_random):
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('random', user_gbsfmid, user_apikey, user_longuid, 0)

        #Add any unplayed song uploaded by the user
        if any(add_command == word for word in wordlist_addlist_unplayed):
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('unplayed', user_gbsfmid, user_apikey, user_longuid, 0)

        #Add any song uploaded by the user
        if any(add_command == word for word in wordlist_addlist_userany):
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('userany', user_gbsfmid, user_apikey, user_longuid, 0)

        #Add fave
        if any(add_command == word for word in wordlist_addlist_faves):
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('faves', user_gbsfmid, user_apikey, user_longuid, 0)

        #Add album title
        if add_command[0] == "#":
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('album', user_gbsfmid, user_apikey, user_longuid, add_command[1:])

        #Add artist
        if add_command[0] == "/":
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('artist', user_gbsfmid, user_apikey, user_longuid, add_command[1:])

        #Add artistid
        if add_command[0] == "\\":
                add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('artistid', user_gbsfmid, user_apikey, user_longuid, add_command[1:])

        #Add title
        if add_command[0] == "!":
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('title', user_gbsfmid, user_apikey, user_longuid, add_command[1:])

        #Add user
        if add_command[0] == ":":
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('user', user_gbsfmid, user_apikey, user_longuid, add_command[1:])

        #Add short dong
        if any(add_command == word for word in wordlist_addlist_short):
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('sup', user_gbsfmid, user_apikey, user_longuid, 10)

        #Add by dong id
        if add_command.isnumeric():
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('dongid', user_gbsfmid, user_apikey, user_longuid, add_command)

        #Add another users faves
        if add_command.startswith('<@'):
            add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('otherfav', user_gbsfmid, user_apikey, user_longuid, add_command)

        #Send response message
        if add_success == 1:
            msgid = await message.channel.send(str_addmessage)
            gbsfm.gbsfm_add_botmessage(msgid.id, added_songid)
        if add_success == 0:
            msgid = await message.channel.send(str_addmessage)

    #Other commands
    if any(message.content.startswith(word) for word in standalone_wordlist_all):
        authbool, user_gbsfmid, user_apikey, user_shortuid, user_longuid = gbsfm.gbsfm_isauthed(message.author.id)
        if authbool == 0:
            await message.channel.send(string_not_authed_response)
            return
        #Stoat-stats
        if any(message.content.startswith(word) for word in wordlist_stoat_list):
            await message.author.send(gbsfm.gbsfm_stoats(user_gbsfmid))
        #Fav current song
        if any(message.content.startswith(word) for word in wordlist_faves):
            await message.channel.send(gbsfm.gbsfm_addfav(user_gbsfmid, user_longuid))
        #Add/remove/list role(s)
        if any(message.content.startswith(word) for word in wordlist_roles):
            if message.content.startswith('!listroles'):
                await message.author.send(string_available_roles)
                return
            rolemessage = message.content.split()
            role = 0
            if rolemessage[1] == "he_him":
                role = 805517499063468094
            if rolemessage[1] == "she_her":
                role = 805517609310355456
            if rolemessage[1] == "they_them":
                role = 805517633658945576
            if rolemessage[1] == "sickos":
                role = 805749035037622322
            if role != 0:
                role = discord.utils.get(message.guild.roles, id=role)
                if message.content.startswith('!addrole'):
                    await message.author.add_roles(role)
                    await message.author.send(string_role_added)
                if message.content.startswith('!removerole'):
                    await message.author.remove_roles(role)
                    await message.author.send(string_role_removed)
            else:
                await message.author.send(string_unknown_role)
        #Give tokens
        if any(message.content.startswith(word) for word in wordlist_tokens):
            if message.content.startswith('!givetokens'):
                valid_group = 0
                for role in message.author.roles:
                    if str(role.id) in list_roles_give_tokens: #Needed role to give tokens
                        valid_group = 1
                        token_message = message.content.split()
                        if len(token_message) == 3:
                            token_recipient = token_message[1][2:len(token_message[1])-1]
                            if token_recipient[:1] == "!":
                                token_recipient = token_recipient[1:len(token_recipient)]
                            token_recipient_short = str(message.mentions[0])
                            token_amount = token_message[2]
                            print(token_recipient)
                            token_response = gbsfm.gbsfm_givetokens(token_recipient, token_recipient_short, token_amount)
                            await message.channel.send(token_response)
                        else:
                            print(token_message)
                if valid_group == 0:
                    await message.channel.send(token_response_no_allowed)
            #Check tokens
            else:
                user_longuid = "<@" + user_longuid + ">"
                token_response = gbsfm.gbsfm_gettokens(user_gbsfmid, user_longuid)
                await message.channel.send(token_response)
        #Play jingle
        if any(message.content.startswith(word) for word in wordlist_jingle):
            valid_group = 0
            for role in message.author.roles:
                    if str(role.id) in list_roles_play_jingle: #Needed role to play jingle
                        valid_group = 1
                        user_longuid = "<@" + str(user_longuid) + ">"
                        add_success, str_addmessage, added_songid = gbsfm.gbsfm_jingle(user_longuid)
                        if add_success == 1:
                            msgid = await message.channel.send(str_addmessage)
                            gbsfm.gbsfm_add_botmessage(msgid.id, added_songid)
                        if add_success == 0:
                            msgid = await message.channel.send(str_addmessage)
            if valid_group == 0:
                await message.channel.send(string_jingle_deny)
        #Check when your next dong is playing
        if any(message.content.startswith(word) for word in wordlist_when):
            result, reponsemessage = gbsfm.gbsfm_when(user_gbsfmid)
            await message.channel.send(reponsemessage)
        #Restart stuff
        if any(message.content.startswith(word) for word in wordlist_system):
            valid_group = 0
            for role in message.author.roles:
                    if str(role.id) in list_roles_system: #Needed role to restart shit
                        valid_group = 1
            if valid_group == 1:
                if message.content.startswith('!restartbot'):
                    await message.channel.send(string_restartdiscord)
                    subprocess.run(['curl', '-s', 'http://controller/restart-discordbot.sh'])
                elif message.content.startswith('!restartlinkbot'):
                    await message.channel.send(string_restartlinkbot)
                    subprocess.run(['curl', '-s', 'http://controller/restart-linkbot.sh'])
                elif message.content.startswith('!restartftp'):
                    await message.channel.send(string_restartftp)
                    subprocess.run(['curl', '-s', 'http://controller/restart-ftp.sh'])
                elif message.content.startswith('!restartirc'):
                    await message.channel.send(string_restartircbot)
                    subprocess.run(['curl', '-s', 'http://controller/restart-ircbot.sh'])
            else:
                await message.channel.send(string_no_restart)
        #Wolfram Alpha
        if any(message.content.startswith(word) for word in wordlist_wa):
            waquery = message.content.split(" ", 1)
            await message.channel.send(wa.wa_query(waquery[1]))
        #Voting
        if any(message.content.startswith(word) for word in wordlist_vote_list):
            voteparts = message.content.split(" ")
            votesuccess, returnmessage = gbsfm.gbsfm_vote(voteparts[1:], user_gbsfmid, user_apikey)
            await message.channel.send(returnmessage)
        #Stream password stuff
        if any(message.content.startswith(word) for word in wordlist_stream):
            valid_group = 0
            for role in message.author.roles:
                    if str(role.id) in list_roles_system: #Needed role to restart shit
                        valid_group = 1
            if valid_group == 1:
                if message.content.startswith('!newstreampw'):
                    streampw = gbsfm.gbsfm_streampw('set')
                if message.content.startswith('!getstreampw'):
                    streampw = gbsfm.gbsfm_streampw('get')
                await message.author.send(streampw)
            else:
                await message.channel.send(string_streampw_denied)
        #Hit or shit
        if any(message.content.startswith(word) for word in wordlist_hitorshit):
            user_longuid = "<@" + str(user_longuid) + ">"
            if message.content.startswith('!hit'):
                #print('fart')
                add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('highrating', user_gbsfmid, user_apikey, user_longuid, 4.8)
            elif message.content.startswith('!shit'):
                add_success, str_addmessage, added_songid = gbsfm.gbsfm_play('lowrating', user_gbsfmid, user_apikey, user_longuid, 2)
            if add_success == 1:
                msgid = await message.channel.send(str_addmessage)
                gbsfm.gbsfm_add_botmessage(msgid.id, added_songid)
            if add_success == 0:
                msgid = await message.channel.send(str_addmessage)
        #Youtube download
        if any(message.content.startswith(word) for word in wordlist_youtubedl):
            msgparts = message.content.split(" ")
            youtubelink = msgparts[1]
            print(youtubelink)
            dl_success, msg = gbsfm.gbsfm_ytdlsong(user_gbsfmid, user_apikey, youtubelink)
            await message.channel.send(msg)
    if message.content.startswith('!idcheck'):
        print('farts')
        valid_group = 0
        for role in message.author.roles:
            if str(role.id) in list_roles_system: #Needed role to restart shit
                valid_group = 1
        if valid_group == 1:
            content = message.content.split(' ')
            #user = await client.fetch_user(int(content))
            #print(user)
            print(content[1][3:30])
        else:
            await message.channel.send('Denied')
    #OpenAI
    if any(message.content.startswith(word) for word in wordlist_botid):
        aiquery = message.content.split(" ", 1)
        await message.channel.send(ai.ai_query(aiquery[1]))

#Stuff you can do un-authed

    #Playing?
    if "playing?" in message.content.lower():
        artwork, textreply, songid = playing.playingquestion()
        em_art = discord.Embed(url=artwork)
        msgid = await message.channel.send(artwork)
        gbsfm.gbsfm_add_botmessage(msgid.id, songid)
        msgid = await message.channel.send(textreply)
        gbsfm.gbsfm_add_botmessage(msgid.id, songid)

    #Authing
    if message.content.startswith('!auth'):
        newmessage = message.content.split()
        authid = newmessage[1]
        auth_success, auth_message = gbsfm.gbsfm_auth(authid, str(message.author), str(message.author.id))
        await message.channel.send(auth_message)

#Vote by reacting 1-5 on the dong
@client.event
async def on_raw_reaction_add(reaction):
    vote_emoji = hashlib.md5(reaction.emoji.name.encode("utf-8")).hexdigest()
    voteresult, votestring = gbsfm.gbsfm_reactionvote( vote_emoji, str(reaction.message_id), reaction.user_id)
    print(voteresult)
    if not (voteresult == 'unvoteable' or voteresult == 'unused_emoji'):
        channel = client.get_channel(reaction.channel_id)
        await channel.send(votestring)

 #This updates the "game" the bot is playing with the current song
#client.loop.create_task(update_playing())

client.run(config.discord_bot_token)
