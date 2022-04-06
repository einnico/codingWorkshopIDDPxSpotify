
import requests
import pandas
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import re
from stop_words import get_stop_words

#################################################################################
##GET ACCESS
#Credentials
CLIENT_ID = 'Fill_In'
CLIENT_SECRET = 'Fill_In'

AUTH_URL = 'https://accounts.spotify.com/api/token'

auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})
#Response to json
auth_response_data = auth_response.json()
#Save Access Token
access_token = auth_response_data['access_token']
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}
#BASE URL
BASE_URL = 'https://api.spotify.com/v1/'
##END ACCESS
#################################################################################

#TrackID RIPTIDE -  Vance Joy
track_id = '7yq4Qj7cqayVTp3FF9CWbm' #not used
#Playlist 
# "OLD" '6j2b8xqdKBcFPbNe31nXLm' 
# aktuell: '0LuqWPOWKo1deOTUbcnTd5' 
# happy beats '37i9dQZF1DWSf2RDTDayIx' <------- for example 2
# kanye west '0ZPj9yk9u6cH1ZS2vVg1uy'
# eminem '37i9dQZF1DX1clOuib1KtQ' <------- for example 1
#Playlist used
playlist_akt_id = '37i9dQZF1DWSf2RDTDayIx'

#################################################################################
#methods
#######

#returns list of songs of given playlist
def getPlaylist(playlistID):
    playlist = requests.get(BASE_URL + 'playlists/' + playlistID + '/tracks', headers=headers)
    playlistj = playlist.json()
    listSongs = playlistj['items']
    nextList =playlistj['next']
    while nextList != None:
        nextPlaylistR= requests.get(nextList, headers=headers)
        nextPlaylistJson = nextPlaylistR.json()
        listSongs = listSongs + nextPlaylistJson['items']
        nextList = nextPlaylistJson['next']
    return listSongs

#returns Audio features from every song in given list
def getAudioFeatures(songlist):
    sList=[] #Song list
    #Vars for getting the audio features
    strIDs =[]
    strId =''
    countIds =0
    #go threw playlist and get tracks
    for i in songlist:
        if i['track']['id'] != None: #because some private songs have no id
            sList.append(i['track'])
            #go through songs for saving the ideas for audio features check
            if(countIds >=100): #because API is for 100 ids max
                strIDs.append(strId)
                strId=''
                countIds=0
            if countIds==0: strId=i['track']['id']
            else: strId=strId + ',' + i['track']['id']
            countIds=countIds+1

    strIDs.append(strId)
    getAllAudioFeatures= [] #all audio features in lists; 0 for first 100, 1 for second 100,...
    for j in strIDs:
        getAudioFeatures = requests.get(BASE_URL + 'audio-features',{
            'ids': j
        },
        headers=headers) #better performance than calling api for every song
        gAF=getAudioFeatures.json()
        for k in gAF['audio_features']:
            getAllAudioFeatures.append(k)
    return getAllAudioFeatures

#get all lyrics with uri
def getLyricsWithURI(songlist):
    lyricsList =[]
    for i in songlist:
        if i['track']['id'] != None: #because some private songs have no id          
            uri = i['track']['uri']
            lyricsOfSong= scrapeLyrics(i['track']['artists'][0]['name'],i['track']['name'])
            uriLyrics={}
            uriLyrics['uri']=uri
            uriLyrics['lyrics']=lyricsOfSong
            lyricsList.append(uriLyrics)
    return lyricsList

#get lyrics from genius
def scrapeLyrics(artistname, songname):
    artistname2 = str(artistname.replace(' ','-')) if ' ' in artistname else str(artistname)
    songname2 = str(songname.replace(' ','-')) if ' ' in songname else str(songname)
    page = requests.get('https://genius.com/'+ artistname2 + '-' + songname2 + '-' + 'lyrics')
    html = BeautifulSoup(page.text, 'html.parser')

    lyrics1 = html.find("div", class_="lyrics")
    lyrics2 = html.find("div", class_="Lyrics__Container-sc-1ynbvzw-6 jYfhrf")
    if lyrics1:
        lyrics = lyrics1.get_text()
    elif lyrics2:
        lyrics = lyrics2.get_text()
    elif lyrics1 == lyrics2 == None:
        lyrics = None
    return lyrics

#get words in lyrics
def getWordsInString(longStringURI):
    longString=longStringURI['lyrics']
    arrayWords=[]
    thisLyrics={}
    thisLyrics['uri']=longStringURI['uri']
    if longString != None:  #when no lyrics found: dont add. If there are lyrics: replace, split and add 
        thisString=longString.replace(',',"").replace('\'','').replace(';','').replace('!','').replace('(',' ').replace(')',' ').replace('-','')
        thisString=thisString.replace('[Chorus]',' ').replace('[Pre-Chorus]',' ').replace('[Verse 1]', ' ').replace('[Verse 2]',' ').replace('[Hook]',' ').replace('[Post-Chorus]',' ').replace('1:',' ')
        arrayWords=re.split(r'\s|\n',thisString)
    thisLyrics['lyrics']=arrayWords
    return thisLyrics

#count words in all lyrics
def countWords(listWithWords):
    lyricsCounts=[]
    stop_words = get_stop_words('en') #get stop words as list
    for x in listWithWords:
        for y in x['lyrics']:

            if any(d['word'].lower() == y.lower() for d in lyricsCounts): #if word is already in list

                currentIndex =next((i for i, item in enumerate(lyricsCounts) if item["word"].lower() == y.lower()), None)
                lyricsCounts[currentIndex]['count']=lyricsCounts[currentIndex]['count']+1

            else: #if word not already in list
                if y != '' and y != ' ' and y != '  ' and y!='   ': #we dont want empty space
                    if y.lower() not in stop_words and y.lower() != 'im' and y.lower() != 'youre': #we dont want the so called "stop-words"
                        element={}
                        element['word']=y
                        element['count']=1
                        lyricsCounts.append(element)
    return lyricsCounts

#################################################################################
#Calls
######

#get data
listSongs =getPlaylist(playlist_akt_id)
#Get tracks only - no need for other parameters:
allTracks =[]
for j in listSongs:
    allTracks.append(j['track'])

listAudioFeatures = getAudioFeatures(listSongs)

'''
lyricsList=getLyricsWithURI(listSongs)
listWithWords=[]
for k in lyricsList:
    listWithWords.append(getWordsInString(k))

countedList=countWords(listWithWords)

'''
#data analysis
lAF=pandas.DataFrame(listAudioFeatures)
lS=pandas.DataFrame(allTracks)
mergedListSAF=lAF.merge(lS,on='uri',how='left')
mergedListSAF =mergedListSAF.sort_values(by='danceability')

#print(mergedListSAF[['danceability','energy','uri', 'name']])
fig= plt.figure(figsize=(10,10))
ax = fig.add_axes([0.1, 0.1, 0.6, 0.9])
ax = sns.scatterplot(data=mergedListSAF, x='valence',y='energy',
    hue='name')
ax.legend(bbox_to_anchor=(1.01, 1), borderaxespad=0,fontsize='xx-small')
plt.tight_layout()
plt.show()
'''
cWDF=pandas.DataFrame(countedList)
cWDF=cWDF.sort_values(by='count', ascending=False).head(30)
plt.figure(figsize=(10,10))
ax = sns.barplot(data=cWDF, x='word',y='count')
plt.tight_layout()
plt.show()
#'''