
from PySide2.QtCore import *
from PySide2.QtGui import *
import requests

class DownloadThread(QThread):

    download_complete = Signal(object)
    download_update = Signal(object)

    def __init__(self, obj):
        QThread.__init__(self)
        self.fileObj = obj

    def run(self):
        # print( "Thread running with {}...".format( self.fileObj['fullName']) )
        with open(self.fileObj['fullName'], 'wb') as f:
            response = requests.get(self.fileObj['url'], headers={"User-Agent": "XY"}, stream=True )
            total = response.headers.get('content-length')

            if total is None:
                f.write(response.content)
            else:
                downloaded = 0
                total = int(total)
                for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                    downloaded += len(data)
                    f.write(data)
                    perc = int( round( downloaded / total * 100 ) )
                    self.download_update.emit( perc )
                   
                self.download_complete.emit(self.fileObj)
        

        
