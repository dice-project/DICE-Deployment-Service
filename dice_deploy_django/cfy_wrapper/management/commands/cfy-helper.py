from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from cfy_wrapper import tasks
from cfy_wrapper.models import Blueprint

"""
Example calls:
python manage.py cfy-helper resync-outputs  # resync outputs of all existing blueprints
python manage.py cfy-helper resync-outputs --blueprint_id=<id>  # resync outputs for this blueprint
"""


class Command(BaseCommand):
    help = 'Manually perform cfy operations'

    def add_arguments(self, parser):
        parser.add_argument('command', type=str, help='outputs|resync-outputs')
        parser.add_argument('--blueprint_id', type=str)

    def handle(self, *args, **options):
        if options['command'].lower() == 'outputs':
            print('Getting outputs')
            blueprint_id = options['blueprint_id']
            blueprint = Blueprint.get(blueprint_id)
            outputs = tasks.get_outputs(blueprint)
            print('Outputs are: %s' % outputs)
        elif options['command'].lower() == 'resync-outputs':
            print('Resyncing outputs')
            blueprint_id = options['blueprint_id']
            blueprints = []
            if blueprint_id:
                print('only for blueprint with id: %s' % blueprint_id)
                blueprints.append(Blueprint.get(blueprint_id))
            else:
                blueprints = Blueprint.objects.all()

            for blueprint in blueprints:
                try:
                    outputs = tasks.get_outputs(blueprint)
                    blueprint.outputs = outputs
                    blueprint.save()
                    print('[OK]  %s blueprint updated with outputs: %s' % (blueprint.id, outputs))
                except Exception, e:
                    print('[ERR] %s blueprint could not be updated: %s' % (blueprint.id, e))
        else:
            raise CommandError('Invalid command argument, got: %s' % options['command'])

