import os
import flask
import requests
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

with open("config/YTconfig.json") as f:
    YTconfig = json.load(f)
    secret_key = YTconfig["secret_key"]

CLIENT_SECRETS_FILE="config/client-secret-new.json"

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

app = flask.Flask(__name__)

app.secret_key=(secret_key)

def add_to_youtube(youtube, videoID):
    playlist_id = YTconfig["playlist_id"]
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
        "snippet": {
            "playlistId": "PLn2UD6MgJEciaVCIC4WpA3jnvCWaZpng3",
            "resourceId": {
            "kind": "youtube#video",
            "videoId": videoID
            }
        }
        }
    )
    response = request.execute()
    
    with open("ytPlaylist.json", 'w') as f:
        json.dump(response, f, indent=4)
    print("Added to Youtube Playlist.")

def ytAuth():
    session1 = flask.session
    with open("config/ytAuth.json") as f:
        ytAuthJson = json.load(f)
        credentials_dict = ytAuthJson['credentials']
    
    credentials = google.oauth2.credentials.Credentials(
        credentials_dict["token"],
        refresh_token = credentials_dict["refresh_token"],
        token_uri = credentials_dict["token_uri"],
        client_id = credentials_dict["client_id"],
        client_secret = credentials_dict["client_secret"],
        scopes = credentials_dict["scopes"]
    )

    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    
    return youtube

@app.route('/app')
def program():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    
    with open("config/ytAuth.json", "w") as f:
        json.dump({"credentials": dict(flask.session['credentials']), "state":flask.session['state']}, f, indent=4)

    #print(flask.session)
    #youtube = ytAuth()
    #add_to_youtube(youtube, "Ezf0tKJ6mWg")
    
    return ("Added!") #You are using flask so if you want to show something in the web page here you have to return it, not print it

@app.route('/authorize') #This function was stolen from google. Thanks google.
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
    # Enable offline access so that you can refresh an access token without
    # re-prompting the user for permission. Recommended for web server apps.
    access_type='offline',
    # Enable incremental authorization. Recommended as a best practice.
    include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state
    #session1['state'] = state
    
    #with open("config/ytAuth.json", "w") as f:
        #json.dump(, f, indent=4)

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session['state']
    
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)
    
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)
    #session1['credentials'] = credentials_to_dict(credentials)
    
    return flask.redirect(flask.url_for('program')) #This line courtesy of Google

def credentials_to_dict(credentials): #courtesy of YouTube / GCP
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Disable in prod?
    
    app.run('localhost', 8080, debug=True)