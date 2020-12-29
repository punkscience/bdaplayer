convert -resize x16 -gravity center -crop 16x16+0+0 icon.png -flatten -colors 256 -background transparent icon.ico
pyinstaller main.py --onefile --icon="icon.ico"