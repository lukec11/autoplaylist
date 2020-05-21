import json
import slack
import requests
import jsonify
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from urlextract import URLExtract
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from time import sleep

from youtube import add_to_youtube, ytAuth
from spotify import addToSpotify


# Spotify config stuff
with open("config/SPconfig.json") as f:
    spotifyConfig = json.load(f)

    spotifyClientId = spotifyConfig["clientID"]
    spotifyClientSecret = spotifyConfig["clientSecret"]
    spotifyBearer = spotifyConfig["bearer"]
    spotifyPlaylistId = spotifyConfig["playlistID"]
    spotifyCtr = spotifyConfig["ctr"]
    spotifyUser = spotifyConfig["spotifyUser"]

# Youtube config stuff
with open("config/YTconfig.json") as f:
    youtubeConfig = json.load(f)

with open("config/slack.json") as f:
    slackConfig = json.load(f)
    slackToken = slackConfig["token"]
    slackChannel = slackConfig["channel"]
    slackTeam = slackConfig["team"]

slack_client = slack.WebClient(token=slackToken)
extractor = URLExtract()  # declare extractor for later

# method to post a (parameter) message to slack, visible to channel


def slack_response(message, userID):
    print("Sending slack response.")

    message = ("{}".format(message))
    slack_client.chat_postMessage(token=slackToken,
                                  as_user=False,
                                  channel=slackChannel,
                                  text=message
                                  )


# method to post an ephemeral message to the chat - only the user will see it
def slack_ephemeral(message, userID):

    message = ("{}".format(message))
    slack_client.chat_postEphemeral(token=slackToken,
                                    as_user=False,
                                    channel=slackChannel,
                                    text=message,
                                    user=userID
                                    )


# passes the song info to song.link to get information
def interpret_song(url, user, origin):
    try:
        song = requests.get(
            f'https://api.song.link/v1-alpha.1/links?url={url}').content
        links = json.loads(song)

        # Access the non-unique platform portions for each, part II of the API
        spotify = links.get('entitiesByUniqueId').get(
            links.get('linksByPlatform').get('spotify').get('entityUniqueId'))
        youtube = links.get('entitiesByUniqueId').get(
            links.get('linksByPlatform').get('youtube').get('entityUniqueId'))
        applemusic = links.get('entitiesByUniqueId').get(
            links.get('linksByPlatform').get('appleMusic').get('entityUniqueId'))

        # Accesses sections fully unique to each part of the ID - Part I
        youtubeID = str(youtube.get('id'))
        spotifyID = ("spotify:track:" + str(spotify.get('id')))
        applemusicID = str(applemusic.get('id'))

        artist = str(spotify.get('artistName'))  # Pulls artist name
        title = str(applemusic.get('title'))  # Pulls song name

        isDupe = addToSpotify(spotifyID)

        if not isDupe:
            add_to_youtube(ytAuth(), youtubeID)
        elif isDupe:
            # logs to console when method is a duplicate
            print(f"INFO: Song {title} is duplicate, not added. [Main]")

        if not isDupe:
            # logs publically to slack when message posted
            slack_response(
                f" <@{user}> added to the playlist: `{title}` by `{artist}` !", user)
        elif isDupe:
            # logs privately to user if song is a duplicate
            slack_ephemeral(
                f"`{title}` by `{artist}` is already in the playlist!", user)
        return {
            "youtubeID": youtubeID,
            "spotifyID": spotifyID,
            "applemusicID": applemusicID,
            "artist": artist,
            "title": title
        }
    except SyntaxError as s:
        slack_ephemeral("The song that you linked was not recognized.", user)
        print(f"WARNING: SyntaxError - {s}")

        return {}  # returns empty dictionary
    except AttributeError as a:
        print(f"WARNING: AttributeError: {a}")
        slack_ephemeral("Your song was not found! If you've linked many songs recently, please wait 60 seconds, you may be rate-limited. If you didn't link a song, please ignore this message and it will disappear automatically.", user)
        print("Rate limited or not found, message posted.")

        return {}  # returns empty dictionary

# Slack listens in pre-defined channel for posted links.
@slack.RTMClient.run_on(event="message")
def message_on(**payload):

    data = payload['data']
    web_client = payload['web_client']
    try:
        if extractor.has_urls(data['text']):
            link = list(extractor.find_urls(data['text']))[0]
            print(f"User printed text: {data['text']}")
            interpret_song(link, data['user'], 'rtm')
    except KeyError as k:
        print(f"WARNING: KeyError from RTM! {k}")


# This stuff needs to actually stay here, for slack to listen! Do not delete
slack_token = slackToken
rtm_client = slack.RTMClient(token=slack_token)
rtm_client.start()
