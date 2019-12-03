import json
import slack
import requests
import jsonify
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from urlextract import URLExtract

from youtube import add_to_youtube, ytAuth

extractor = URLExtract()

#Spotify config stuff
with open("config/SPconfig.json") as f:
    spotifyConfig = json.load(f)
    
    spotifyClientID = spotifyConfig["clientID"]
    spotifyBearer = spotifyConfig["bearer"]
    spotifyPlaylistId = spotifyConfig["playlistID"]
    spotifyCtr = spotifyConfig["ctr"]

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

#Function to add song to Apple Music playlist
def add_to_apple(songID):
    requests.post(
                    "https://api.music.apple.com/v1/me/library/playlists/{}/tracks".format(appleConfig["playlistID"]),
                    {"data": [{"id": songID, "type": "songs"}]}
                )
    
    print("Added to Apple Music playlist.")

def slack_response(song, userID):
    print ("Sending slack response.")
    
    message = ("{}".format(song))
    slack_client.chat_postEphemeral(token = slackToken,
                                    as_user=True, 
                                    channel=slackChannel, 
                                    text=message, 
                                    user=userID
                                )

def interpret_song(url, user):
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
        
        add_to_spotify(spotifyID)
        add_to_apple(applemusicID)
        add_to_youtube(ytAuth(), youtubeID)

        slack_response(("{} by {} was added to the playlist.").format(title, artist), user)
        
        return {
                "youtubeID": youtubeID, 
                "spotifyID": spotifyID, 
                "applemusicID": applemusicID, 
                "artist": artist, 
                "title": title
            }
    except:
        slack_response("The song that you linked was not recognized.", user)
        return {}
 

@slack.RTMClient.run_on(event="message")
def message_on(**payload):
    print ("Message sent in channel.")
    data = payload['data']
    web_client = payload['web_client']
    
    try: 
        if extractor.has_urls(data['text']):
            link = list(extractor.find_urls(data['text']))[0]
            interpret_song(link,data['user'])
    except KeyError:
        print("Text got deleted.")
    
slack_token = slackToken #This stuff needs to actually stay here, for slack to listen! Do not delete
rtm_client = slack.RTMClient(token=slack_token)
rtm_client.start()

#print (interpret_song('https://music.apple.com/us/album/thunder/1411625594?i=1411629089&app=music&ign-mpt=uo%3D4'))


#i love this song' https://music.apple.com/us/album/thunder/1411625594?i=1411629089&app=music&ign-mpt=uo%3D4, it's really amazing and it's good'
