import os
import requests
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote

downloadQueue = []

def queueDownload( obj ):
    downloadQueue.append( obj )

def startDownloading():
    print( "Downloading " + str( len( downloadQueue ) ) + " files...")
    count = 1
    for obj in downloadQueue:
        print("Downloading " + str( count ) + " of " + str( len( downloadQueue ) ) + ": " + obj['fullName'] + '...')

        download( obj['url'], obj['fullName'] )
        count = count + 1

def download( url, filename ):
    with open(filename, 'wb') as f:
        response = requests.get(url, headers={"User-Agent": "XY"}, stream=True )
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


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

        if localAnchor != "/" and localAnchor[len(localAnchor)-1] == '/' and localAnchor.find('http://') == -1 and localAnchor.find('https://') == -1:
            parseFolder( url, localAnchor )
        elif localAnchor.find( '.mp3' ) != -1:
            mp3url = urljoin( url, localAnchor )
            
            urlObj = urlparse( mp3url )
            filename = os.path.basename(urlObj.path)
            filename = unquote( filename )

            # Make the folder if we need to
            if not os.path.exists( 'output' ):
                os.mkdir( 'output')

            fullName = './output/' + filename

            # Check to see if we already have the file and if not, download it. 
            if not os.path.exists( fullName ):
                obj = {
                    "url": mp3url,
                    "fullName": fullName
                }
                
                queueDownload( obj )
            else:
                print( "Skipping " + fullName + '.')

root = 'http://archives.bassdrivearchive.com/'

parseFolder( root, '')
startDownloading()




