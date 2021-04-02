
import os
import json
with open('/etc/config.json') as config_file:
    config = json.load(config_file)

class Config: 
    SECRET_KEY = config.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = config.get('EMAIL_USER')
    MAIL_PASSWORD = config.get('EMAIL_PASS')
    DISCORD_CLIENT_ID = config.get('DISCORD_ID')
    DISCORD_CLIENT_SECRET = config.get('DISCORD_SECRET')
    DISCORD_REDIRECT_URI = "https://thecorporation.space/discord_callback"
    DISCORD_BOT_TOKEN = config.get('DISCORD_BOT_TOKEN')
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = config.get('RECAP_PUBKEY')
    RECAPTCHA_PRIVATE_KEY = config.get('RECAP_PRVKEY')
    RECAPTCHA_DATA_ATTRS = {'theme': 'dark'}
    RECAPTCHA_DISABLE = True