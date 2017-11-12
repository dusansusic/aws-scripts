# Documentation
As of majority cases, documentation is poor or missing.

## Requirements:
- In order to get it working, EC2 should be tagged with **backupEnabled** tag which has value **yes** || **Yes** || **YES**
- retention tag should have integer value how long backups are preserved

- Create IAM policy and attach policy to Role. Policy must have next values:
 -  describe_instances
 -  create_snapshot
 -  create_tags
 -  describe_snapshots
 -  delete_snapshot

### Create Lambda:
- pick Author from scratch on right upper side
- give it a name
- and choose previously created role
- select Python 2.7 interpreter and paste ebsSnapshot.py content.
Please, copy it from RAW page to be sure you will not have issues with execution.
- increase timeout to 3 mins
- add environment variables
 - name: region
 - value: eg. us-east-1
 - only for ebsCleanup function add **account_id** environment variable with account id of your account
- click on Triggers
- add new trigger clicking on CloudWatch Events
- select schedule and set up cron expression, eg. 0 12 * * ? *


Repeat the process for deleting snapshots with DeleteOn flag.

### Note:

Additionally, you can set SNS to send notification whenever Lambda reported an error.
With CloudWatch you can create dashboard with Invocations, Duration, Throttles and Errors.
