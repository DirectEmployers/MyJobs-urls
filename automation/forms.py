from django import forms
from django.core.exceptions import ValidationError

from automation.source_codes import process_spreadsheet
from redirect.models import Redirect

PARAMETERS = {
    'brassring': 'codes',
    'icims': ['mode', 'iis', 'iisn'],
    'taleo': 'src',
    'silkroad': 'jobboardid',
    'openhire': 'jobboardid',
    'ultipro': '_jbsrc',
    'apply2jobs': 'sid',
    'applytracking': 's',
    'catsone': 'ref',
    'recruitmentplatform': 'stype',
    'navicus': 'Source'
}


class SourceCodeFileUpload(forms.Form):
    source_code_file = forms.FileField(required=True)
    source_code_parameter = forms.CharField(required=False)
    buids = forms.CharField(required=True)

    def clean_buids(self):
        buids = self.data.get('buids', None)
        if buids is not None:
            buids = buids.split(',')
            buids = [buid.strip() for buid in buids]
            if not all([buid.isdigit() for buid in buids]):
                raise ValidationError('Buids provided are not numeric')
        else:
            raise ValidationError('No buids provided')

    def clean_source_code_parameter(self):
        parameter = self.cleaned_data.get('source_code_parameter')
        buids = self.data.get('buids').split(',')

        test_job = Redirect.objects.filter(buid__in=buids,
                                           expired_date__isnull=True)
        if test_job.count():
            test_job = test_job[0]
        return parameter

    def clean(self):
        self.cleaned_data['source_code_file'] = process_spreadsheet(
            self.cleaned_data['source_code_file'],
            self.cleaned_data['buids'],
            self.cleaned_data['source_code_parameter'])
