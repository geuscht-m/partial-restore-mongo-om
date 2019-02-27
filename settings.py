#### Global settings for all modules ####
# Import this file into every module and specify settings here.


# Lock and wait settings
waitForGroupLockSeconds = 5
waitForUpgradeSeconds = 120
checkUpgradeStatusSeconds = 5
waitForRestartSeconds = 15

# Ops Manager settings
opsMgrSettings = {
    'serverUrl': 'http://localhost:8080', # Be sure there is no trailing slash here
    'user': 'admin',
    'apiKey': 'e9771327-fe09-4a3f-8fb4-3289ff2aa75b'
}

# Queryable Backup settings
queryableBackupSettings = {
    'sourceCollection': 'testdb.testcoll',
    'queryableProxy':   [ 'localhost:29000' ],
    'dumpPath':         '/Users/timo/tmp',
    'dumpName':         'db.dump'
}

#sourceCluster = {
#    'group' : 'Initial Group'
#}

# Where to stand up the cluster that the queryable backup gets restored into
tempDestinationCluster = {
    'group' : 'Restore Group',
    'cluster': 'wf-restore',
    #'targetCluster': ['r1:28000','r1:28001','r2:28002' ],
    'targetCluster': ['r1:28000'],
    'rs-name': 'wf-restore',
    'shards': 0,   # NOTE: shards 0 means plain replica set
    'protocolVersion': 1,
    'mongo-version': '4.0.5',
    'featureCompatibility': '4.0'
}

# Final destination of the restored backup
restoreTargetCluster = {
    'dumpPath': '/Users/timo/tmp',
    'dumpName': 'db.dump2',
    'targetCluster': ['n1:26000','n1:26001','n2:26051'],
    'destCollection': 'testdb.testcoll'
}
