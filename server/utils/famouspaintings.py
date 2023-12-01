# %%
import os
import time
import re
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image

# %%
url = 'http://en.most-famous-paintings.com'
img_size = 600 # The image is scaled with the long side being img_size
wanted = 100 # The number of images want to save
# %%
top_url = url+'/MostFamousPaintings.nsf/ListOfTop1000MostPopularPainting?OpenForm'
r = requests.get(top_url)
soup = BeautifulSoup(r.content, 'html.parser')
images_url=[]
for element_img in soup.find_all('div', attrs={'class': 'mosaicflow__item'}):
    images_url.append(url+'/MostFamousPaintings.nsf/'+element_img.a.get('href'))
images_url=images_url[::-1] # popular first
time.sleep(20)
# %%
if os.path.exists('saved.csv'):
    with open('saved.csv','r') as f:
        saved = [x.strip().split(',')[0] for x in f.readlines()]
else:
    saved = []
# %%
while len(saved)<wanted:
    try:
        img_url = images_url.pop()
        r = requests.get(img_url)
        soup = BeautifulSoup(r.content, 'html.parser')
        filename = re.sub(r'\W', '_', soup.find('h1').get('title'))+'.png'
        if filename in saved:
            continue
        print('{}/{}:{}'.format(len(saved), wanted, filename))
        for element_img in soup.find_all('div', attrs={'class': 'ArtworkImageBlock'}):
            img_url = url+element_img.img.get('src')
            img = Image.open(BytesIO(requests.get(img_url).content))

            w, h = img.size
            if w < h:
                h = img_size * h // w
                w = img_size
            else:
                w = img_size * w // h
                h = img_size

            img.thumbnail((w, h))

            img.save(filename)
            with open('saved.csv', 'a') as f:
                f.write(f'{filename},{img.width},{img.height}\n')
            saved.append(filename)
    except Exception as e:
        print(e)
    time.sleep(20)
