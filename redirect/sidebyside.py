from collections import defaultdict
import csv
from datetime import datetime, time
import json
import sys

import requests

from redirect.models import Redirect


def compare(start=0, count=0, guid="", vsid=""):
    """
    Comparison method for looking a the redirects generated from jcnlx and
    r.my.jobs and comparing the end result. This method is designed to be run
    from the command line only.
    
    Inputs:
    :start: The location in the test file to start. Defaults to 0.
    
    :count: The number of redirects to process. Primarily passed for testing
            purposes only. Default to 0, which the method interprets as all
            
    :guid:  The specific guid to process. If passed without the vsid parameter,
            then all view sources for the buid will be checked.
            
    :vsid:  View source to test. If passed without a guid parameter, it 
            processes all entries with a view source
    
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
        
    if guid: # trim down to specified guid
        guid_guid = []
        for g in guids:
            if g['guid'] == guid:
                guid_guid.append(g)
        guids=guid_guid
                
    if vsid: # trim down to specifed view source
        vsid_guid = []
        for g in guids:
            if g['vsid'] == str(vsid):
                vsid_guid.append(g)
        guids=vsid_guid
    
    redirects = []
    for guid in guids:
        if guid['vsid'] != 0:
            redirect_url = "%s%s" % (guid['guid'],guid['vsid'])
        else:
            redirect_url = guid['guid']
        redirects.append({
            "path":redirect_url,
            "guid":guid['guid'],
            "vsid":guid['vsid']
            })

    total = [] # track all processed records
    match = [] # track only matched records
    mismatch = [] #track only error records
        
    if not count: #control whether we do a partial or full test
        count = len(guids)
    
    do_process = True
    if count>10:
        ask_user = raw_input("There are %s records. Continue (y/n)?" % count)
        if ask_user != "y":
            do_process = False
    
    if not do_process:
        return "Processing cancelled"
    
    end = count+start #prevent index errors if count+start is > length of list
    if end > len(redirects):
        end = len(redirects)
        
    print "Processing %s records" % (end-start) #report correct record total
    # present whole number percentages ~ at the quartiles.
    status_update = [int(count*.01),int(count*.25),int(count*.5),int(count*.75)]
    record = 0    

    results = defaultdict(lambda: defaultdict(list))

    for r in redirects[start:end]:
        record=record+1
        if record in status_update:
            print "%s percent done" % int((float(record)/float(count))*100)
        jcnlx_url = ""
        myjobs_url = ""
        myjobs_headers = ""
        jcnlx_url_src="http://jcnlx.com/%s"%r['path']
        myjobs_url_src = "http://localhost:8000/%s"%r['path']
        try:
            results[r['path']]['jcnlx'] = requests.head(jcnlx_url_src)
        except:
            pass
        try:
            results[r['path']]['myjobs'] = requests.head(myjobs_url_src)
        except:
            pass

    for path in results.keys():
            
        if results[path]['jcnlx']:
            jcnlx_url = results[path]['jcnlx'].headers.get('location')
        
        if results[path]['myjobs']:
            mj_result = results[path]['myjobs']
            myjobs_url = mj_result.headers.get('location')
            myjobs_headers = dict(mj_result.headers)

        report = {
            "jcnlx_url":"",
            "myjobs_url":"",
            "status":"",
            "guid":"",
            "path":"",
            "vsid":""
            }

        report["guid"]=r['guid']
        report["vsid"]=r['vsid']
        report["jcnlx_url_src"]=jcnlx_url_src
        report["jcnlx_url"]=jcnlx_url
        report["myjobs_url_src"]=myjobs_url_src
        report["myjobs_url"]=myjobs_url
        report["x_headers"]=myjobs_headers
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
