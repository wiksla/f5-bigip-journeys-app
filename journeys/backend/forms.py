from django import forms
from django.core.exceptions import ValidationError


class SourceForm(forms.Form):
    ucs_file = forms.FileField(required=False)
    ucs_passphrase = forms.CharField(required=False, initial=None)
    as3_file = forms.FileField(required=False)
    username = forms.CharField(max_length=64, required=False)
    password = forms.CharField(max_length=64, required=False)
    host = forms.CharField(max_length=256, required=False)

    def clean(self):
        super(SourceForm, self).clean()

        ucs_file = self.cleaned_data.get("ucs_file", None)
        if ucs_file:
            return

        username = self.cleaned_data.get("username", None)
        password = self.cleaned_data.get("password", None)
        host = self.cleaned_data.get("host", None)

        if username and password and host:
            return

        raise ValidationError("Either ucs_file or credentials has to be passed")


class FileUploadFrom(forms.Form):
    file = forms.FileField(required=True)
