#### Utility Functions including functions to get metrics from OpsMgr ####

import settings
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime
import dateutil.parser
import time
import json
import fcntl
import errno


# get groupID from OpsMgr given a group name
def getOpsMgrGroupId(name):
    retVal = None
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups'
    resp = requests.get(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Ops Manager groups - ' + `resp.status_code` + ' was returned')
        print(json.dumps(resp.json()))
    else:
        for grp in resp.json()['results']:
            if grp['name'].lower() == name.lower():
                retVal = grp['id']
                break
    return retVal


# get Host ID given either a host or a host and port
def getOpsMgrHostId(name, group):
    retVal = None
    h = getOpsMgrHost(name, group)
    if h is not None:
        retVal = h['id']
    return retVal


# get Host name, ID and port given either a host or a host and port
#   Note we want to be permissive here and allow hostnames less than the FQDN
#     so, we will match on the hostname sent in and the port (if specified) separately
def getOpsMgrHost(name, group):
    retVal = None
    host = getHostName(name)
    port = getPort(name)
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + group + "/hosts"
    resp = requests.get(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Ops Manager Hosts - ' + `resp.status_code` + ' was returned')
        print(json.dumps(resp.json()))
    else:
        for h in resp.json()['results']:
            # Split out the 2 names being compared and compare up to what we sent in
            #    i.e. 'node1', 'node1.aaa', etc will all match with 'node1.aaa.bbb.com'
            hostList = host.split('.')
            omList = h['hostname'].lower().split('.')
            match = True
            for i, item in enumerate(hostList):
                if omList[i] != hostList[i]:
                    match = False
                    break
            if match:
                if port is not None:
                    if port == h['port']:
                        retVal = h
                        break
                else:
                    retVal = h
                    break
    return retVal


# get Host names, ID and ports given a group and rplset
def getHostsInRplSet(rplSet, groupId):
    retVal = []
    for h in getHostsInGroup(groupId):
        if 'replicaSetName' in h:
            if h['replicaSetName'].lower() == rplSet.lower():
                retVal.append(h)
        else:
            continue
    if len(retVal) < 1:
        retVal = None
    return retVal


def getHostsInGroup(groupId):
    retVal = None
    if groupId is not None:
        url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + groupId + "/hosts"
        resp = requests.get(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
        if resp.status_code != 200:
            # This means something went wrong.
            print('---- ERROR Retrieving Ops Manager Hosts - ' + `resp.status_code` + ' was returned')
            print(json.dumps(resp.json()))
        else:
            retVal = resp.json()['results']
    return retVal


# Get all hosts in OpsMgr from all groups
def getAllHosts():
    retVal = None
    hosts = []
    for grp in getAllGroups():
        lst = getHostsInGroup(grp['id'])
        if lst is not None and len(lst) > 0:
            for l in lst:
                hosts.append(l)
    if len(hosts) > 0:
        retVal = hosts
    return retVal


# Get all groups for OpsMgr
def getAllGroups():
    retVal = None
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups'
    resp = requests.get(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Groups - ' + `resp.status_code` + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()['results']
    return retVal


# Pull automation config for a group
def getAutomationConfig(groupId):
    retVal = None
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/' + groupId + '/automationConfig'
    resp = requests.get(url, auth=HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Automation Config - ' + `resp.status_code` + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()
    return retVal


# Parse out minor version number from a string
def getMinorVersion(version):
    n = version.split('-')[0]
    l = n.split('.')
    v = l[len(l) - 1]
    return int(v)


# Parse out major version as a string (i.e. '3.2')
def getMajorVersion(version):
    l = version.split('.')
    return l[0] + '.' + l[1]


# Get next available minor version based on version sent in
# i.e.  3.2.11-ent  would return 3.2.12-ent if enabled
#       Note that it might skip versions too : 3.2.11-ent -> 3.2.14-ent
def getNextMinorVersion(automationConfig, version):
    retVal = None
    currentMinor = getMinorVersion(version)
    desiredMinor = 999
    currentMajor = getMajorVersion(version)

    for v in automationConfig['mongoDbVersions'] :
        if getMajorVersion(v['name']) == currentMajor and \
                getMinorVersion(v['name']) > currentMinor and \
                v['name'].endswith('ent') == version.endswith('ent') and \
                getMinorVersion(v['name']) < desiredMinor:
            desiredMinor = getMinorVersion(v['name'])
            retVal = v['name']

    return retVal




# get UTC Offset
def getUTCOffset():
    now_timestamp = time.time()
    return (datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp))


# Strip port number from OpsMgr host
def getHostName(hostnameAndPort):
    return hostnameAndPort.split(':')[0]


# Get port number from OpsMgr host
def getPort(hostnameAndPort):
    retVal = None
    p = hostnameAndPort.split(':')
    if len(p) > 1:
        retVal = int(p[1])
    return retVal


# Create a lock to ensure that 2 MongoBot requests cannot take an action at the same time
# Note that for OpsMgr type actions, the lock file is the group ID from OpsMgr as it's not
# a problem to modify different OpsMgr groups concurrently.
class FileLock:
    def __init__(self, filename=None):
        self.filename = './MONGODB_AUTOMATION_LOCK_FILE' if filename is None else filename
        self.lock_file = open(self.filename, 'w+')

    def unlock(self):
        fcntl.flock(self.lock_file, fcntl.LOCK_UN)

    def lock(self):
        waited = 0
        while True:
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

                return True
            except IOError as e:
                if e.errno != errno.EAGAIN:
                    raise e
                else:
                    time.sleep(1)
                    waited += 1
                    if waited >= settings.waitForGroupLockSeconds:
                        return False

