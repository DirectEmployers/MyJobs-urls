from django.shortcuts import render_to_response
from django.template import RequestContext

from automation.forms import SourceCodeFileUpload


def source_code_upload(request):
    if request.method == 'POST':
        print request.POST
        post = request.POST.copy()
        upload_file = request.FILES.get('source_code_file')
        if hasattr(upload_file, 'name'):
            post['source_code_file'] = upload_file.name
        print request.FILES
        form = SourceCodeFileUpload(post, request.FILES)
        print form.is_valid()
        print form.errors
    else:
        form = SourceCodeFileUpload()
    return render_to_response('automation/excel_upload_form.html',
                              {'form': form},
                              context_instance=RequestContext(request))
