import resend
from django.conf import settings
from django.template.loader import render_to_string
from .ics_service import build_appointment_ics

# ref: Resend email API — https://resend.com/docs


def send_training_plan_email(plan, recipient_email):
    resend.api_key = settings.RESEND_API_KEY

    html = render_to_string('emails/training_plan.html', {
        'plan': plan,
        'client': plan.client,
        'trainer': plan.trainer,
        'exercises': plan.exercises.all(),
    })

    response = resend.Emails.send({
        'from': f'{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>',
        'to': recipient_email,
        'subject': f'Your training plan: {plan.title}',
        'html': html,
    })

    return response


def send_appointment_email(appointment):
    resend.api_key = settings.RESEND_API_KEY

    html = render_to_string('emails/appointment.html', {
        'appointment': appointment,
        'client': appointment.client,
        'trainer': appointment.trainer,
    })

    ics_bytes = build_appointment_ics(appointment)
    import base64

    response = resend.Emails.send({
        'from': f'{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>',
        'to': appointment.client.email,
        'subject': f'Training session confirmed — {appointment.scheduled_at.strftime("%b %d at %H:%M")}',
        'html': html,
        'attachments': [{
            'filename': 'appointment.ics',
            'content': base64.b64encode(ics_bytes).decode('ascii'),
        }],
    })

    return response