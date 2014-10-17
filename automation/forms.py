from django import forms

from automation.source_codes import process_spreadsheet, add_source_codes
from redirect.models import Redirect

ATS_PARAMETERS = {
    'brassring': 'codes',
    # reenable when we come up with a good way of handling this
    #'icims': ['mode', 'iis', 'iisn'],
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
    buids = forms.CharField(required=True)
    source_code_parameter = forms.CharField(required=False)

    def clean_buids(self):
        buids = self.data['buids']
        if buids:
            buids = buids.split(',')
            buids = [buid.strip() for buid in buids]
            if not all([buid.isdigit() for buid in buids]):
                raise forms.ValidationError('Buids provided are not numeric')
        else:
            raise forms.ValidationError('No buids provided')
        return buids

    def clean_source_code_parameter(self):
        parameter = self.cleaned_data['source_code_parameter']
        buids = self.data['buids'].split(',')

        test_job = Redirect.objects.filter(buid__in=buids,
                                           expired_date__isnull=True)
        if test_job.count():
            test_job = test_job[0]
            for url_part, key in ATS_PARAMETERS.items():
                if url_part in test_job.url:
                    parameter = key
                    break
        if not parameter:
            raise forms.ValidationError("Can't guess source code parameters")
        return parameter

    def clean(self):
        cleaned_data = super(SourceCodeFileUpload, self).clean()
        if all(field in cleaned_data for field in ['source_code_parameter',
                                                   'buids']):
            cleaned_data['source_codes'] = process_spreadsheet(
                cleaned_data['source_code_file'],
                cleaned_data['buids'],
                cleaned_data['source_code_parameter'],
                add_codes=False)
        return cleaned_data

    def save(self):
        return add_source_codes(self.cleaned_data['buids'],
                                self.cleaned_data['source_codes'])
