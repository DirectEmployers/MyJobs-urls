import csv
from datetime import datetime, time
import json
import sys
import urllib2 as url
from redirect.models import Redirect
def compare(count=0):
    """
    Comparison method for looking a the redirects generated from jcnlx and
    r.my.jobs and comparing the end result. This method is designed to be run
    from the command line only.
    
    Inputs:
    :count: The number of redirects to process. Primarily passed for testing
            purposes only. Default to 0, which the method interprets as all
    
    Returns:
    :result:    A multilevel dictionary split into the following keys:
                - ok (contains all matched comparisons)
                - error (contains all errors and mismatched comparisons)
                - all (contains everything)
                
                Each of the above is a dictionary of values with these keys:
                - jcnlx_url
                - myjobs_url
                - status
                - guid
    
    """
    filename = "fixtures/TestGUIDs.csv"
    guids = []
    with open(filename, 'rb') as f:
        reader=csv.reader(f)        
        for row in reader:
            guids.append({
                    'buid':row[0],
                    'vsid':row[1],
                    'guid':row[2]
                })
        del guids[0]
    
    redirects = []
    for guid in guids:
        if guid['vsid'] != 0:
            redirect_url = "%s%s" % (guid['guid'],guid['vsid'])
        else:
            redirect_url = guid['guid']
        redirects.append({
            "path":redirect_url,
            "guid":guid['guid']
            })

    
    total = [] # track all processed records
    match = [] # track only matched records
    mismatch = [] #track only error records
        
    if not count: #control whether we do a partial or full test
        count = len(guids)
    
    print "Processing %s records" % count
    status_update = [int(count*.01),int(count*.25),int(count*.5),int(count*.75)]
    record = 0    
    for r in redirects[0:count]:
        record=record+1
        if record in status_update:
            print "%s percent done" % int((float(record)/float(count))*100)
        jcnlx_url = ""
        myjobs_url = ""
        report = {
            "jcnlx_url":"",
            "myjobs_url":"",
            "status":"",
            "guid":"",
            "path":"",
            }
        jcnlx_url_src="http://jcnlx.com/%s"%r['path']
        myjobs_url_src = "http://r.my.jobs:8002/%s"%r['path']
        try:
            jcnlx_url = url.urlopen(jcnlx_url_src)
        except:
            pass            
        try:
            myjobs_url = url.urlopen(myjobs_url_src)
        except:
            pass
            
        if jcnlx_url:
            jcnlx_url = jcnlx_url.geturl()
        
        if myjobs_url:
            myjobs_url = myjobs_url.geturl()
        
        report["jcnlx_url_src"]=jcnlx_url_src
        report["myjobs_url_src"]=myjobs_url_src
        report["jcnlx_url"]=jcnlx_url
        report["myjobs_url"]=myjobs_url
        report["guid"]=r['guid']
        report["path"]=r['path']
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
    results_file = "comparison_log/sidebyside%s.json" % datetime.now().time()
    log = open(results_file,'w')
    log.write(json.dumps(result))
    return result
        
