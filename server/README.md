# 服务端

> 注意：该服务端基于http.server，它仅仅实现了最基础的安全检查。**绝对不要**把这个服务暴露到公网上！

## 安装

- python==3.8
- Pillow==10.0.1
- schedule==1.2.1
- Requests==2.31.0
- beautifulsoup4==4.12.2（可选，用于爬取most-famous-paintings.com的TOP1000作品）
  - 请确保爬取图像时有合理的时间间隔
- 默认字体为[文泉驿微米黑](http://wenq.org/wqy2/index.cgi?MicroHei)，已放置在`resource/wqy-microhei.ttc`

## 配置

1. 需要修改在`server/config_demo.py`中的内容，并重命名为`server/config.py`.
2. 假期日历由[holiday-cn](https://github.com/NateScarlet/holiday-cn)提供，使用前请提前下载对应年份的json文件并放置在`resource/holiday`。年份是按照国务院文件标题年份而不是日期年份，12月份的日期可能会被下一年的文件影响，因此最好保证有今明两年的文件。
   1. 另一个选择是使用`utils/get_holiday.py`这个脚本从[https://holiday-api.mooim.com/v1/](https://holiday-api.mooim.com/v1/)获取，除节假日外还可以获取节气、传统节日等，不保证api的有效性。
3. 自定义纪念日放置在`resource/holiday/anniversary.json`，格式与holiday-cn基本相同。其中`date`不包含年份。
4. 修改`utils/get_vault_json.py`中的路径并运行，生成`vault.json`文件

`anniversary.json`格式如下:

```json
{
    "days": [
        {
            "name": "test",
            "date": "12-10",
            "isOffDay": false
        }
    ]
}
```

# 运行

```python
python server.py
```

服务器启动后，会响应以下页面：

- `http://[IP]:[Port]`：上传图像，并且作为下一张日历的主图像
- `http://[IP]:[Port]/next`：手动更新日历图像并返回
- `http://[IP]:[Port]/show`：返回下一张日历图像
- `http://[IP]:[Port]/hash`：返回下一张日历图像的hash值，用于检查图像是否更新
- `http://[IP]:[Port]/bytes`：返回下一张日历图像的二进制流，用于ESP32更新
- `http://[IP]:[Port]/[name].png`：查看过去的日历图像
