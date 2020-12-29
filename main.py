import os
import sys
import json
from datetime import datetime, timedelta
import vlc
import random

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QProgressBar, QFileDialog
from workers.downloader import DownloadThread
from workers.webscraper import ScraperThread


ROOTURL = 'http://archives.bassdrivearchive.com/'
DBFILE = 'filedata.json'


class Form(QDialog):

    def __init__(self, parent=None):
        self.player = vlc.MediaPlayer()
        super(Form, self).__init__(parent)
        self.setWindowTitle("Bassdrive Archive Player")

        self.pbPlay = QPushButton( "Play")
        self.pbStop = QPushButton( "Stop")
        self.pbRandom = QPushButton( "Random" )
        self.pbDownload = QPushButton( "Download" )
        self.pbPlay.clicked.connect( self.onPbPlay )
        self.pbDownload.clicked.connect( self.onPbDownload )
        self.pbRandom.clicked.connect( self.onPbRandom )
        self.pbStop.clicked.connect( self.onPbStop )

        self.pbPlay.setEnabled( False )
        self.xProgressBar = QProgressBar( self )
        self.eOutputFolder = QLineEdit( self )
        self.pbBrowse = QPushButton( '...' )
        self.pbBrowse.clicked.connect( self.onBrowseClick )

        self.listFiles = QListWidget()
        self.listFiles.itemClicked.connect( self.onItemSelected )

        # Create layout and add widgets
        layout = QVBoxLayout()

        layoutEdit = QHBoxLayout()
        layoutEdit.addWidget(self.eOutputFolder)
        layoutEdit.addWidget(self.pbBrowse)

        layout.addLayout(layoutEdit)
        layout.addWidget(self.xProgressBar)
        layout.addWidget(self.listFiles )
        layout.addWidget(self.pbPlay)
        layout.addWidget(self.pbStop )
        layout.addWidget(self.pbRandom )
        layout.addWidget(self.pbDownload)

        self.xProgressBar.setRange(1, 100)

        # Set dialog layout
        self.setLayout(layout)

        # Read in what we've already scanned
        if os.path.isfile( DBFILE ):
            with open(DBFILE, "r") as f:
                self.db = json.load( f )
                
                self.eOutputFolder.setText(self.db['output'])
                for file in self.db['files']:
                    self.listFiles.addItem( file['filename'] )
        else:
            self.db = {
                "output": "output",
                "last_scan": "2020-12-28T19:19:10.702353",
                "files": []
            }
    
        if datetime.now() >= datetime.fromisoformat(self.db['last_scan']) + timedelta( hours=12 ):
            self.startWebScraping( DBFILE, ROOTURL )

    def onPbStop( self ):
        self.player.stop()
        self.pbPlay.setText( "Play")
        self.pbPlay.clicked.disconnect( self.onPause )
        self.pbPlay.clicked.connect( self.onPbPlay )
        self.pbPlay.setEnabled( True )

    def onPbRandom( self ):
        randomNo = random.randint( 0, len( self.db['files'] )-1 )
        self.listFiles.setCurrentRow(randomNo )
        obj = self.db['files'][randomNo]
        self.playFile( obj )

    def playFile( self, obj ):
        self.player.stop()
        self.player.set_mrl( obj['url'])
        self.player.play()
        self.pbPlay.setText( "Pause")
        self.pbPlay.clicked.disconnect( self.onPbPlay )
        self.pbPlay.clicked.connect( self.onPause )
        self.pbPlay.setEnabled( True )

    def onItemSelected( self, listItem ):
        self.pbPlay.setEnabled( True )
        print( 'Selected: {}({})'.format( listItem.text(), self.listFiles.currentRow() ))

    def startWebScraping( self, dbFile, rootUrl ):
        self.pbBrowse.setEnabled( False )
        print( "Starting web scraping from {} to {}...".format( rootUrl, dbFile ))
        self.scrapethread = ScraperThread( dbFile, rootUrl )
        self.scrapethread.scraper_update.connect( self.onScraperUpdate )
        self.scrapethread.scraper_complete.connect( self.onScraperComplete )
        self.scrapethread.start()
        
    def onScraperUpdate( self, obj ):
        pass
        
    def onScraperComplete( self, newdb ):
        for obj in newdb:
            if obj not in self.db:
                self.db.append( obj )
                self.listFiles.addItem( obj['filename'])
                print( "Adding new mix: {}".format(obj['filename']))

        self.pbBrowse.setEnabled( True )

    def onBrowseClick( self ):
        self.db['output'] = QFileDialog.getExistingDirectory()
        self.eOutputFolder.setText( self.db['output'])
        self.writeDb()

    def onPbDownload( self ):
        self.pbDownload.setEnabled( False )
        selectedItem = self.listFiles.currentRow()
        fileObj = self.db['files'][selectedItem]
        self.download( fileObj )

    def onPbPlay( self ):
        obj = self.db['files'][self.listFiles.currentRow()]
        self.playFile( obj )

    def onPause( self ):
        self.player.pause()
        self.pbPlay.setText( "Play" )
        self.pbPlay.clicked.disconnect( self.onPause )
        self.pbPlay.clicked.connect( self.onPbPlay )

    def writeDb( self ):
        self.db['output'] = self.eOutputFolder.text()
        with open( DBFILE, "w") as f:
            json.dump( self.db, f, indent=4)

    def setDownloaded( self, fullName, state ):
        for obj in self.db['files']:
            if obj['filename'] == fullName:
                obj['downloaded'] = state

        self.writeDb()

    def onDownloadUpdate( self, data ):
        self.xProgressBar.setValue( data )

    def onDownloadComplete( self, obj ):
        #print( "Download complete on {}.".format(obj['fullName']))
        self.setDownloaded( obj['filename'], True)
        

    def download( self, obj ):
        if not os.path.isdir( 'cache'):
            os.mkdir( 'cache' )

        filename = os.path.join( 'cache', obj['filename'])
        print( "Downloasing {}...".format(filename) )
        self.downloadthread = DownloadThread( 'cache', obj )
        self.downloadthread.download_update.connect( self.onDownloadUpdate )
        self.downloadthread.download_complete.connect( self.onDownloadComplete )
        self.downloadthread.start()


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())


#startDownloading()




