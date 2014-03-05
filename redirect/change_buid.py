from redirect.models import *


old = [27196]

new = [14383]

old_new = dict(zip(old, new))

def change_buid():
    dms = list(DestinationManipulation.objects.filter(buid__in=old))
    cms = list(CanonicalMicrosite.objects.filter(buid__in=old))


    for item in dms:
        item.buid = old_new[str(item.buid)]
        item.id = None
        item.pk = None
        item.save()
    for item in cms:
        item.buid = old_new[str(item.buid)]
        item.save()
