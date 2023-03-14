import caldav
from datetime import datetime, timedelta
from icalendar import Event
from caldav.lib.url import URL
from caldav.elements import dav, cdav

# 连接CalDav服务器
url = "https://caldav.feishu.cn"
pw = 'PL5NRJyBWR'
user = 'lei.zhang_stardust.ai'
client = caldav.DAVClient(url, password=pw, username=user)
principal = client.principal()
calendars = principal.calendars()

# 获取第一个日历
calendar = [c for c in calendars if 'Derek' in c.name][0]

# 检查接下来1天内是否有可用时间
now = datetime.now()
end = now + timedelta(days=1)

# 创建一个查询
events = calendar.search(start=now, end=end, event=True)

def event_to_dict(event):
    # 获取事件的各个属性
    start = event.instance.vevent.dtstart.value.strftime('%Y-%m-%d %H:%M:%S')
    end = event.instance.vevent.dtend.value.strftime('%Y-%m-%d %H:%M:%S')
    summary = event.instance.vevent.summary.value
    try:
        description = event.instance.vevent.description.value
    except:
        description = ''
    try:
        location = event.instance.vevent.location.value
    except:
        location = ''
    uid = event.instance.vevent.uid.value

    # 将事件属性组合成字典并返回
    event_dict = {
        'start': start,
        'end': end,
        'summary': summary,
        'description': description,
        'location': location,
        'uid': uid
    }
    return event_dict

# 判断是否有空闲时间
print(f'There are {len(events)} events')
for event in events:
    if not event.instance:
        print(event.data)
        continue
    print(event_to_dict(event))