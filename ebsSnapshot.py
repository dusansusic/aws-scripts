import boto3
import collections
import datetime
import json
import itertools

region = 'us-east-1'

def lambda_handler(event, context):

    ec = boto3.client('ec2', region_name=region)
    reservations = ec.describe_instances(
        Filters=[
            {
                'Name': 'tag:backupEnabled',
                'Values': ['yes', 'Yes', 'YES']
            }
        ]
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print "Found %d instances that need backing up in region %s" % (len(instances), region)

    to_tag_retention = collections.defaultdict(list)
    to_tag_mount_point = collections.defaultdict(list)

    for instance in instances:
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Retention'][0]
        except IndexError:
            retention_days = 7

        try:
            skip_volumes = [
                str(t.get('Value')).split(',') for t in instance['Tags']
                if t['Key'] == 'Skip_Backup_Volumes']
        except Exception:
            pass

        from itertools import chain
        skip_volumes_list = list(chain.from_iterable(skip_volumes))

        instance_name = [str(name.get('Value')) for name in instance['Tags']
                         if name['Key'] == 'Name'][0]
        print(instance_name)

        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            vol_id = dev['Ebs']['VolumeId']
            if vol_id in skip_volumes_list:
                print "Volume %s is set to be skipped, not backing up" % (vol_id)
                continue
            dev_attachment = dev['DeviceName']
            print "Found EBS volume %s on instance %s attached to %s" % (
                vol_id, instance['InstanceId'], dev_attachment)

            creation_time = datetime.datetime.now()
            creation_time_fmt = creation_time.strftime("%Y-%m-%d__%H-%M")

            snap = ec.create_snapshot(
                VolumeId=vol_id,
                Description=instance['InstanceId'],
                DryRun=False
            )

            to_tag_retention[retention_days].append(snap['SnapshotId'])
            to_tag_mount_point[vol_id].append(snap['SnapshotId'])

            print "Retaining snapshot %s of volume %s from instance %s for %d days" % (
                snap['SnapshotId'],
                vol_id,
                instance['InstanceId'],
                retention_days,
            )

            ec.create_tags(
                Resources=to_tag_mount_point[vol_id],
                DryRun=False,
                Tags=[
                    {'Key': 'Name', 'Value': dev_attachment + " of " + instance_name + " @ " + creation_time_fmt},
                ]
            )

    for retention_days in to_tag_retention.keys():
        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%Y-%m-%d')
        print "Will delete %d snapshots on %s" % (len(to_tag_retention[retention_days]), delete_fmt)
        ec.create_tags(
            Resources=to_tag_retention[retention_days],
            Tags=[
                {'Key': 'DeleteOn', 'Value': delete_fmt},
            ]
        )