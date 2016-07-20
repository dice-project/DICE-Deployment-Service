from rest_framework.serializers import ValidationError

from .base import BaseTest

import datetime
import mock
import uuid

from cfy_wrapper.serializers import (
    BlueprintSerializer,
)

from cfy_wrapper.models import Input


class BlueprintSerializerTest(BaseTest):

    def test_valid_serialization(self):
        id = uuid.uuid4()
        b = mock.MagicMock(id=id, state_name="test", outputs={"k": "v"},
                           modified_date=datetime.datetime(2015, 10, 3),
                           in_error=False)
        d = BlueprintSerializer(b).data
        self.assertEqual({
            "id": str(id),
            "state_name": "test",
            "modified_date": "2015-10-03T00:00:00",
            "outputs": {"k": "v"},
            "in_error": False,
        }, d)

    def test_prevent_saving(self):
        id = uuid.uuid4()
        data = {
            "id": str(id),
            "state_name": "test",
            "modified_date": "2015-10-03T00:00:00",
            "outputs": {"test": "dict"},
            "in_error": True,
        }
        s = BlueprintSerializer(data=data)
        s.is_valid()
        self.assertTrue(s.is_valid(raise_exception=True))
        with self.assertRaises(Exception):
            s.save()
