from django import forms
import tarfile
import yaml as yaml_lib
from cfy_wrapper.models import Blueprint


class BlueprintUploadForm(forms.ModelForm):
    """
    Feed this form with uploaded file and it will decide which of the two model fields is correct -
    archive or yaml.
    Using form instead of serializer due to rest_framework being too buggy when it comes to files.
    """
    def clean_archive(self):
        f = self.cleaned_data.get('archive')
        try:
            tarfile.open(fileobj=f)
            return f
        except tarfile.TarError:
            return None

    def clean_yaml(self):
        f = self.cleaned_data.get('yaml')
        try:
            yaml_lib.load(f)
            return f
        except yaml_lib.YAMLError:
            return None

    def clean(self):
        super(BlueprintUploadForm, self).clean()

        archive = self.cleaned_data.get('archive')
        yaml = self.cleaned_data.get('yaml')

        if (archive is None and yaml is None) or (archive is not None and yaml is not None):
            raise forms.ValidationError('Must upload either archive either yaml')

        return self.cleaned_data

    class Meta:
        model = Blueprint
        fields = ("archive", "yaml")