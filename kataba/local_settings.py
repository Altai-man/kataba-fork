# Example of local settings
# Should be renamed to local_settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'python',                      # Or path to database file if using sqlite3.
        'USER': 'adminq9veewn',                      # Not used with sqlite3.
        'PASSWORD': 'D_F9Lc34fQsJ',                  # Not used with sqlite3.
        'HOST': url.hostname,
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

PIC_SIZE = 180.0 # Must be float!
THREADS = 8 # Threads per page, must be integer

TIME_ZONE = 'Europe/Kiev'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'as29DKJHg972kljh'
