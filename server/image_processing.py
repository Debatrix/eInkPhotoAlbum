# %%
import os
import json
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont

from config import *
# %%
def dithering(image):
    pal_image = Image.new("P", (1,1))
    pal_image.putpalette((16,14,27,  169,164,155,  19,30,19,  21,15,50,  122,41,37,  156,127,56,  128,67,54) + (0,0,0)*249)

    image_7color = image.convert("RGB").quantize(palette=pal_image)
    image_7color = image_7color.convert("RGB")

    return image_7color

def buffImg(image):
    image_temp = dithering(image)
    buf_7color = bytearray(image_temp.tobytes('raw'))
    # PIL does not support 4 bit color, so pack the 4 bits of color
    # into a single byte to transfer to the panel
    buf = [0x00] * int(image_temp.width * image_temp.height / 2)
    idx = 0
    for i in range(0, len(buf_7color), 2):
        buf[idx] = (buf_7color[i] << 4) + buf_7color[i+1]
        idx += 1
    return buf

def get_dominant_color(pil_img):
    img = pil_img.copy()
    img = img.convert("RGBA")
    img = img.resize((5, 5), resample=0)
    dominant_color = img.getpixel((2, 2))
    return dominant_color

def image_reshape(img,img_size=448):
    if img.width > img.height:
        img = img.resize((img_size, int(img_size * img.height / img.width)))
        flag = 'w'
    else:
        img = img.resize((int(img_size * img.width / img.height), img_size))
        flag = 'h'
    return img,flag

# %%
def get_date_img(dominant_color):
    date_img = Image.new('RGB', (150, 150), color = (255, 255, 255))
    d = ImageDraw.Draw(date_img)

    now = datetime.now()

    holiday_json = f'resource/{now.strftime("%Y")}.json'
    holiday_json2 = f'resource/{int(now.strftime("%Y"))+1}.json'

    if os.path.exists(holiday_json):
        with open(holiday_json,'r') as f:
            holiday = json.load(f)['days']
        if os.path.exists(holiday_json2):
            with open(holiday_json2,'r') as f:
                holiday += json.load(f)['days']

        for day in holiday:
            date = datetime.strptime(day['date'], "%Y-%m-%d")
            if date == now:
                date_string = day['name']
                if day['isOffDay']:
                    date_string += '(休)'
                else:
                    date_string += '(班)'
                break
            elif date > now:
                date_string = day['name']+'({}天后)'.format((date-now).days)
                break
            date_string = '该更新节假日表了'

    else:
        date_string = '该更新节假日表了'

    fnt_s = ImageFont.truetype(font_path, 20)
    fnt_b = ImageFont.truetype(font_path, 60)
    week_list = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
    d.text((10,10), now.strftime("%Y/%m"), font=fnt_s, fill=(0, 0, 0))
    d.text((95,10), week_list[now.weekday()], font=fnt_s, fill=(0, 0, 0))
    d.text((47,45), now.strftime("%d"), font=fnt_b, fill=dominant_color)
    if date_string:
        d.text((10,120), date_string, font=fnt_s, fill=(0, 0, 0))
    return date_img

# %%
def get_wether(location,key):
    wether_url = f'https://devapi.qweather.com/v7/weather/3d?location={location}&key={key}'
    aqi_url = f'https://devapi.qweather.com/v7/air/5d?location={location}&key={key}'

    wether = requests.get(wether_url).json()
    aqi = requests.get(aqi_url).json()
    return wether,aqi

def get_today_wether_img(wether,aqi,dominant_color):
    fnt = ImageFont.truetype(font_path, 12)

    today = wether['daily'][0]
    today.update(aqi['daily'][0])
    wether_today_img = Image.new('RGB', (150, 150), color = (255, 255, 255))

    palette = dominant_color[:-1]*128+(0,0,0)
    iconDay = 'resource/icons/{}.jpg'.format(today['iconDay'])
    iconDay = iconDay if os.path.exists(iconDay) else 'resource/icons/999.jpg'
    iconNight = 'resource/icons/{}.jpg'.format(today['iconNight'])
    iconNight = iconNight if os.path.exists(iconNight) else 'resource/icons/999.jpg'
    iconDay = Image.open(iconDay).convert('L')
    iconDay.putpalette(palette)
    iconDay = iconDay.convert('RGB').resize((30,30))
    iconNight = Image.open(iconNight).convert('L')
    iconNight.putpalette(palette)
    iconNight = iconNight.convert('RGB').resize((30,30))
    wether_today_img.paste(iconDay, (15, 10))
    wether_today_img.paste(iconNight, (95, 10))

    d = ImageDraw.Draw(wether_today_img)
    d.text((10,50), '白天:{}'.format(today['textDay']), font=fnt, fill=(0, 0, 0))
    d.text((90,50), '夜间:{}'.format(today['textNight']), font=fnt, fill=(0, 0, 0))
    d.text((10,70), '{}级风'.format(today['windScaleDay']), font=fnt, fill=(0, 0, 0))
    d.text((90,70), '{}级风'.format(today['windScaleNight']), font=fnt, fill=(0, 0, 0))
    d.text((10,90), '温度:{}~{}℃ '.format(today['tempMin'],today['tempMax'],), font=fnt, fill=(0, 0, 0))
    d.text((80,90), 'AQI:{}({})'.format(today['category'],today['aqi']), font=fnt, fill=(0, 0, 0))
    d.text((10,110), '降水:{}mm '.format(today['precip']), font=fnt, fill=(0, 0, 0))
    d.text((80,110), '湿度:{}%'.format(today['humidity']), font=fnt, fill=(0, 0, 0))
    d.text((10,130), '紫外线等级:{}'.format(today['uvIndex']), font=fnt, fill=(0, 0, 0))
    d.text((80,130), '能见度:{}km'.format(today['vis']), font=fnt, fill=(0, 0, 0))

    return wether_today_img

def get_future_wether_img(wether,aqi,dominant_color):
    fnt = ImageFont.truetype(font_path, 12)

    future1 = wether['daily'][1]
    future1.update(aqi['daily'][1])
    future2 = wether['daily'][2]
    future2.update(aqi['daily'][2])

    wether_future_img = Image.new('RGB', (150, 150), color = (255, 255, 255))


    palette = dominant_color[:-1]*128+(0,0,0)
    icon1 = 'resource/icons/{}.jpg'.format(future1['iconDay'])
    icon1 = icon1 if os.path.exists(icon1) else 'resource/icons/999.jpg'
    icon1 = Image.open(icon1).convert('L')
    icon1.putpalette(palette)
    icon1 = icon1.convert('RGB').resize((30,30))
    wether_future_img.paste(icon1, (22, 15))

    icon2 = 'resource/icons/{}.jpg'.format(future2['iconDay'])
    icon2 = icon2 if os.path.exists(icon2) else 'resource/icons/999.jpg'
    icon2 = Image.open(icon2).convert('L')
    icon2.putpalette(palette)
    icon2 = icon2.convert('RGB').resize((30,30))
    wether_future_img.paste(icon2, (22, 85))

    d = ImageDraw.Draw(wether_future_img)
    wstr = '明天: {}'.format(future1['textDay']) if future1['textDay'] == future1['textNight'] else  '明天: {} 转 {}'.format(future1['textDay'],future1['textNight'])
    d.text((70,15), wstr, font=fnt, fill=(0, 0, 0))
    d.text((70,35), '温度: {}~{}℃'.format(future1['tempMin'],future1['tempMax']), font=fnt, fill=(0, 0, 0))
    d.text((10,55), '降水:{}mm '.format(future1['precip']), font=fnt, fill=(0, 0, 0))
    d.text((80,55), 'AQI:{}({})'.format(future1['category'],future1['aqi']), font=fnt, fill=(0, 0, 0))

    wstr = '后天: {}'.format(future2['textDay']) if future2['textDay'] == future2['textNight'] else  '后天: {} 转 {}'.format(future2['textDay'],future2['textNight'])
    d.text((70,85), wstr, font=fnt, fill=(0, 0, 0))
    d.text((70,105), '温度: {}~{}℃'.format(future2['tempMin'],future2['tempMax']), font=fnt, fill=(0, 0, 0))
    d.text((10,125), '降水:{}mm '.format(future2['precip']), font=fnt, fill=(0, 0, 0))
    d.text((80,125), 'AQI:{}({})'.format(future2['category'],future2['aqi']), font=fnt, fill=(0, 0, 0))

    return wether_future_img

def get_wether_img(location,key,dominant_color):
    wether,aqi = get_wether(location,key)
    try:
        wether_today_img = get_today_wether_img(wether,aqi,dominant_color)
    except Exception as e:
        print(e)
        wether_today_img = Image.new('RGB', (150, 150), color = (255, 255, 255))

    try:
        wether_future_img = get_future_wether_img(wether,aqi,dominant_color)
    except Exception as e:
        print(e)
        wether_future_img = Image.new('RGB', (150, 150), color = (255, 255, 255))
    return wether_today_img,wether_future_img

# %%
def get_calendar_img(location,key,main_img,is_dithering=False):
    dominant_color = get_dominant_color(main_img)
    main_img,flag = image_reshape(main_img)

    date_img = get_date_img(dominant_color)
    wether_today_img,wether_future_img = get_wether_img(location,key,dominant_color)

    if flag == 'w':
        calendar_img = Image.new('RGB', (448, 600), color = (255, 255, 255))
        off_set = (448-main_img.height)//2
        calendar_img.paste(main_img,(0,off_set))
        calendar_img.paste(date_img,(0,448))
        calendar_img.paste(wether_today_img,(150,448))
        calendar_img.paste(wether_future_img,(300,448))
        calendar_img.transpose(Image.ROTATE_270)
    else:
        calendar_img = Image.new('RGB', (600, 448), color = (255, 255, 255))
        off_set = (448-main_img.width)//2
        calendar_img.paste(main_img,(off_set,0))
        calendar_img.paste(date_img,(448,0))
        calendar_img.paste(wether_today_img,(448,150))
        calendar_img.paste(wether_future_img,(448,300))
    if is_dithering:
        calendar_img = dithering(calendar_img).convert("RGB")
    return calendar_img

# %%
