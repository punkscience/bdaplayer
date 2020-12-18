import os
import requests
import sys
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QListWidget

downloadQueue = []
root = 'http://archives.bassdrivearchive.com/'


def queueDownload( obj ):
    for obj in downloadQueue:
        if obj['fullName'] == obj['fullName']:
            return

    downloadQueue.append( obj )






class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Bassdrive Archive Extractor")

        self.btnScan = QPushButton("Scan Archive")
        self.btnScan.clicked.connect( self.onPbScan )
        self.btnStartDownload = QPushButton( "Start Download")
        self.btnStartDownload.clicked.connect( self.onPnDownload )

        self.listFiles = QListWidget()


        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.btnScan)
        layout.addWidget(self.btnStartDownload)
        layout.addWidget(self.listFiles )

        # Set dialog layout
        self.setLayout(layout)

        # Read in what we've already scanned
        with open("filelist.json", "r") as f:
            obj = json.load( f )
            for file in obj['files']:
                downloadQueue.append( file )
                self.listFiles.addItem( file['fullName'] )


    def onPbScan( self ):
        self.btnScan.setEnabled( False )
        self.listFiles.clear()
        self.parseFolder( root, '')
        self.writeDb()
        self.btnScan.setEnabled( True )

    def onPnDownload( self ):
        self.btnStartDownload.setEnabled( False )
        self.startDownloading()
        self.btnStartDownload.setEnabled( True )

    def writeDb( self ):
        with open( "filelist.json", "w") as f:
            obj = {
                "files": downloadQueue
            }
            json.dump( obj, f )

    def setDownloaded( self, fullName, state ):
        for obj in downloadQueue:
            if obj['fullName'] == fullName:
                obj['downloaded'] = state

        self.writeDb()

    def download( self, url, filename ):
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
                    #done = int(50*downloaded/total)
                self.setDownloaded( filename, True )


    def startDownloading( self ):
        print( "Downloading " + str( len( downloadQueue ) ) + " files...")
        count = 1
        for obj in downloadQueue:
            if obj['downloaded'] == True:
                continue

            print("Downloading " + str( count ) + " of " + str( len( downloadQueue ) ) + ": " + obj['fullName'] + '...')

            self.download( obj['url'], obj['fullName'] )
            count = count + 1

    def parseFolder( self, sub, nightFolder ):
        url = urljoin( sub, nightFolder )
        #print( "Scanning " + url + '...') 
        pagecontent = requests.get( url, headers={"User-Agent": "XY"})
        soup = BeautifulSoup( pagecontent.content, "html.parser")

        anchors = soup.find_all('a')

        for anchor in anchors:
            
            localAnchor = anchor['href']
            contents = anchor.contents[0]
            if contents.find( 'Parent') != -1:
                continue

            if localAnchor != "/" and localAnchor[len(localAnchor)-1] == '/' and localAnchor.find('http://') == -1 and localAnchor.find('https://') == -1:
                self.parseFolder( url, localAnchor )
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
                        "fullName": fullName,
                        "downloaded": False
                    }
                    
                    queueDownload( obj )
                    self.listFiles.addItem( obj['fullName'])
                    


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())


#startDownloading()




