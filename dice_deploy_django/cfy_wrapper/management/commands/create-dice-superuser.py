from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError

"""
This management command is needed in order to enable automatic provisioning of Wrapper without
prompt for superuser password.
Example calls:
python manage.py create-dice-superuser
python manage.py create-dice-superuser --username john --password abc
"""


class Command(BaseCommand):
    help = 'Starts or stops celery service.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Defaults to "root"')
        parser.add_argument('--email', type=str, help='Defaults to "root@email.com"')
        parser.add_argument('--password', type=str, help='Defaults to "root"')
        parser.set_defaults(username='root')
        parser.set_defaults(email='root@email.com')
        parser.set_defaults(password='root')

    def handle(self, *args, **options):
        print('Creating superuser "%s" with password %s' %
              (options['username'], '*'*len(options['username'])))
        try:
            User.objects.create_superuser(
                username=options['username'],
                email=options['email'],
                password=options['password'],
            )
        except IntegrityError, e:
            print 'There was a problem creating superuser: %s' % e
            print 'Please create superuser on your own later.'
            return
        print('Success')


