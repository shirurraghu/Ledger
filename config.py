import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'mysql://billinguser:vEg84aRs@localhost/billing'
    MAIL_SERVER = os.environ.get('smtp.mandrillapp.com')
    MAIL_PORT = 587
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('shirur.raghu@gmail.com')
    MAIL_PASSWORD = os.environ.get('md-J85zS526BCfK8MjGDW2F_w')
    ADMINS = ['shirur.raghu@gmail.com']
    RAZORPAY_KEY_ID = 'rzp_test_7bPWI4nWcRtQ0S'
    RAZORPAY_KEY_SECRET = 'hYKeEuVwpXXxAw1Vktyx14gT'
    SESSION_COOKIE_SAMESITE = 'Lax'  # Helps with cross-site cookie sharing
    SESSION_COOKIE_HTTPONLY = True   # Only accessible by the server, not JavaScript
    SESSION_COOKIE_SECURE = False    # Set to True if running over HTTPS
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'vEg84aRs@7790')



    MAIL_DEBUG = True
