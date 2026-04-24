from flask import render_template, current_app
from flask_mail import Message
from app import mail  # Import both app and mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        try:
            with mail.connect() as conn:
                conn.send(msg)  # Try sending email within connection context
        except Exception as e:
            current_app.logger.error(f"Error sending email: {e}")

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    msg = Message('[Billbook] Reset Your Password',
                  sender=app.config['ADMINS'][0],
                  recipients=[user.email])
    msg.body = render_template('email/reset_password.txt', user=user, token=token)
    msg.html = render_template('email/reset_password.html', user=user, token=token)

    # Option 1: Async send (optional but recommended)
    Thread(target=send_async_email, args=(app, msg)).start()

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # ✅ Use current_app._get_current_object() when passing app to thread
    threading.Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()
