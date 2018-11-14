import util

def getQueryableBackupInfo(groupName, cluster, timestamp):
    groupId = util.getOpsMgrGroupId(groupName)
    clusterID, replSets = getClusters(groupId, cluster)
    backupInfo = startRestoreJob(clusterID, replSets, timestamp)

    return backupInfo

def startTempMongoD(groupName, settingInfo):
    autoConfig = getAutomationConfig(getGroupID(groupName))
    autoConfig = addSettings(settingsInfo)
    updateAutomationConfig(autoConfig)
    return waitForDeployment(autoConfig)

def stopTempMongoD(tempDB, settingInfo):
    autoConfig = getAutomationConfig(getGroupID(tempDB.groupName))
    autoConfig = removeSettings(settingsInfo)
    updateAutomationConfig(autoConfig)
    return waitForDeployment(autoConfig)
    
def runTheWholeThing(groupName, cluster, timestamp, collectionName, settingsFile):
    storedSettings = loadSettingsFile(settingsFile)

    qb = getQueryableBackup(groupName, cluster, timestamp)
    tempMDB = startTempMongoD(storedSettings.tmpRestoreGroup, storedSettings.RSSettings)

    dumpCollection(collName)
    restoreCollection(collName, tempMDB)
