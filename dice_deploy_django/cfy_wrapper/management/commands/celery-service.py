from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import subprocess

"""
Example calls:
python manage.py celery-service start
python manage.py celery-service stop
"""


class Command(BaseCommand):
    help = 'Starts or stops celery service.'

    def add_arguments(self, parser):
        parser.add_argument('command', type=str, help='start|stop')
        parser.add_argument('--unit_tests', action='store_true',
                            help='Add this flag to run celery-test-service instead of celery-service')
        parser.set_defaults(unit_tests=False)

    def handle(self, *args, **options):
        print('unit_tests: %s' % options['unit_tests'])

        if options['command'].lower() == 'start':
            print('Starting celery for app %s' % settings.CELERY_APP_NAME)
            p = subprocess.Popen([
                'sudo',
                'service',
                'celery-service' if not options['unit_tests'] else 'celery-test-service',
                'start'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if 'start/running' in out or 'already running' in err:
                print('Success')
            else:
                print('ERROR: %s\n%s' % (out, err))
        elif options['command'].lower() == 'stop':
            print('Stopping celery for app %s' % settings.CELERY_APP_NAME)
            p = subprocess.Popen([
                'sudo',
                'service',
                'celery-service' if not options['unit_tests'] else 'celery-test-service',
                'stop'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if 'stop/waiting' in out:
                print('Success')
            else:
                print('ERROR: %s\n%s' % (out, err))
        else:
            raise CommandError('Invalid command argument, got: %s' % options['command'])

