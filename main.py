import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote

def parseFolder( sub, nightFolder ):
    url = urljoin( sub, nightFolder )
    print( "Scanning " + url + '...') 
    pagecontent = requests.get( url, headers={"User-Agent": "XY"})
    soup = BeautifulSoup( pagecontent.content, "html.parser")

    anchors = soup.find_all('a')

    for anchor in anchors:
        
        localAnchor = anchor['href']
        contents = anchor.contents[0]
        if contents.find( 'Parent') != -1:
            continue

        if localAnchor != "/" and localAnchor[len(localAnchor)-1] == '/':
            parseFolder( url, localAnchor )
        elif localAnchor.find( '.mp3' ) != -1:
            mp3url = urljoin( url, localAnchor )
            
            urlObj = urlparse( mp3url )
            filename = os.path.basename(urlObj.path)
            filename = unquote( filename )
            print("Downloading " + filename + '...')
            mp3 = requests.get( mp3url, headers={"User-Agent": "XY"})

            if not os.path.exists( 'output' ):
                os.mkdir( 'output')

            with open( './output/' + filename, "wb") as f:
                f.write( mp3.content )


root = 'http://archives.bassdrivearchive.com/'

parseFolder( root, '')



