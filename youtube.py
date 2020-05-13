# Written by Luke Carapezza (@lukec11) and Harshith Iyer (@harbar20), December 2019
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

# stuff for oauth
CLIENT_SECRETS_FILE = "config/client-secret-new.json"

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


app = flask.Flask(__name__)

app.secret_key = (secret_key)


# adds song to the youtube playlist
def add_to_youtube(youtube, videoID):
    playlist_id = YTconfig["playlist_id"]

    r2 = youtube.playlistItems().insert(
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
    # runs the request to add
    response = r2.execute()
    with open("ytPlaylist.json", 'w') as f:
        json.dump(response, f, indent=4)
    print("Added to Youtube Playlist.")


# This is for auth for youtube
def ytAuth():
    with open("config/ytAuth.json") as f:
        ytAuthJson = json.load(f)
        credentials_dict = ytAuthJson['credentials']

    credentials = google.oauth2.credentials.Credentials(
        credentials_dict["token"],
        refresh_token=credentials_dict["refresh_token"],
        token_uri=credentials_dict["token_uri"],
        client_id=credentials_dict["client_id"],
        client_secret=credentials_dict["client_secret"],
        scopes=credentials_dict["scopes"]
    )

    youtube = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    return youtube


# redirects to auth because it doesn't work without this for some reason
@app.route('/app')
def program():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    with open("config/ytAuth.json", "w") as f:
        json.dump({"credentials": dict(
            flask.session['credentials']), "state": flask.session['state']}, f, indent=4)

    # return this - will show on web page
    return ("Added!")

# This function was stolen from google. Thanks google.
# Allows offline access to the API, so client re-auth isn't required.
@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If
    # value doesn't match an authorized URI, you will get a
    # 'redirect_uri_mismatch' error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state
    # session1['state'] = state

    print(authorization_url)
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')  # calllback for oauth
def oauth2callback():
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('program'))


def credentials_to_dict(credentials):  # courtesy of YouTube / GCP
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    app.run('localhost', 9099, debug=True)
