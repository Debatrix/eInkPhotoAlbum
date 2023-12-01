# %%
import cgi
from io import BytesIO
import json
import time
import logging
import threading
import os.path as osp
from random import sample
from datetime import datetime
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import TimedRotatingFileHandler

import schedule
from PIL import Image

from image_processing import get_calendar_img
from config import *

# %%
def load_json(path):
    if osp.exists(path):
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
            path = osp.join(calendar_img_dir,'{}{:0>2}.png'.format(name,i))
            if not osp.exists(path):
                break
        path = osp.join(calendar_img_dir,'{}.png'.format(datetime.now().strftime('%Y%m%d%H%M%S')))
    else:
        path = osp.join(calendar_img_dir,'{}.png'.format(name))
    calendar_img.save(path)
    return path

# %%
def reset_queue():
    current = datetime.now()
    wh_flag = 'w' if int(current.strftime('%U'))%2==0 else 'h'

    vault = load_json(vault_path)
    cabin = load_json(cabin_path)
    archive = set(cabin.get('archive',[]))
    vault_img = set(list(vault[wh_flag].keys()))

    if len(vault_img-archive)<=0:
        archive = set()
        logging.info('reset archive!')

    queue = sample(list(vault_img-archive),min_queue_size)
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

# %%
class RequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, message, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def do_GET(self):
        if self.path == '/':
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
            file_path = self.path[1:]  # remove the leading '/'
            if file_path == 'd':
                file_path = osp.join(calendar_img_dir,'next.png')
                if not osp.isfile(file_path):
                    img_dequeue()
            else:
                file_path = osp.join(calendar_img_dir,file_path)
                if not osp.isfile(file_path):
                    self.send_error(404)
                    return
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                self.wfile.write(f.read())

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
            img_path = osp.join(upload_dir,name)
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
schedule.every().day.at("03:45").do(img_dequeue)
schedule.every().day.at("14:45").do(img_dequeue)
schedule.every().sunday.at("00:00").do(reset_queue)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run(server_class=ThreadingHTTPServer, handler_class=RequestHandler):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(filename)s] => %(message)s",
        handlers=[
            TimedRotatingFileHandler(log_path,'D',14,0),
            logging.StreamHandler()
        ],
    )

    reset_queue()
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
    run()