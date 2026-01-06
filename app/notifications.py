from flask_mail import Message
from app import mail
from flask import current_app, render_template
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject,
        recipients=[to],
        html=render_template(template, **kwargs)
    )
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
