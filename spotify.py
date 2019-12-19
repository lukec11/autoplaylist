#Written by Luke Caraprzza (@lukec11) and Harshith Iyer (@harbar20), December 2019
import sys
import spotipy
import spotipy.util
import json


#global vars
isDuplicate = False #Initializes to false by default, will be set to true below if it is a duplicate

with open("config/SPconfig.json") as f:
    spotifyConfig = json.load(f)
    
    spotifyClientId = spotifyConfig["clientID"]
    spotifyClientSecret = spotifyConfig["clientSecret"]
    spotifyBearer = spotifyConfig["bearer"]
    spotifyPlaylistId = spotifyConfig["playlistID"]
    spotifyCtr = spotifyConfig["ctr"]
    spotifyUser = spotifyConfig["spotifyUser"]

def spDupeChecker(tracks, uuid):
    for trackInfo in tracks["items"]: #Loops through all the tracks to check if the inputted track is already in the playlist
        id = "spotify:track:"+trackInfo["track"]["id"]
        if uuid == id:
            return True #returns true if it finds a duplicate while looping through the playlist
        else:
            alreadyInPlaylist = False
        
    return alreadyInPlaylist #Returns False if alreadyInPlaylist hasn't been returned to be true

def addToSpotify(uuid):
    uid = [uuid] #This converts the UID string into a list, because spotipy api only accepts inputs as lists.
    
    #global vars
    global isDuplicate
    
    scope = 'playlist-modify-public' #Describes the scope necessary, so spotify API can authorize.

    if (len(sys.argv) > 1): #stuff that spotipy uses - leaving it here so stuff doesn't break
        username = sys.argv[1]
    else:
        ("Usage: {} username".format(sys.argv[0])) #This is entirely irrelevant, but the code doesn't run without it.

    token = spotipy.util.prompt_for_user_token(spotifyUser, #prompts for spotify user token, so it can access the api
                                               scope,
                                               client_id=spotifyClientId,
                                               client_secret=spotifyClientSecret,
                                               redirect_uri='http://localhost:9898/spotifyCallback'
                                               ) #Authorizes with Spotify using OAuth

    if token: #Adds song to playlist
        sp = spotipy.Spotify(auth=token)
        sp.trace = False #idk what this does but the docs told me to do it
        
        tracks = sp.user_playlist_tracks(spotifyUser, spotifyPlaylistId, limit=100) #Gets all tracks in the playlist
        
        alreadyInPlaylist = spDupeChecker(tracks, uuid) #Checks for duplicate tracks in the playlist
        if not alreadyInPlaylist:
            results = sp.user_playlist_add_tracks(spotifyUser, 
                                              spotifyPlaylistId, 
                                              uid
                                              ) #Adds song to said playlist
            #print (results) #logs snapshot to console
            print ("Added to spotify playlist.")
            isDuplicate = False
        else:
            print("I'm sorry, this song is already in the playlist.")
            isDuplicate = True
            
            
    else:
        print ("CATCH HERE! Couldn't get token.") 
    
    return isDuplicate

#addToSpotify("spotify:track:2g2a5kDeZexbUTD8abcvm6")