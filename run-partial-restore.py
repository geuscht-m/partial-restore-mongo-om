from __future__ import print_function        # For Python 3 compatibility
import utils
import settings
import requests
import pymongo
import subprocess
import pprint
import time

def runWholeProcess(group_name, cluster, timestamp, collection_name, settings_file):
    # Extract temporary restore from queryable backup
    if checkQueryableBackupAccess(settings):
        print('Looks like we have a working queryable backup')
        if runMongoDump(utils.buildMongoDBURI(settings.queryableBackupSettings['queryableProxy']),
                        settings.queryableBackupSettings['sourceCollection'],
                        settings.queryableBackupSettings['dumpPath'],
                        settings.queryableBackupSettings['dumpName']):
            conn_str = createDestinationCluster(settings)
            runMongoRestore(conn_str, settings)
    else:
        print("Couldn't find database or collection, aborting")
    # Restore into target cluster
    if runMongoDump(utils.buildMongoDBURI(settings.tempDestinationCluster['targetCluster']),
                     settings.queryableBackupSettings['sourceCollection'],
                     settings.restoreTargetCluster['dumpPath'],
                     settings.restoreTargetCluster['dumpName']):
        checkAndDropTargetCollection(settings.restoreTargetCluster['targetCluster'], settings.restoreTargetCluster['destCollection'])
        conn_str = utils.buildMongoDBURI(settings.restoreTargetCluster['targetCluster'])
        runMongoRestore(conn_str, settings)


def getQueryableBackupInfo(group_name, cluster, timestamp):
    group_id = utils.getOpsMgrGroupId(group_name)
    clusterID, replSets = getClusters(group_id, cluster)
    backupInfo = startRestoreJob(group_id, clusterID, replSets, timestamp)

    return backupInfo

def startTempMongoD(groupName, settingInfo):
    autoConfig = utils.getAutomationConfig(utils.getOpsMgrGroupId(groupName))
    autoConfig = addSettings(settingsInfo)
    updateAutomationConfig(autoConfig)
    return waitForDeployment(autoConfig)

def stopTempMongoD(tempDB, settingInfo):
    autoConfig = utils.getAutomationConfig(utils.getOpsMgrGroupId(tempDB.groupName))
    autoConfig = removeSettings(settingsInfo)
    updateAutomationConfig(autoConfig)
    return waitForDeployment(autoConfig)

def getClusters(group_id, cluster_name):
    print("Trying to get cluster id for group", group_id, "cluster", cluster_name)
    cluster_id, repl_sets = utils.getClusterId(group_id, cluster_name)
    return (cluster_id, repl_sets)

def startRestoreJob(group_id, cluster_id, repl_sets, timestamp):
    url = utils.urlBuilder(settings, 'groups', group_id, 'clusters', cluster_id, 'restoreJobs')
    auth = utils.authBuilder(settings)
    resp = requests.get(url, auth=auth)
    print('response to restoreJobs post is', resp.json())
    return {}

def addSettings(config):
    return config

def removeSettings(config):
    return config

def checkQueryableBackupAccess(settings):
    qb_proxy = settings.queryableBackupSettings['queryableProxy']
    db_name,db_coll  = utils.parseQueryableCollInfo(settings)

    if db_name is None:
        return False

    client = pymongo.MongoClient(qb_proxy)
    dbnames = client.list_database_names()

    if db_name in dbnames:
        if db_coll is not None:
            collections = client[db_name].list_collection_names()
            if db_coll in collections:
                return True
        else:
            return True
    return False

def runMongoDump(fromClusterInfo, namespace, dump_path, dump_name):
    db_name, db_coll = utils.parseCollNamespaceInfo(namespace)
    dump_args = utils.createMongoDumpArgs(fromClusterInfo, dump_path, dump_name, db_name, db_coll)
    success   = subprocess.call(dump_args)
    print('Output from mongodump:', success)
    return success == 0
    
def createDestinationCluster(parameters):
    #monitoring_config = getSourceClusterMonitoringConfig(parameters.sourceCluster['group'], parameters)
    dest_group_id = utils.getGroupIdFromName(parameters.tempDestinationCluster['group'])
    config = utils.getAutomationConfig(dest_group_id)
    #utils.pushAutomationConfig(parameters.sourceCluster['group'], config)
    #raise Exception("push done")
    if not utils.isMonitoringAgentPresent(config):
        raise Exception("Monitoring agent not present, aborting creation of temporary cluster")
        
    replicaSetMembers = []
    rs_index = 0
    for rs_member in parameters.tempDestinationCluster['targetCluster']:
        server, port = utils.splitHostAndPort(rs_member)
        process = {
            'version': '4.0.4',
            'name': parameters.tempDestinationCluster['cluster'] + '_' + str(port),
            'hostname': server,
            'logRotate': {
                'sizeThresholdMB': 1000.0,
                'timeThresholdHrs': 24
            },
            "manualMode":False,
            'authSchemaVersion': 5,

            "disabled":False,
            "featureCompatibilityVersion":"4.0",
            'processType': 'mongod',
            'args2_6': {
                'net': { 'port': port },
                'storage' : { 'dbPath': '/data/' + str(port) },
                'systemLog': {
                    'path': '/data/' + str(port) + '/mongod.log',
                    'destination': 'file'
                },
                'replication': { 'replSetName': parameters.tempDestinationCluster['rs-name'] }
            }
        }
        config['processes'].append(process)
        replicaSetMembers.append({ u'_id': rs_index,
                                  u'arbiterOnly': False,
                                  u'buildIndexes': True,
                                  u'hidden': False,
                                  u'host': parameters.tempDestinationCluster['cluster'] + '_' + str(port),
                                  u'priority': 1.0,
                                  u'slaveDelay': 0,
                                  u'votes': 1})
        rs_index += 1
        
    config['replicaSets'].append({ '_id' : parameters.tempDestinationCluster['cluster'],
                                   'members': replicaSetMembers,
                                   'protocolVersion':parameters.tempDestinationCluster['protocolVersion']})
            
    pp =  pprint.PrettyPrinter(indent=2)
    pp.pprint(config)
    success = utils.pushAutomationConfig(dest_group_id, config)
    if not success:
        raise Exception("Pushing the new replica set configuration failed")
    utils.waitForAutomationStatus(dest_group_id)
    return utils.buildMongoDBURI(settings.tempDestinationCluster['targetCluster'])

def runMongoRestore(connection_str, parameters):
    db_name, db_coll = utils.parseQueryableCollInfo(parameters)
    restore_args = utils.createMongoRestoreArgs(parameters, connection_str, db_name, db_coll, parameters.queryableBackupSettings['dumpPath'])
    success = subprocess.call(restore_args)
    return success == 0

def getSourceClusterMonitoringConfig(clusterName, parameters):
    group_id = utils.getGroupIdFromName(parameters.sourceCluster['group'])
    config = utils.getAutomationConfig(group_id)
    #pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(config)
    return config['monitoringVersions']

def checkAndDropTargetCollection(cluster_info, namespace):
    db_name, db_coll = utils.parseCollNamespaceInfo(namespace)
    conn_info  = utils.buildMongoDBURI(cluster_info)
    connection = pymongo.MongoClient(conn_info)
    db = connection[db_name]
    if db_coll and db_coll in db.collection_names():
        print('Dropping target collection', db_coll)
        db.drop_collection(db_coll)

runWholeProcess("Initial Group", "wf-test", 0, "testcoll", "settings")
