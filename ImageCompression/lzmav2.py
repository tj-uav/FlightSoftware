import sys
import lzma
import pickle
import zlib
import bz2
import base64

'''
not using b64:
zlib = .34 seconds with 2580 KB
bz2 = .658 seconds with 2501 KB arguably best result

using b64:
zlib = .39 seconds with 2603 KB
bz2 = .613 seconds with 2613 KB


'''

def encode():
    img_name = sys.argv[1]
    b64str = base64.b64encode(open(img_name, "rb").read())
    #b64str = open(img_name, "rb").read()
    print("raw size:  ", sys.getsizeof(b64str))
    retstr = zlib.compress(b64str, 9)
    print("compressed size:  ", sys.getsizeof(retstr))
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
