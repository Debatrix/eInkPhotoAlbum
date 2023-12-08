# %%
import cgi
import json
import os
import time
import hashlib
import logging
import threading
from io import BytesIO
from random import sample
from datetime import datetime, timedelta
from collections import OrderedDict
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import TimedRotatingFileHandler

import schedule
from PIL import Image

from image_processing import dithering, get_calendar_img,buffImg
from config import *

# %%
def load_json(path):
    if os.path.exists(path):
        with open(path,'r') as f:
            return json.load(f)
    else:
        return {}

def dump_json(path,data):
    with open(path,'w') as f:
        json.dump(data,f, indent=4, separators=(',', ':'))

def save_img(calendar_img,name=None):
    if name is None:
        name = datetime.now().strftime('%Y%m%d')
        for i in range(100):
            path = os.path.join(calendar_img_dir,'{}{:0>2}.png'.format(name,i))
            if not os.path.exists(path):
                break
        path = os.path.join(calendar_img_dir,'{}.png'.format(datetime.now().strftime('%Y%m%d%H%M%S')))
    else:
        path = os.path.join(calendar_img_dir,'{}.png'.format(name))
    calendar_img.save(path)
    return path

def file_md5(file_path):
    h,chunk = hashlib.md5(), 0
    with open(file_path, 'rb') as f:
        while chunk != b'':
            chunk = f.read(1024)
            h.update(chunk)
    return h.hexdigest()

# %%
def reset_queue():
    current = datetime.now()
    wh_flag = 'w' if int(current.strftime('%U'))%2==0 else 'h'

    vault = load_json(vault_path)
    cabin = load_json(cabin_path)
    archive = set(cabin.get('archive',[]))
    vault_img = set(list(vault[wh_flag].keys()))

    if len(vault_img-archive)<=min_queue_size:
        archive = set()
        logging.info('reset archive!')

    num = min(min_queue_size,len(vault_img-archive))
    queue = sample(list(vault_img-archive),num)
    queue = {x:vault[wh_flag][x] for x in queue}

    cabin = {'queue':queue,'archive':list(archive)}
    dump_json(cabin_path,cabin)
    logging.info('queue:{}, archive:{}'.format(len(queue),len(archive)))

    return cabin

def img_dequeue():
    cabin = load_json(cabin_path)
    if len(cabin['queue'])==0:
        cabin = reset_queue()
    queue = OrderedDict(cabin['queue'])
    archive = cabin['archive']
    task, path = queue.popitem(last=False)
    logging.info('Image {} dequeue, queue size: {}/{}'.format(task,len(queue),min_queue_size))
    archive.append(task)
    dump_json(cabin_path,{'queue':queue,'archive':archive})

    main_img = Image.open(path)
    calendar_img = process_img(main_img)
    return calendar_img

def process_img(main_img):
    calendar_img = get_calendar_img(location,key,main_img)
    save_img(calendar_img,'next')
    if is_save_calendar_img:
        save_img(calendar_img)
    return calendar_img

def next_wakeup():
    now = datetime.now()
    _schedules = []
    for t in schedules:
        t = datetime.strptime(t, "%H:%M")
        dt = datetime(now.year, now.month, now.day, t.hour, t.minute)
        dt += timedelta(minutes=15)
        if dt < now:
            dt += timedelta(days=1)
        delta = dt - now
        _schedules.append(delta)
    return str(min(_schedules).seconds)

    

# %%
class RequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, message, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(message))
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def _send_img(self, file_path,is_dithering=False):
        if os.path.isfile(file_path):
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            if is_dithering:
                img = Image.open(file_path)
                img = dithering(img)
                img_io = BytesIO()
                img.save(img_io, 'PNG')
                img_io.seek(0)
                self.wfile.write(img_io.read())
            else:
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def _send_buffImg(self, file_path):
        if os.path.isfile(file_path):
            img = Image.open(file_path)
            img = buffImg(img)
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Length', len(img))
            self.end_headers()
            self.wfile.write(img)
        else:
            self.send_error(404)

    def do_GET(self):
        parse_result = urlparse(self.path)
        if parse_result.path == '/':
            self._send_response('''
                <html>
                <body>
                <form method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit" value="Upload">
                </form>
                </body>
                </html>
            ''')
        else:
            file_path = parse_result.path[1:]  # remove the leading '/'
            try:
                if file_path == 'hash':
                    file_path = os.path.join(calendar_img_dir,'next.png')
                    if not os.path.isfile(file_path):
                        img_dequeue()
                    hash = file_md5(file_path)
                    logging.info('hash of next image:{}'.format(hash))
                    self._send_response(hash)
                elif file_path == 'next':
                    img_dequeue() # force update
                    file_path = os.path.join(calendar_img_dir,'next.png')
                    self._send_img(file_path,is_dithering=True)
                elif file_path == 'show':
                    file_path = os.path.join(calendar_img_dir,'next.png')
                    if not os.path.isfile(file_path):
                        img_dequeue()
                    self._send_img(file_path,is_dithering=True)
                elif file_path == 'bytes':
                    file_path = os.path.join(calendar_img_dir,'next.png')
                    if not os.path.isfile(file_path):
                        img_dequeue()
                    self._send_buffImg(file_path)
                    logging.info('send bytes of next image')
                elif file_path == 'wakeup':
                    t = next_wakeup()
                    self._send_response(t)
                    logging.info('Setup ESP32 to sleep for {} seconds'.format(t))
                elif file_path == 'info':
                    parse_query = parse_qs(parse_result.query)
                    if 'info' in parse_query:
                        logging.info('ESP32:{}'.format(parse_query['info']))
                    elif 'error' in parse_query:
                        logging.error('ESP32:{}'.format(parse_query['error']))
                    else:
                        logging.info('ESP32:{}'.format(parse_result.query))
                else:
                    file_path = os.path.join(calendar_img_dir,file_path)
                    self._send_img(file_path)
            except Exception as e:
                logging.error(e)
                self.send_error(404)
                

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        fileitem = form['file']
        if fileitem.filename:
            name = datetime.now().strftime('%Y%m%d%H%M%S.png')
            img = Image.open(BytesIO(fileitem.file.read()))
            img_path = os.path.join(upload_dir,name)
            img.save(img_path)
            cabin = load_json(cabin_path)
            queue = OrderedDict(cabin['queue'])
            queue[name]=img_path
            queue.move_to_end(name, last=False)
            dump_json(cabin_path,{'queue':queue,'archive':cabin['archive']})
            message = 'The file was uploaded successfully'
            logging.info('Image {} enqueue, queue size: {}/{}'.format(name,len(queue),min_queue_size))
        self._send_response(message)

        def log_message(self, format, *args):
            logging.info(format % args)
        
        def log_error(self, format, *args):
            logging.error(format % args)


# %%
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_server(server_class=ThreadingHTTPServer, handler_class=RequestHandler):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == '__main__':
    # create dirs
    os.makedirs(os.path.dirname(log_path),exist_ok=True)
    os.makedirs(calendar_img_dir,exist_ok=True)
    os.makedirs(upload_dir,exist_ok=True)
    assert os.path.exists(font_path), 'Font not found: {}!'.format(os.path.basename(font_path))
    assert os.path.exists(vault_path), 'Vault not found!'
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] => %(message)s",
        handlers=[
            TimedRotatingFileHandler(log_path,'D',14,0),
            logging.StreamHandler()
        ],
    )

    # schedules
    for img_schedule in schedules:
        schedule.every().day.at(img_schedule).do(img_dequeue)
        logging.info('Update image at {} every day'.format(img_schedule))
    schedule.every().sunday.at("00:00").do(reset_queue)
    logging.info('Reset queue at 00:00 every sunday')
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()

    reset_queue()
    logging.info('Start server...')
    run_server()