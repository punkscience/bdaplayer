import os
import requests
import sys
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QProgressBar, QFileDialog
from downloader import DownloadThread


root = 'http://archives.bassdrivearchive.com/'


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Bassdrive Archive Extractor")

        self.btnScan = QPushButton("Scan Archive")
        self.btnScan.clicked.connect( self.onPbScan )
        self.btnStartDownload = QPushButton( "Start Download")
        self.btnStartDownload.clicked.connect( self.onPnDownload )
        self.xProgressBar = QProgressBar( self )
        self.eOutputFolder = QLineEdit( self )
        self.pbBrowse = QPushButton( '...' )
        self.pbBrowse.clicked.connect( self.onBrowseClick )

        self.listFiles = QListWidget()

        # Create layout and add widgets
        layout = QVBoxLayout()

        layoutEdit = QHBoxLayout()
        layoutEdit.addWidget(self.eOutputFolder)
        layoutEdit.addWidget(self.pbBrowse)

        layout.addLayout(layoutEdit)
        layout.addWidget(self.btnScan)
        layout.addWidget(self.btnStartDownload)
        layout.addWidget(self.xProgressBar)
        layout.addWidget(self.listFiles )

        self.xProgressBar.setRange(1, 100)

        # Set dialog layout
        self.setLayout(layout)

        # Read in what we've already scanned
        with open("filelist.json", "r") as f:
            self.db = json.load( f )
            
            self.eOutputFolder.setText(self.db['output'])
            for file in self.db['queue']:
                if file['downloaded'] != True:
                    self.listFiles.addItem( file['fullName'] )

    def queueDownload( self, obj ):
        for obj in self.db['queue']:
            if obj['fullName'] == obj['fullName']:
                return

        self.db['queue'].append( obj )


    def onBrowseClick( self ):
        self.db['output'] = QFileDialog.getExistingDirectory()
        self.eOutputFolder.setText( self.db['output'])
        self.writeDb()


    def onPbScan( self ):
        self.btnScan.setEnabled( False )
        self.listFiles.clear()
        self.parseFolder( root, '')
        self.writeDb()
        self.btnScan.setEnabled( True )

    def onPnDownload( self ):
        self.btnStartDownload.setEnabled( False )
        self.btnScan.setEnabled( False )
        self.startDownloading()

    def writeDb( self ):
        with open( "filelist.json", "w") as f:
            json.dump( self.db, f )

    def setDownloaded( self, fullName, state ):
        for obj in self.db['queue']:
            if obj['fullName'] == fullName:
                obj['downloaded'] = state

        self.writeDb()

    def onDownloadUpdate( self, data ):
        self.xProgressBar.setValue( data )

    def onDownloadComplete( self, obj ):
        #print( "Download complete on {}.".format(obj['fullName']))
        self.setDownloaded( obj['fullName'], True)
        self.startDownloading() # Kick it off again
        self.listFiles.takeItem(0)

    def download( self, obj ):
        filename = os.path.join( self.db['output'], obj['fullName'])
        print( "Downloasing {}...".format(filename) )
        self.thread = DownloadThread( self.eOutputFolder.text(), obj )
        self.thread.download_update.connect( self.onDownloadUpdate )
        self.thread.download_complete.connect( self.onDownloadComplete )
        self.thread.start()

    def startDownloading( self ):

        for file in self.db['queue']:
            if file['downloaded'] == True:
                continue

            self.download( file )
            break
    

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
                    
                    self.queueDownload( obj )
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




