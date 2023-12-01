# 服务端

> 注意：该服务端基于http.server与Pillow，它仅仅实现了最基础的安全检查。**绝对不要**把这个服务保留在公网上！

## 安装

- python==3.8
- Pillow==10.0.1
- schedule==1.2.1
- Requests==2.31.0
- beautifulsoup4==4.12.2（可选，用于爬取most-famous-paintings.com的TOP1000作品）
  - 请确保爬取图像时有合理的时间间隔

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

## 使用

假期日历由[holiday-cn](https://github.com/NateScarlet/holiday-cn)提供，使用前请提前下载对应年份的json文件。年份是按照国务院文件标题年份而不是日期年份，12月份的日期可能会被下一年的文件影响，因此最好保证有今明两年的文件。

服务器启动后，会相应以下页面：

- `http://[IP]:[Port]/d`：将返回下一张日历图像
- `http://[IP]:[Port]/[日期][序号]`：查看过去的日历图像
- `http://[IP]:[Port]`：上传图像，并且作为下一张日历的主图像
