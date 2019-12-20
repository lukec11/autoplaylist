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
#import applemusicpy 

from youtube import add_to_youtube, ytAuth
from spotify import addToSpotify

extractor = URLExtract()

#global vars



#Spotify config stuff
with open("config/SPconfig.json") as f:
    spotifyConfig = json.load(f)
    
    spotifyClientId = spotifyConfig["clientID"]
    spotifyClientSecret = spotifyConfig["clientSecret"]
    spotifyBearer = spotifyConfig["bearer"]
    spotifyPlaylistId = spotifyConfig["playlistID"]
    spotifyCtr = spotifyConfig["ctr"]
    spotifyUser = spotifyConfig["spotifyUser"]

#Youtube config stuff
with open("config/YTconfig.json") as f:
    youtubeConfig = json.load(f)

#Apple Music config stuff
with open("config/AMconfig.json") as f:
    appleConfig = json.load(f)
    
with open("config/slack.json") as f:
    slackConfig = json.load(f)
    slackToken = slackConfig["token"]
    slackChannel = slackConfig["channel"]
    slackTeam = slackConfig["team"]
    
    slack_client = slack.WebClient(token = slackToken)
'''
def auth_spotify():
    client_credentials_manager = SpotifyClientCredentials(client_id=spotifyClientId, client_secret=spotifyClientSecret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    sp.user_playlist_add_tracks(spotifyUser, spotifyPlaylistId, "spotify:track:1ru5R5iSawvuMELqKXxLjS"); print ("done")

#Function to add song to Spotify playlist
def add_to_spotify(uri):
    requests.post('https://api.spotify.com/v1/playlists/{}/tracks?position={}&uris={}'.format(spotifyPlaylistId, spotifyCtr, uri),
                   headers = 
                    {'Authorization': spotifyBearer,
                     'Accept': 'application/json',
                     'Content-Type':'application/json' })
    spotifyCtr += 1
    print(spotifyCtr)
    
    with open("config/SPconfig.json") as f:
        json.dump({"clientID":spotifyClientID, "bearer":spotifyBearer, "playlistID":spotifyPlaylistId, "ctr":spotifyCtr}, f, indent=4)
    
    print ("Added to Spotify playlist.")
'''
#Function to add song to Apple Music playlist
def add_to_apple(songID):
    requests.post(
                    "https://api.music.apple.com/v1/me/library/playlists/{}/tracks".format(appleConfig["playlistID"]),
                    {"data": [{"id": songID, "type": "songs"}]}
                )
    
    print("Added to Apple Music playlist.")

def slack_response(message, userID): #method to post a (parameter) message to slack, visible to channel
    print ("Sending slack response.")
    
    message = ("{}".format(message))
    slack_client.chat_postMessage(token = slackToken, 
                                    as_user=False, 
                                    channel=slackChannel, 
                                    text=message 
    )
                                    #user=userID
    
def slack_ephemeral(message, userID): #method to post an ephemeral message to the chat - only the user will see it
    
    message = ("{}".format(message))
    slack_client.chat_postEphemeral(token = slackToken,
                                    as_user=False, 
                                    channel=slackChannel, 
                                    text=message, 
                                    user=userID
    )
                                

def interpret_song(url, user, origin): #passes the song info to song.link to get information
    try:
        song = (requests.get('https://api.song.link/v1-alpha.1/links?url={}'.format(url)).content)
        links = json.loads(song)
        
        #Access the non-unique platform portions for each, part II of the API
        spotify = links.get('entitiesByUniqueId').get(links.get('linksByPlatform').get('spotify').get('entityUniqueId')) 
        youtube = links.get('entitiesByUniqueId').get(links.get('linksByPlatform').get('youtube').get('entityUniqueId'))
        applemusic = links.get('entitiesByUniqueId').get(links.get('linksByPlatform').get('appleMusic').get('entityUniqueId'))
        
        #Accesses sections fully unique to each part of the ID - Part I
        youtubeID = str(youtube.get('id'))
        spotifyID = ("spotify:track:" + str(spotify.get('id'))) 
        applemusicID = str(applemusic.get('id'))
        
        artist = str(applemusic.get('artistName')) #Pulls artist name
        title = str(applemusic.get('title')) #Pulls song name
        
        isDupe = addToSpotify(spotifyID)
        #add_to_apple(applemusicID) # Function deprecated due to Apple Music's $99 fee :(
        
        
        if not isDupe:
            add_to_youtube(ytAuth(), youtubeID)
        elif isDupe:
            print ("Not added to youtube, because it is a duplicate. [Sign main]") #logs to console when method is a duplicate
        
        if not isDupe:
            slack_response(f" <@{user}> added to the playlist: `{title}` by `{artist}` !", user) #logs publically to slack when message posted
        elif isDupe:
            slack_ephemeral(f"`{title}` by `{artist}` is already in the playlist!", user) #logs privately to user if song is a duplicate
        return {
                "youtubeID": youtubeID, 
                "spotifyID": spotifyID, 
                "applemusicID": applemusicID, 
                "artist": artist, 
                "title": title
            }
    except SyntaxError:
        slack_ephemeral("The song that you linked was not recognized.", user)
        print ("Song wasn't recognized, or something else broke.") # ¯\_(ツ)_/¯
        
        return {} #returns empty dictionary
    except AttributeError:
        slack_ephemeral("Autoplaylist has been rate limited, or it didn't recognize your song. Try using `/song title` or `/song artist - title` to add it manually.", user)
        print ("Rate limited, message posted.")

        return {} #returns empty dictionary

@slack.RTMClient.run_on(event="message") #Slack listens in pre-defined channel for posted links.
def message_on(**payload):
    
    data = payload['data']
    web_client = payload['web_client']
    try: 
        if extractor.has_urls(data['text']):
            link = list(extractor.find_urls(data['text']))[0]
            interpret_song(link,data['user'], 'rtm')
            
    except KeyError:
        print("Text got deleted, or extractor messed up again.")
    
slack_token = slackToken #This stuff needs to actually stay here, for slack to listen! Do not delete
rtm_client = slack.RTMClient(token=slack_token)
rtm_client.start()
