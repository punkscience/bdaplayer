
from PySide2.QtCore import *
from PySide2.QtGui import *
import requests

class DownloadThread(QThread):

    data_downloaded = Signal(object)
    data_updated = Signal(object)

    def __init__(self, obj):
        QThread.__init__(self)
        self.fileObj = obj

    def run(self):
        print( "Thread running...")
        with open(self.obj['fullName'], 'wb') as f:
            response = requests.get(self.obj['url'], headers={"User-Agent": "XY"}, stream=True )
            total = response.headers.get('content-length')

            if total is None:
                f.write(response.content)
            else:
                downloaded = 0
                total = int(total)
                for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                    downloaded += len(data)
                    f.write(data)
                    self.data_update.emit(len(data))
                    #done = int(50*downloaded/total)
                #self.setDownloaded( filename, True )
                self.data_downloaded.emit(True)
        

        
