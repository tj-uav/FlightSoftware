import sys
import lzma
import pickle

def encode():
    img_name = sys.argv[1]
    retstr = ""
    with open(img_name, "rb") as imgf:
        retstr = lzma.compress(imgf.read())
    outfilename = img_name+"_encoded.pkl"
    outfile = open(outfilename, 'wb')
    pickle.dump(retstr,outfile)

def decode():
    img_name = sys.argv[1]
    pkl_img_name = img_name+"_encoded.pkl"
    retstr = ""
    with open(pkl_img_name, "rb") as pklimgf:
        retstr = pickle.load(pklimgf)
    outfilename = img_name+"_decoded.JPG"
    outfile = open(outfilename, 'wb')
    outfile.write(lzma.decompress(retstr))

if(len(sys.argv)<3):
    print("Please specify the image that you would like to use as an argument and whether you are encoding or decoding (ex: $python imglzma.py image.JPG enc or $python imglzma.py image.JPG dec)")
elif sys.argv[2] == 'enc':
    encode()
elif sys.argv[2] == 'dec':
    decode()
else:
    print("please check your arguments again!")
