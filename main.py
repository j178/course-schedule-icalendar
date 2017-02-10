from icalendar import Calendar, Event

with open('vcal.ics') as f:
    cal = Calendar.from_ical(f.read())
    for component in cal.walk():
        if component.name == 'VEVENT':
            print(component.get('summary'))
