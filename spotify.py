import sys
import spotipy
import spotipy.util
import json

with open("config/SPconfig.json") as f:
    spotifyConfig = json.load(f)
    
    spotifyClientId = spotifyConfig["clientID"]
    spotifyClientSecret = spotifyConfig["clientSecret"]
    spotifyBearer = spotifyConfig["bearer"]
    spotifyPlaylistId = spotifyConfig["playlistID"]
    spotifyCtr = spotifyConfig["ctr"]
    spotifyUser = spotifyConfig["spotifyUser"]
    


def addToSpotify(uuid):
    uid = [uuid] #This converts the UID string into a list, because spotipy api only accepts inputs as lists.
    
    scope = 'playlist-modify-public' #Describes the scope necessary, so spotify API can authorize.

    if (len(sys.argv) > 1): #stuff that spotipy uses - leaving it here so stuff doesn't break
        username = sys.argv[1]
    else:
        ("Usage: {} username".format(sys.argv[0])) #This is entirely irrelevant, but the code doesn't run without it.

    token = spotipy.util.prompt_for_user_token(spotifyUser,
                                               scope,
                                               client_id=spotifyClientId,
                                               client_secret=spotifyClientSecret,
                                               redirect_uri='http://localhost:9898/spotifyCallback'
                                               ) #Authorizes with Spotify using OAuth


    if token: #Adds song to playlist
        sp = spotipy.Spotify(auth=token)
        sp.trace = False #idk what this does but the docs told me to do it
        results = sp.user_playlist_add_tracks(spotifyUser, 
                                              spotifyPlaylistId, 
                                              uid
                                              ) #Adds song to said playlist
        print (results) #logs snapshot to console
        print ("Added to spotify playlist.")
    else:
        print ("CATCH HERE! Couldn't get token.") 
        
