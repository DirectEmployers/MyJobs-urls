from django import forms


class SourceCodeFileUpload(forms.Form):
    source_code_file = forms.FileField(required=True)
    source_code_parameter = forms.CharField(required=False)
    buids = forms.CharField(required=True)