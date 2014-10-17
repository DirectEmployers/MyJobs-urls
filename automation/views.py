from django.shortcuts import render_to_response
from django.template import RequestContext

from automation.forms import SourceCodeFileUpload


def source_code_upload(request):
    context = {}
    if request.method == 'POST':
        post = request.POST.copy()
        upload_file = request.FILES.get('source_code_file')
        if hasattr(upload_file, 'name'):
            post['source_code_file'] = upload_file.name
        form = SourceCodeFileUpload(post, request.FILES)
        if form.is_valid():
            context['stats'] = form.save()
    else:
        form = SourceCodeFileUpload()
    context['form'] = form
    return render_to_response('automation/excel_upload_form.html',
                              {'form': form},
                              context_instance=RequestContext(request))
