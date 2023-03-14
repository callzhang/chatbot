import caldav
import icalendar
from tqdm import tqdm

# connect to CalDAV server and get principal
url = "https://caldav.feishu.cn"
pw = 'PL5NRJyBWR'
user = 'lei.zhang_stardust.ai'
client = caldav.DAVClient(url, password=pw, username=user)
principal = client.principal()

# find the calendar and get its data
calendars = principal.calendars()
calendar = [c for c in calendars if 'Derek' in c.name][0] 
events = calendar.events() # get all events in this calendar

# Create a new iCalendar object and add each event to it
new_calendar = icalendar.Calendar()
for event in tqdm(events):
    event_data = event.data
    event_ics = icalendar.Event.from_ical(event_data)
    new_calendar.add_component(event_ics)

# write the new icalendar object to a file
with open("calendar.ical", "wb") as f:
    f.write(new_calendar.to_ical())
