import os
import glob
import json
from PIL import Image

dir = './server/resource/Images'
vault_path = './server/vars/vault.json'
ext_list = ['.jpg','.png','.jpeg','.JPG','.PNG','.JPEG']

img_list = []
for ext in ext_list:
    img_list.extend(glob.glob(os.path.join(dir , '*' + ext)))

vault = {'w':{},'h':{}}
for idx,img_path in enumerate(img_list):
    img_name = os.path.basename(img_path)
    img = Image.open(img_path)
    if img.width>img.height:
        vault['w'][img_name]=img_path
    else:
        vault['h'][img_name]=img_path
    print('{}/{}:{}'.format(idx+1,len(img_list),img_path))

with open(vault_path,'w') as f:
    json.dump(vault,f)