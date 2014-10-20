from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from automation.forms import SourceCodeFileUpload


@staff_member_required
def source_code_upload(request):
    context = {}
    if request.method == 'POST':
        post = request.POST.copy()
        form = SourceCodeFileUpload(post, request.FILES)
        if form.is_valid():
            context['stats'] = form.save()
    else:
        form = SourceCodeFileUpload()
    context['form'] = form
    return render_to_response('automation/excel_upload_form.html',
                              context,
                              context_instance=RequestContext(request))
