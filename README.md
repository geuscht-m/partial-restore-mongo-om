# 

## How it works

These scripts connect to a MongoDB queryable backup via the backup tunnel. The tunnel must already exist before the script is started.

The process will first create a temporary server or replica setn and restore the designated database or collection to this temporary target. After a successful restore to the temporary target, it will then drop the database or collection in the target cluster and restore from the temporary server/replica set to the target cluster.

## Preconditions

Before running the script, the following preconditions need to be met:

- The queryable backup needs to be up and running before the script is executed. I'd recommend testing the queryable backup first by connecting to it via the mongo shell before running the script.
- The Ops Manager group for the temporary instance(s) needs to exist and have running automation and monitoring agents. The script will exit with an error if these agents are not present.
-

## Configuration

All user relevant settings are in the file settings.py. The important settings are:

### opsMgrSettings - settings used to access Ops Manager
- serverUrl: Where to find the OM instance to talk to
- user: OM user to use for authentication. Needs to have appropriate privileges to be able to create new replica sets
- apiKey: OM api key for _user_

### queryableBackupSettings - defines how to connect to the queryable backup instance

- sourceCollection - name of the collection to pull the data from
- queryableProxy - address of the local end of the SSH tunnel that connects to the queryable backup
- dumpPath - path that mongodump can write the backup to
- dumpName - name of the backup to be written

### tempDestinationCluster - configuration of the cluster the backup temporarly is restored to

- group: OM group to create the temporary servers in
- cluster: name of the cluster to create
- targetCluster is an array containing the names of the servers and port numbers to be used to create the temporary restore target. If the array has a single element, the script will spin up a single standalone mongod, otherwise it will spin up a replica set.
- rs-name: Name of the temporary replica set, applied when the replica set is created
- shards: specify the number of shards, 0 signalling either a replica set or a standalone instance. _Reserved for future use, sharded cluster creation is currently not supported_.
- mongo-version: specifies the version of mongodb that Ops Manager uses for the intermediate replica set
- featureCompatibility: feature compatibility version used by the intermediate replica set. Needs to match or exceed the feature compatibility required by the source data

### restoreTargetCluster - defines the final target for the restore process
- dumpPath: Path to temporary storage for the dump taken from the temporary replica set/cluster
- dumpName: Name of the dump directory
- targetCluster: array containing a list of servers making up the replica set that is the target of the restore
- destCollection: Collection to restore to
- user: specifies the authenticated user for restore if authentication on the restoration target is enabled
- password: specifies the password for user authentication if authentication is enabled on the restoration target

## TODO

- Currently, the intermediate replica set needs to be removed manually and its storage directory deleted.
- Support additional authentication mechanisms
