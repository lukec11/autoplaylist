# Written by Luke Carapezza (@lukec11), December 2019

import sys
import spotipy
import spotipy.util
import json
from flask import Flask, request, abort, Response
import jsonify

# imports methods from main
from main import interpret_song, slack_ephemeral

# import for flask
import traceback
from werkzeug.wsgi import ClosingIterator


class AfterResponse:
    def __init__(self, app=None):
        self.callbacks = []
        if app:
            self.init_app(app)

    def __call__(self, callback):
        self.callbacks.append(callback)
        return callback

    def init_app(self, app):
        # install extension
        app.after_response = self

        # install middleware
        app.wsgi_app = AfterResponseMiddleware(app.wsgi_app, self)

    def flush(self):
        for fn in self.callbacks:
            try:
                fn()
            except Exception:
                traceback.print_exc()


class AfterResponseMiddleware:  # credit Matthew Story @ Stackoverflow
    def __init__(self, application, after_response_ext):
        self.application = application
        self.after_response_ext = after_response_ext

    def __call__(self, environ, after_response):
        iterator = self.application(environ, after_response)
        try:
            return ClosingIterator(iterator, [self.after_response_ext.flush])
        except Exception:
            traceback.print_exc()
            return iterator

    spotifyConfig = os.environ
    spotifyClientId = spotifyConfig["spotify_clientID"]
    spotifyClientSecret = spotifyConfig["spotify_clientSecret"]
    spotifyBearer = spotifyConfig["spotify_bearer"]
    spotifyPlaylistId = spotifyConfig["spotify_playlistID"]
    spotifyCtr = spotifyConfig["spotify_ctr"]
    spotifyUser = spotifyConfig["spotify_spotifyUser"]
    slackTeamId = spotifyConfig["slack_team"]
    slackToken = spotifyConfig["slack_verificationToken"]


def searchSpotify(vquery):

    # global vars
    global username
    query = [vquery]  # converts UID string to list; spotipy only accepts lists
    scope = 'playlist-modify-public'  # spotipy API scpoe

    if (len(sys.argv) > 1):
        username = sys.argv[1]
    else:
        # This is entirely irrelevant, but the code doesn't run without it.
        ("Usage: {} username".format(sys.argv[0]))

    token = spotipy.util.prompt_for_user_token(spotifyUser,  # prompts for spotify user token, so it can access the api
                                               scope,
                                               client_id=spotifyClientId,
                                               client_secret=spotifyClientSecret,
                                               redirect_uri='http://localhost:9898/spotifyCallback'
                                               )  # Authorizes with Spotify using OAuth
    sp = spotipy.Spotify(auth=token)
    sp.trace = False  # idk what this does but the docs told me to do it
    try:
        tracks = sp.search(query, limit=1, offset=0, type="track", market=None)
        tracks2 = tracks.get('tracks').get('items')[0].get('uri')
        return tracks2
    except (IndexError or AttributeError) as e:
        # returns ephemeral message to user
        slack_ephemeral(
            'We couldn\'t find this track! Try searching in a different format, e.g. "artist - title"', username)
        # logs output to console for debug
        print(f"DEBUG: Served response: NOT FOUND - {e}")

        return "NotFound"


# flask stuff to accept slack slash commands
app = Flask("after_response")
AfterResponse(app)  # calls AfterResponse after flask app

# initializes strings to blank by default
username = ""
text = ""


def request_valid(request):
    slackToken = request.form['token']
    # slackTeamId = request.form['team-id']
    return slackToken


@app.after_response
def after_request_function():
    # global vars
    global username
    global text
    song = str(text)
    print(f"INFO: User {username} requested the song \"{song}\".")
    # runs interpretation with info from spotify - slack serve call there
    searchSong = searchSpotify(song)
    try:
        interpret_song(searchSpotify(song), username, 'cmd')
    except:
        slack_ephemeral(
            'Sorry, we weren\'t able to get matadata for that song :(', username)


@app.route('/songadd', methods=['POST'])
def songadd():
    if not request_valid(request):
        print('NOT VALID!')
        abort(400)
    # global vars
    global username
    global text
    # gets vars based on slack's post
    username = request.form.get('user_id')
    text = request.form.get('text')
    # returns early response, to avoid slack timeout reply - empty 200
    return ('', 200)


# flask stuff that runs web server

print('Starting flask server!')
app.run(host='0.0.0.0', debug=False, port=3000)
