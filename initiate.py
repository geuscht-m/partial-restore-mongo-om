from __future__ import print_function        # For Python 3 compatibility
import utils
import settings
import requests
import pymongo
import subprocess

def getQueryableBackupInfo(group_name, cluster, timestamp):
    group_id = utils.getOpsMgrGroupId(group_name)
    #print("Group id for group", group_name, " is ", groupId)
    clusterID, replSets = getClusters(group_id, cluster)
    #print("getClusters returned ", clusterID, "and", replSets)
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

def loadSettingsFile(file_name):
    return {'tmpRestoreGroup': 'abd', 'RSSettings': 'wf-restore'}

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
    
def runTheWholeThing(group_name, cluster, timestamp, collection_name, settings_file):
    storedSettings = loadSettingsFile(settings_file)

    #qb = getQueryableBackupInfo(group_name, cluster, timestamp)
    #tempMDB = startTempMongoD(storedSettings['tmpRestoreGroup'], storedSettings['RSSettings'])

    #dumpCollection(collName)
    #restoreCollection(collName, tempMDB)
    if checkQueryableBackupAccess(settings):
        print('Looks like we have a working queryable backup')
        runMongoDump(settings)
        conn_str = createDestinationCluster(settings)
        runMongoRestore(conn_str, settings)
    else:
        print("Couldn't find database or collection, aborting")


def checkQueryableBackupAccess(settings):
    qb_proxy = settings.queryableProxy
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

def runMongoDump(parameters):
    dump_path = parameters.queryableDumpPath
    db_name,db_coll = utils.parseQueryableCollInfo(parameters)
    dump_args = utils.createMongoDumpArgs(parameters, db_name, db_coll)
    success   = subprocess.call(dump_args)
    #output    = success.stdout.read()
    #print("Output from mongodump:", success, output)
    print('Output from mongodump:', success)
    
def createDestinationCluster(parameters):
    connection_str = 'localhost:26000'
    return connection_str

def runMongoRestore(connection_str, parameters):
    dump_path = parameters.queryableDumpPath
    db_name, db_coll = utils.parseQueryableCollInfo(parameters)
    restore_args = utils.createMongoRestoreArgs(parameters, connection_str, db_name, db_coll, dump_path)
    success = subprocess.call(restore_args)
    return success == 0
    
runTheWholeThing("Initial Group", "wf-test", 0, "testcoll", "settings")
