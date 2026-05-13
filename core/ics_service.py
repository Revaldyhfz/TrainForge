# core/ics_service.py
# Generate iCalendar (.ics) files for appointments.

from datetime import timedelta
from icalendar import Calendar, Event
import uuid


def build_appointment_ics(appointment):
    cal = Calendar()
    cal.add('prodid', '-//TrainForge//trainforge.app//EN')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')

    event = Event()
    event.add('uid', f'trainforge-{appointment.id}@trainforge.app')
    event.add('summary', f'Training session with {appointment.trainer.username}')
    event.add('dtstart', appointment.scheduled_at)
    event.add('dtend', appointment.scheduled_at + timedelta(minutes=appointment.duration_minutes))
    event.add('dtstamp', appointment.created_at)
    event.add('description', appointment.notes or 'Personal training session')

    cal.add_component(event)

    return cal.to_ical()