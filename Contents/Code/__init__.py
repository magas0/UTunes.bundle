####################################################################################################
# UTunes
#
# This Plex Channel allows users to see music videos from Youtube based on their Plex music
# collection.
#
# Credits: ART from:
#          http://stuffpoint.com/youtube/image/422295/youtube-wallpaper-photoshop-wallpaper/
####################################################################################################

import os

#Channel Constants
PREFIX   = '/video/utunes'
NAME     = 'UTunes'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

#Youtube Constants
DEVELOPER_KEY            = "AIzaSyC6PEY5H_NchiqNZhd1fMKk6zEeoGX5uFg"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION      = "v3"

#Plex API Constants
TOP_TRACKS  = 25
TOP_ARTISTS = 10
PLEX_IP = '127.0.0.1'
PLEX_PORT = os.environ['PLEXSERVERPORT']

if 'PLEXTOKEN' in os.environ:
    PLEX_TOKEN = os.environ['PLEXTOKEN']
else:
    PLEX_TOKEN = None 

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME    
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)       
    
    HTTP.CacheTime = CACHE_1HOUR    

####################################################################################################
@handler(PREFIX, NAME, art=ART, thumb=ICON)
def MainMenu():       

    #Check Token
    if PLEX_TOKEN == None:
        return ObjectContainer(header="Empty", message="Cannot find Plex Media Server token.")

    #Has the user already choosen a music library before?
    if (Dict['music_library'] < 0):
        return LibrarySelect()    

    #If the user has chosen a library, show main menu
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(ViewArtists), title="View Artists by Name"))
    oc.add(DirectoryObject(key=Callback(ViewLetters), title="View Artists by Letter"))
    oc.add(DirectoryObject(key=Callback(TopTracks), title="Search by Top Tracks"))
    oc.add(DirectoryObject(key=Callback(TopArtists), title="Search by Top Artists"))    
    oc.add(DirectoryObject(key=Callback(LibrarySelect), title="Choose Another Music Library"))
    
    return oc   

####################################################################################################
# Allow the user to select which Plex music library they want to search with
#
@route(PREFIX + '/libraryselect')
def LibrarySelect():

    try:
        plex_url = "https://%s:%s/library/sections/?X-Plex-Token=%s" % (PLEX_IP, PLEX_PORT, PLEX_TOKEN)
        oc = ObjectContainer(title2="Select a Music Library")
        plex_libraries = XML.ElementFromURL(plex_url).xpath("//Directory")        

        for library in plex_libraries:
            if library.get('type') == "artist":
                oc.add(DirectoryObject(key=Callback(LibrarySave, library_key = library.get('key')), title="Choose Library: " + library.get('title')))

        if not len(oc):
            oc.header = "Empty"
            oc.message = "There are no music libraries on this Plex server."                      
                
        return oc
    
    except:
        return ObjectContainer(header="Empty", message="Cannot connect to the Plex Media Server.")


####################################################################################################
# Save the users library section and grab the information needed for searches on YouTube
#
def LibrarySave(library_key):

    if library_key:
        Dict['music_library'] = int(library_key)

        try:
            #Grab the top tracks from your Plex music library to send to Youtube
            PLEX_LIBRARY = Dict['music_library']        
            tracks = []    
            plex_url = "https://%s:%s/library/sections/%i/all?type=10&sort=viewCount%%3Adesc&X-Plex-Container-Start=0&X-Plex-Container-Size=%i&X-Plex-Token=%s" % \
                       (PLEX_IP, PLEX_PORT, PLEX_LIBRARY, TOP_TRACKS, PLEX_TOKEN)

            plex_tracks = XML.ElementFromURL(plex_url).xpath("//Track")
            for track in plex_tracks:
                tracks.append(track.get('grandparentTitle') + " - " + track.get('title'))

            Dict['tracks'] = tracks    

            #Grab the top artists from your Plex music library to send to Youtube
            artists = []    
            plex_url = "https://%s:%s/library/sections/%i/all?type=8&sort=viewCount%%3Adesc&X-Plex-Container-Start=0&X-Plex-Container-Size=%i&X-Plex-Token=%s" % \
                       (PLEX_IP, PLEX_PORT, PLEX_LIBRARY, TOP_ARTISTS, PLEX_TOKEN)

            plex_artists = XML.ElementFromURL(plex_url).xpath("//Directory")
            for artist in plex_artists:
               if artist.get('title') != "Various Artists":
                    artists.append(artist.get('title'))

            Dict['artists'] = artists 
        
            return MainMenu()
        
        except:
            return ObjectContainer(header="Empty", message="Cannot connect to the Plex Media Server.")

####################################################################################################
# Take the top tracks from Plex and search Youtube for those tracks
#
@route(PREFIX + '/toptracks')
def TopTracks():    
    
    if Dict['tracks']:
        try:
            oc = ObjectContainer(title2="Top Tracks")
        
            for search_track in Dict['tracks']:            
                search_string = String.Quote("%s" % (search_track), usePlus=False)            
                youtube_url = "https://www.googleapis.com/%s/%s/search?part=id,snippet&type=video&q=%s&maxResults=1&key=%s" % \
                              (YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, search_string, DEVELOPER_KEY)
                              
                json_data = JSON.ObjectFromURL(encoding='utf-8', url=youtube_url)            
                if json_data['items']:
                    channel = json_data['items'][0]['snippet']['channelTitle']                                
                    video_url = "http://www.youtube.com/watch?v=" + json_data['items'][0]['id']['videoId']
                    title = json_data['items'][0]['snippet']['title']
                    summary = json_data['items'][0]['snippet']['description']
                    image = json_data['items'][0]['snippet']['thumbnails']['medium']['url']
        
                    oc.add(VideoClipObject(
                            url = video_url,
                            title = title,
                            summary = summary,
                            thumb = image
                           ))
            return oc
        
        except:
            return ObjectContainer(header="Empty", message="Cannot connect to the YouTube API.")
    else:
        return ObjectContainer(header="Empty", message="There are no results to list right now.")

####################################################################################################
# Take the top artists from Plex and search Youtube for the first 5 videos for each artist
#
@route(PREFIX + '/topartists')
def TopArtists():  
    
    if Dict['artists']:
        try:
            oc = ObjectContainer(title2="Your Top Artists on Youtube")
        
            for search_artist in Dict['artists']:
                search_artist = search_artist + " music"
                search_string = String.Quote("%s" % (search_artist), usePlus=False)
                youtube_url = "https://www.googleapis.com/%s/%s/search?part=id,snippet&type=video&q=%s&maxResults=5&key=%s" % \
                              (YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, search_string, DEVELOPER_KEY)

                json_data = JSON.ObjectFromURL(encoding='utf-8', url=youtube_url)            
                if json_data['items']:
                    for item in json_data['items']:            
                        video_url = "http://www.youtube.com/watch?v=" + item['id']['videoId']
                        title = item['snippet']['title']
                        summary = item['snippet']['description']
                        image = item['snippet']['thumbnails']['medium']['url']
        
                        oc.add(VideoClipObject(
                                url = video_url,
                                title = title,
                                summary = summary,
                                thumb = image
                               ))                        
            return oc
        except:
            return ObjectContainer(header="Empty", message="Cannot connect to the YouTube API.")
    else:
        return ObjectContainer(header="Empty", message="There are no results to list right now.")

####################################################################################################
# Show all the artists from the users Plex music library
#
@route(PREFIX + '/viewartists', offset=int)
def ViewArtists(offset = 0):

    if Dict['music_library']:
        PLEX_LIBRARY = Dict['music_library']
        items_per_page = 25
        
        try:        
            oc = ObjectContainer(title2="Your Artists")       
            plex_url = "https://%s:%s/library/sections/%i/all?type=8&X-Plex-Container-Start=%i&X-Plex-Container-Size=%i&X-Plex-Token=%s" % \
                       (PLEX_IP, PLEX_PORT, PLEX_LIBRARY, offset, items_per_page, PLEX_TOKEN)

            plex_artists = XML.ElementFromURL(plex_url).xpath("//Directory")
            for artist in plex_artists:        
                artist_name = artist.get('title')
                url_artist_name = String.Quote("%s" % (artist_name), usePlus=False)
                if artist.get('thumb'):
                    thumb = "http://%s:%s" % (PLEX_IP, PLEX_PORT) + artist.get('thumb') + "?X-Plex-Token=%s" % (PLEX_TOKEN)
                else:
                    thumb = ICON
                    
                oc.add(DirectoryObject(
                        key = Callback(ArtistDetail, artist_name = artist_name, url_artist_name = url_artist_name),
                        title = artist_name,
                        thumb = thumb    
                       ))

            oc.add(NextPageObject(
                        key = Callback(ViewArtists, offset=(offset+items_per_page)),
                        title = "More ..."
                   ))
    
            return oc
        except:
            return ObjectContainer(header="Empty", message="Cannot connect to the Plex API.")
    else:
        return ObjectContainer(header="Empty", message="A music library needs to be choosen.")

####################################################################################################
# Pull Youtube videos based on the artists name
# 
@route(PREFIX + '/artistdetail/{url_artist_name}')
def ArtistDetail(artist_name, url_artist_name, page_token=""):

    try:
        oc = ObjectContainer(title2="YouTube search for " + artist_name)
        url_artist_name = '"' + url_artist_name + '%20-%20"%20music%20video'
        youtube_url = "https://www.googleapis.com/%s/%s/search?part=id,snippet&type=video&q=%s&maxResults=30&pageToken=%s&key=%s" % \
                      (YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, url_artist_name, page_token, DEVELOPER_KEY)

        json_data = JSON.ObjectFromURL(encoding='utf-8', url=youtube_url) 
        if json_data['items']:
            for item in json_data['items']: 
                video_url = "http://www.youtube.com/watch?v=" + item['id']['videoId']
                title = item['snippet']['title']
                summary = item['snippet']['description']
                image = item['snippet']['thumbnails']['medium']['url']
        
                oc.add(VideoClipObject(
                        url = video_url,
                        title = title,
                        summary = summary,
                        thumb = image
                       ))

            if json_data['nextPageToken']:
                oc.add(NextPageObject(
                        key = Callback(ArtistDetail, artist_name = artist_name, url_artist_name = url_artist_name, page_token = json_data['nextPageToken']),
                        title = "More ..."
                      ))                
        return oc
    except:
        return ObjectContainer(header="Empty", message="Cannot connect to the YouTube API.")

####################################################################################################
# Show all the artists from the users Plex music library organized by letter
#
@route(PREFIX + '/viewletters')
def ViewLetters(offset = 0):

    if Dict['music_library']:
        PLEX_LIBRARY = Dict['music_library']

        try:
            oc = ObjectContainer(title2="Artists by First Letter")    
            plex_url = "https://%s:%s/library/sections/%i/firstCharacter?type=8&X-Plex-Token=%s" % \
                       (PLEX_IP, PLEX_PORT, PLEX_LIBRARY, PLEX_TOKEN)

            plex_letters = XML.ElementFromURL(plex_url).xpath("//Directory")
            for letter in plex_letters:        
                letter_title = letter.get('title')
                letter_size = letter.get('size')        
                oc.add(DirectoryObject(
                        key = Callback(ArtistLetter, letter_title = letter_title),
                        title = letter_title + " (" + letter_size + ")"                
                       ))       
            return oc
        except:
            return ObjectContainer(header="Empty", message="Cannot connect to the Plex API.")
    else:
        return ObjectContainer(header="Empty", message="A music library needs to be choosen.")

####################################################################################################
# Show all the artists from the users Plex music library by a first letter
#
@route(PREFIX + '/artistletter/{letter_title}')
def ArtistLetter(letter_title):

    if Dict['music_library']:
        PLEX_LIBRARY = Dict['music_library']

        try:
            oc = ObjectContainer(title2="Artists Starting with '" + letter_title + "'")          
            plex_url = "https://%s:%s/library/sections/%i/firstCharacter/%s?type=8&X-Plex-Token=%s" % \
                       (PLEX_IP, PLEX_PORT, PLEX_LIBRARY, letter_title, PLEX_TOKEN)

            plex_artists = XML.ElementFromURL(plex_url).xpath("//Directory")
            for artist in plex_artists:        
                artist_name = artist.get('title')
                url_artist_name = String.Quote("%s" % (artist_name), usePlus=False)
                if artist.get('thumb'):
                    thumb = "http://%s:%s" % (PLEX_IP, PLEX_PORT) + artist.get('thumb') + "?X-Plex-Token=%s" % (PLEX_TOKEN)
                else:
                    thumb = ICON
            
                oc.add(DirectoryObject(
                        key = Callback(ArtistDetail, artist_name = artist_name, url_artist_name = url_artist_name),
                        title = artist_name,
                        thumb = thumb
                       ))       
            return oc
        except:
            return ObjectContainer(header="Empty", message="Cannot connect to the Plex API.")
    else:
        return ObjectContainer(header="Empty", message="A music library needs to be choosen.")    
