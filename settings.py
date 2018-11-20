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
opsmgrApiKey = 'b22c2049-6ca9-422e-a20e-e3c6d5d25aaf'
opsmgrWebHookReturnValue = '{"ok": true}' # Value OpsMgr want to see returned from the webhook if all went well
opsmgrDefaultGroup = 'wf-test' # If O/M group is not provided in chat, we will use this one

# Queryable Backup settings
restoreCollection = 'testdb.testcoll'
queryableProxy    = 'localhost:27017'
queryableDumpPath = '/Users/timo/tmp'
queryableDumpName = 'db.dump'

destinationCluster = {
    'group' : 'Restore Group',
    'cluster': 'wf-restored',
    'server': ['n2'],
    'ports': [ 26000, 26001, 26002 ],
    'rs-size': 3,  # NOTE: number of members in the replica set (per shard if sharded cluster)
    'rs-name': 'wf-restore',
    'shards': 0 }  # NOTE: shards 0 means plain replica set
