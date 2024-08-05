from django.shortcuts import render, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.http import HttpResponse
from requests import Request, post
from .util import *
from .forms import PlaylistForm
from .models import *
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

code = ''
def login(request):
    # get a link for the user to authorize their account
    context = {
        'auth_url': create_spotify_oauth().get_authorize_url()
    }
    return render(request, "spotify/home.html", context)

def find(request):
    # create a spotify api client using the access token
    try:
        code = request.GET['code']
        token = create_spotify_oauth().get_access_token(code)
    except:
        return redirect('spotify:home')
    sp = spotipy.Spotify(auth=token['access_token'])

    # save the user
    user_name = sp.current_user()['display_name']
    if Users.objects.filter(name=user_name).exists():
        user = Users.objects.get(name=user_name)
    else:
        user = Users(name=user_name)
        user.save()

    context = {}

    # if the user gives a playlist name, search for it
    if request.method == "POST":
        playlist_form = PlaylistForm(request.POST)
        context["form"] = playlist_form
        if playlist_form.is_valid():
            playlist_name = playlist_form.cleaned_data["name"]
            for playlist in sp.current_user_playlists()['items']:
                # if the playlist is in the user's library, save its info and render it
                if playlist['name'] == playlist_name:
                    context["status"] = "We found the playlist you are looking for!"
                    context["image"] = playlist['images'][0]
                    context["title"] = playlist_name

                    # process the tracks to display
                    tracks = sp.playlist_tracks(playlist['id'])
                    context["songs"] = tracks['items']
                    while tracks['next']:
                        tracks = sp.next(tracks)
                        context['songs'].extend(tracks['items'])
                    
                    # save the playlist
                    pl = Playlists(
                        name = playlist['name'],
                        user = Users.objects.get(id=user.id),
                    )
                    if not Playlists.objects.filter(name=pl.name, user=pl.user).exists():
                        pl.save()
                        context['id'] = pl.id
                    else:
                        pl = Playlists.objects.get(name=pl.name, user=user.id)
                        context['id'] = pl.id

                    for item in context['songs']:
                        track = item['track']

                        # save the artist
                        ar = Artists(name=track['artists'][0]['name'])
                        if not Artists.objects.filter(name=ar.name).exists():
                            ar.save()
                        else:
                            ar = Artists.objects.filter(name=ar.name)[0]
                        
                        # save the album
                        al = Albums(name=track['album']['name'], artist=ar)
                        if not Albums.objects.filter(name=al.name).exists():
                            al.save()
                        else:
                            al = Albums.objects.filter(name=al.name)[0]

                        # save the track
                        tr = Tracks(
                            name = track['name'],
                            artist = ar,
                            album = al,
                            duration = track['duration_ms']
                        )
                        if not Tracks.objects.filter(name=tr.name, artist=tr.artist, album=tr.album, duration=tr.duration).exists():
                            tr.save()
                            tr.playlist.add(pl)
                        else:
                            tr = Tracks.objects.get(name=tr.name, artist=tr.artist, album=tr.album, duration=tr.duration)
                            tr.playlist.add(pl)
                    break
            else:
                context["invalid"] = "That playlist wasn't in your libary"
    else:
        context["form"] = PlaylistForm()

    return render(request, "spotify/input.html", context)

def transfer(request):
    # create a spotify client
    try:
        token = create_spotify_oauth().get_access_token(code)
    except:
        return redirect('spotify:home')
    sp = spotipy.Spotify(auth=token['access_token'])

    context = {}
    context['transfered'] = False

    playlist_name = Playlists.objects.get(id=request.GET['id']).name
    context["playlist_name"] = playlist_name

    # authenticate user for youtube
    client_secrets_file = "client_secret_1066233879197-ts3d3knt4mddmu4p9hr79i5a29to71mv.apps.googleusercontent.com.json"
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        client_secrets_file, scopes=scopes)
    flow.redirect_uri = f"http://127.0.0.1:8000/transfer/?id={request.GET['id']}"
    auth_url, state = flow.authorization_url(
        access_type='offline',
    )
    context['auth_url'] = auth_url

    if request.GET.get('code'):
        # fetch token
        flow.fetch_token(code=request.GET['code'])

        # create youtube api client
        api_service_name = "youtube"
        api_version = "v3"
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=flow.credentials)
        
        # create playlist on youtube account
        create_playlist = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "tags": [
                        "sample playlist",
                        "API call"
                    ],
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "private"
                }
            }
        )
        try:
            playlist_id = create_playlist.execute()['id']
        except googleapiclient.errors.HttpError as err:
            context['reason'] = err._get_reason()
            return render(request, 'spotify/error.html', context)

        # fill playlist with songs from spotify playlist
        for track in Tracks.objects.filter(playlist=request.GET['id']):
            # search for the track
            artist_name = track.artist.name
            query = f'{artist_name} - {track.name}'
            search = youtube.search().list(
                part="snippet",
                q=query,
                type="video"
            )
            try:
                results = search.execute()
            except googleapiclient.errors.HttpError as err:
                context['reason'] = err._get_reason()
                return render(request, 'spotify/error.html', context)
            video_id = results['items'][0]['id']

            # add the result to the playlist
            insert = youtube.playlistItems().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": video_id,
                    }    
                }
            )
            try:
                insert.execute()
            except googleapiclient.errors.HttpError as err:
                context['reason'] = err._get_reason()
                return render(request, 'spotify/error.html', context)
        context['transferred'] = True
    return render(request, "spotify/youtube.html", context)