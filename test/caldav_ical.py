from datetime import datetime
import json
from pytz import UTC # timezone
import caldav
from icalendar import Calendar, Event

# CalDAV info
url = "https://caldav.feishu.cn"
userN = "lei.zhang_stardust.ai"
passW = "PL5NRJyBWR"

client = caldav.DAVClient(url=url, username=userN, password=passW)
principal = client.principal()
calendars = principal.calendars()

if len(calendars) > 0:
    calendar = calendars[0]
    print ("Using calendar", calendar)
    results = calendar.events()
    eventSummary = []
    eventDescription = []
    eventDateStart = []
    eventdateEnd = []
    eventTimeStart = []
    eventTimeEnd = []

    for eventraw in results:

        event = Calendar.from_ical(eventraw._data)
        for component in event.walk():
            if component.name == "VEVENT":
                print (component.get('summary'))
                eventSummary.append(component.get('summary'))
                print (component.get('description'))
                eventDescription.append(component.get('description'))
                startDate = component.get('dtstart')
                print (startDate.dt.strftime('%m/%d/%Y %H:%M'))
                eventDateStart.append(startDate.dt.strftime('%m/%d/%Y'))
                eventTimeStart.append(startDate.dt.strftime('%H:%M'))
                endDate = component.get('dtend')
                print (endDate.dt.strftime('%m/%d/%Y %H:%M'))
                eventdateEnd.append(endDate.dt.strftime('%m/%d/%Y'))
                eventTimeEnd.append(endDate.dt.strftime('%H:%M'))
                dateStamp = component.get('dtstamp')
                print (dateStamp.dt.strftime('%m/%d/%Y %H:%M'))
                print ('')

    # Modify or change these values based on your CalDAV
    # Converting to JSON
    data = [{ 'Events Summary':eventSummary[0], 'Event Description':eventDescription[0],'Event Start date':eventDateStart[0], 'Event End date':eventdateEnd[0], 'At:':eventTimeStart[0], 'Until':eventTimeEnd[0]}]
    data_string = json.dumps(data)
    print ('JSON:', data_string)