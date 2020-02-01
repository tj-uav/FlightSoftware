import sys
from PIL import Image
def main():
    ogpic = Image.open(sys.argv[1])
    newname = sys.argv[1][0:sys.argv[1].find('.')]+"_downscaled"+sys.argv[1][sys.argv[1].find('.'):]
    if(len(sys.argv)==2):
        ogpic.save(newname, quality = 50)
    if(len(sys.argv)==3):
        ogpic.save(newname, quality = int(sys.argv[2]))

if(len(sys.argv)<2):
    print("Please specify the image that you would like to use (ex: $python imgc.py image.JPG)")
if(len(sys.argv)<3):
    print("Keep in mind that you can also specify the quality of compression, higher quality images transmit slower...\n because you did not specify a quality number, it will defaullt to 50")
else:
    main()
