from django.core.management.base import BaseCommand, CommandError
from djcelery.management.commands import celery
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
            print('Starting celery')
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
            print('Stopping celery')
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
        elif options['command'].lower() == 'purge':
            print('Purging celery')
            # following is a mimic of manually calling
            # 'manage.py celery ampq queue.purge <QUEUE_NAME>' which cannot be called with
            # call_command due to bug in django-celery implementation of management commands...
            command = celery.Command()
            args = [
                'manage.py',
                'celery',
                'amqp',
                'queue.purge',
                'dice_deploy' if not options['unit_tests'] else 'dice_deploy_tests',
            ]
            try:
                command.run_from_argv(args)
            except SystemExit:
                pass
        else:
            raise CommandError('Invalid command argument, got: %s' % options['command'])

