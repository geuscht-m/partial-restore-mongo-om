#### Utility Functions including functions to get metrics from OpsMgr ####

import settings
import requests
from requests.auth import HTTPDigestAuth
import time
import json
import urllib
import pprint

# Helper - build the URLs
def urlBuilder(settings, *parameters):
    #print('len parameters is', len(parameters), 'parameters is', parameters)
    retval = settings.opsmgrServerUrl + '/api/public/v1.0/'
    retval += '/'.join(filter(None, parameters))
    return retval

def authBuilder(settings):
    return HTTPDigestAuth(settings.opsmgrUser, settings.opsmgrApiKey)

# get groupID from OpsMgr given a group name
def getOpsMgrGroupId(name):
    retVal = None
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups'
    resp = requests.get(url, auth=authBuilder(settings))
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
    url  = urlBuilder(settings, 'groups', group, '/hosts')
    resp = requests.get(url, auth=authBuilder(settings))
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

def getGroupIdFromName(group_name):
    url = settings.opsmgrServerUrl + '/api/public/v1.0/groups/byName/' + urllib.quote(group_name)
    #print('group id from name url is ', url)
    resp = requests.get(url, auth=authBuilder(settings))
    if resp.status_code != 200:
        print(json.dumps(resp.json()))
        return None
    else:
        return resp.json()['id']
        
# Get the cluster id for a cluster
def getClusterId(group_id, cluster_name):
    url  = urlBuilder(settings, 'groups', group_id, 'clusters')
    resp = requests.get(url, auth=authBuilder(settings))
    if resp.status_code != 200:
        print(json.dumps(resp.json()))
        return None
    else:
        for cluster_info in resp.json()['results']:
            if cluster_info['clusterName'].lower() == cluster_name.lower():
                return (cluster_info['id'], cluster_info['replicaSetName'])
    return None
    

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
        url  = urlBuilder(settings, 'groups', groupId, 'hosts')
        resp = requests.get(url, auth=authBuilder(settings))
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
    url  = urlBuilder(settings, 'groups')
    resp = requests.get(url, auth=authBuilder(settings))
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
    url = urlBuilder(settings, 'groups', groupId, 'automationConfig')
    print('get request url is', url)
    resp = requests.get(url, auth=authBuilder(settings))
    if resp.status_code != 200:
        # This means something went wrong.
        print('---- ERROR Retrieving Automation Config - ' + `resp.status_code` + ' was returned')
        print(json.dumps(resp.json()))
    else:
        retVal = resp.json()
    return retVal

def pushAutomationConfigUpdate(group_id, config, url_suffix = None):
    url = urlBuilder(settings, 'groups', group_id, 'automationConfig', url_suffix)
    print('post request URL is', url)
    resp = requests.put(url, auth=authBuilder(settings), data=json.dumps(config), headers={ 'Content-type':'application/json'})
    if resp.status_code != 200:
        print('Posting new automation config resulted in error', resp.status_code)
        print(json.dumps(resp.json()))
        return False
    return True
    
def pushMonitoringConfig(group_id, config):
    return pushAutomationConfigUpdate(group_id, config, 'monitoringAgentConfig')

def pushAutomationConfig(group_id, config):
    return pushAutomationConfigUpdate(group_id, config)

# Strip port number from OpsMgr host
def getHostName(hostnameAndPort):
    return splitHostAndPort(hostnameAndPort)[0]


# Get port number from OpsMgr host
def getPort(hostnameAndPort):
    return splitHostAndPort(hostnameAndPort)[1]

def parseQueryableCollInfo(parameters):
    db_coll = parameters.queryableBackupSettings['sourceCollection']
    return parseCollNamespaceInfo(db_coll)

def parseCollNamespaceInfo(namespace_info):
    parts = namespace_info.split('.')
    num_parts = len(parts)
    if num_parts == 0:
        return (None, None)
    elif num_parts == 1:
        return (parts[0], None)
    elif num_parts == 2:
        return (parts[0], parts[1])
    else:
        print('More parts than expected in the db/coll specification:', db_coll)
        return (None, None)

def splitHostAndPort(host_port_string):
    elements = host_port_string.split(':')
    if len(elements) == 1:
        return (elements[0], '27017')
    elif len(elements) == 2:
        return (elements[0], elements[1])
    else:
        return (None, None)
    
def createMongoDumpArgs(clusterURI, dump_path, dump_name, db_name, db_coll):
    #host, port = splitHostAndPort(fromClusterInfo)
    args = [ 'mongodump', '--uri', clusterURI + '/' + db_name ]
    if db_coll is not None:
        args.append('-c')
        args.append(db_coll)
    args.append('-o')
    args.append('/'.join([dump_path, dump_name]))
    print('args is ', args)
    return args

def createMongoRestoreArgs(parameters, conn_str, db_name, db_coll, dump_path):
    args = [ 'mongorestore', '--uri=' + conn_str, '--nsInclude', db_name + '.' + db_coll]
    args.append(dump_path + '/db.dump/')
    print('restore args is', args)
    return args

def isMonitoringAgentPresent(config):
    # Check if we have monitoring agent versions present
    if not config['monitoringVersions']:
        return False
    return True

def installMonitoringAgent(group_id, monitoring_config):
    if not monitoring_config:
        raise Exception("Source monitoring config is empty, cannot duplicate")
    if not settings.tempDestinationCluster['server']:
        raise Exception("No destination servers specified")
    #first_server_monitoring = monitoring_config[0]
    #first_server_monitoring['hostname'] = settings.destinationCluster['server'][0]
    monitoring_hostname = settings.tempDestinationCluster['server'][0]
    monitoring_settings = { 'hostname':monitoring_hostname }
    #pp = pprint.PrettyPrinter(indent = 2)
    #pp.pprint(first_server_monitoring)
    config = getAutomationConfig(group_id)
    config['monitoringVersions'].append(monitoring_settings)
    #config['backupVersions'][0]['hostname'] = settings.destinationCluster['server'][0]
    #json_config = json.dumps(config)
    #pp = pprint.PrettyPrinter(indent = 2)
    #pp.pprint(json_config)
    pushAutomationConfig(group_id, config)
    #waitForAutomationStatus(group_id)
                        

def waitForAutomationStatus(group_id):
    while True:
        url = urlBuilder(settings, 'groups', group_id, 'automationStatus')
        resp = requests.get(url, auth=authBuilder(settings))
        if resp.status_code != 200:
            raise Exception('Unable to retrieve automation status, status_code was', resp.status_code)
        status = resp.json()
        goalVersion = status['goalVersion']
        if not filter(lambda(x): x['lastGoalVersionAchieved'] < goalVersion, status['processes']):
            print('All processes in goal state')
            break
        time.sleep(5)
    
    
def waitForAgentInstall(group_id):
    waitForAutomationStatus(group_id)

def buildMongoDBURI(clusterInfo):
    uri = "mongodb://" + ','.join(clusterInfo)
    return uri
