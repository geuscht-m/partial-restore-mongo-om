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
opsmgrApiKey = '8fcedbc9-bf61-45fd-a145-e890c4b943e4'
opsmgrWebHookReturnValue = '{"ok": true}' # Value OpsMgr want to see returned from the webhook if all went well
opsmgrDefaultGroup = 'wf-test' # If O/M group is not provided in chat, we will use this one

# Queryable Backup settings
restoreCollection = 'testdb.testcoll'
queryableProxy    = 'localhost:29000'
queryableDumpPath = '/Users/timo/tmp'
queryableDumpName = 'db.dump'

sourceCluster = {
    'group' : 'Initial Group'
    }

destinationCluster = {
    'group' : 'Restore Group',
    'cluster': 'wf-restore',
    'server': ['r1', 'r1', 'r1'],
    'ports': [ 28000, 28001, 28002 ],
    'rs-size': 3,  # NOTE: number of members in the replica set (per shard if sharded cluster)
    'rs-name': 'wf-restore',
    'shards': 0,   # NOTE: shards 0 means plain replica set
    'protocolVersion': 1
}
