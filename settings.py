#### Global settings for all modules ####
# Import this file into every module and specify settings here.


# Lock and wait settings
waitForGroupLockSeconds = 5
waitForUpgradeSeconds = 120
checkUpgradeStatusSeconds = 5
waitForRestartSeconds = 15

# Ops Manager settings
opsmgrServerUrl = 'http://localhost:8080' # Be sure there is no trailing slash here
opsmgrUser = 'admin'
opsmgrApiKey = '8155a1a2-99e2-4eac-9e13-d61855420afb'
opsmgrWebHookReturnValue = '{"ok": true}' # Value OpsMgr want to see returned from the webhook if all went well
opsmgrDefaultGroup = 'wf-test' # If O/M group is not provided in chat, we will use this one

# Queryable Backup settings
queryableBackupSettings = {
    'sourceCollection': 'testdb.testcoll',
    'queryableProxy':   'localhost:29000',
    'dumpPath':         '/Users/timo/tmp',
    'dumpName':         'db.dump'
}

sourceCluster = {
    'group' : 'Initial Group'
}

# Where to stand up the cluster that the queryable backup gets restored into
tempDestinationCluster = {
    'group' : 'Restore Group',
    'cluster': 'wf-restore',
    'server': ['r1'], # NOTE: Number entries in server and ports array must match
    'ports': [ 28000 ],
    'rs-size': 3,  # NOTE: number of members in the replica set (per shard if sharded cluster)
    'rs-name': 'wf-restore',
    'shards': 0,   # NOTE: shards 0 means plain replica set
    'protocolVersion': 1
}

# Final destination of the restored backup
restoreTargetCluster = {
    'dumpPath': '/Users/timo/tmp',
    'dumpName': 'db.dump2',
    'targetCluster': ['n1:26000','n1:26001','n2:26051'],
    'destCollection': 'testdb.testcoll'
}
