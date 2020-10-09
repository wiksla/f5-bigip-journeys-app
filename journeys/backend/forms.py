from django import forms


class SourceForm(forms.Form):
    ucs_file = forms.FileField(required=True)
    ucs_passphrase = forms.CharField(required=False, initial=None)
    as3_file = forms.FileField(required=False)


class FileUploadFrom(forms.Form):
    file = forms.FileField(required=True)
