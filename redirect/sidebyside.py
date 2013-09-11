import urllib2 as url
from redirect.models import Redirect
def compare(count=0):
    if count:
        rs=Redirect.objects.all()[:count]
    else:
        rs=Redirect.objects.all()
    total = []
    match = []
    mismatch = []
    for r in rs:
        jcnlx_url = ""
        myjobs_url = ""
        report = {
            "jcnlx_url":"",
            "myjobs_url":"",
            "status":"",
            "guid":""
            }
        try:
            jcnlx_url = url.urlopen("http://jcnlx.com/%s10"%r.guid)
        except:
            pass            
        try:
            myjobs_url = url.urlopen("http://r.my.jobs:8002/%s10"%r.guid)
        except:
            pass
            
        if jcnlx_url:
            jcnlx_url = jcnlx_url.geturl()
        
        if myjobs_url:
            myjobs_url = myjobs_url.geturl()
        
        report["jcnlx_url"]=jcnlx_url
        report["myjobs_url"]=myjobs_url
        report["guid"]=r.guid
        if myjobs_url and jcnlx_url:
            if myjobs_url != jcnlx_url:
                report["status"] = "URL Mismatch"
                mismatch.append(report)
            else:
                report["status"] = "OK"
                match.append(report)                
        else:
            report["status"] = "URL Error"
            mismatch.append(report)
            
        total.append(report)
        
    print "%s OK | %s mismatch | %s total" % (
        len(match),len(mismatch),len(total)
        )
    
    result = {
        "ok": match,
        "error": mismatch,
        "all": total
        }
    return result
        
