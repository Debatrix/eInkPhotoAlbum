# %%
import json
import time
import requests
from datetime import datetime, timedelta

url="https://holiday-api.mooim.com/v1/"
year=2023
# %%
feast = []
for i in range(0,367):
    day = datetime(year, 1, 1) + timedelta(days=i)
    date = day.strftime("%Y-%m-%d")
    data = requests.get(url+date).json()['data']
    if data.get('holiday', None):
        name = data['holiday']['name']
    elif data['lunar'].get('traditional', None):
        name = data['lunar']['traditional'][0]
    elif data['lunar'].get('jie_qi', None):
        name = data['lunar']['jie_qi']
    else:
        continue
    d = {'name':name,'date':date,"isOffDay":not (data['work']['is_work'])}
    print(d)
    feast.append(d)

with open('resource/holiday/{}.json'.format(year),'w') as f:
    json.dump({"days":feast},f, ensure_ascii=False)
# %%
