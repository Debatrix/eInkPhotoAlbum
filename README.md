#  一个墨水屏日历

## 配置文件

需要自行在`server/`中新建配置文件，内容如下：
```python
# Font
font_path = 'resource/MaoKenWangXingYuan-2.ttf'

# QWeather
location = '101010100'
key = 'REPLACE_THIS_WITH_YOUR_KEY'

# Server
port = 8000
vault_path = 'vars/vault.json'
cabin_path = 'vars/cabin.json'
log_path = 'vars/log.log'
calendar_img_dir = 'vars/'
upload_dir = 'vars/upload/'
min_queue_size = 14
is_save_calendar_img = True
```
其中`key`为和风天气API密钥，请自行申请并替换
