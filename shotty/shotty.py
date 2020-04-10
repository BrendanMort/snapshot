import boto3
import botocore
import click

def start_session(profile = 'shotty'):
    session = boto3.Session(profile_name = profile)
    ec2 = session.resource('ec2')
    return ec2

def filter_instances(ec2, project):
    instances = []

    if project:
        filters = [{'Name':'tag:Project','Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
@click.option('--profile', default = 'shotty',
    help="Select a profile for shotty to use")

@click.pass_context
def cli(ctx, profile):
    """Shotty manages snapshots"""
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile


@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project',default=None,
    help="Only snapshots for project (tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all snapshots for each volume, not just the most recent")
@click.pass_context
def list_snapshots(ctx, project, list_all):
    "List EC2 snapshots"

    ec2 = start_session(ctx.obj["PROFILE"])
    instances = filter_instances(ec2, project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(" , ".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

                if s.state == 'completed' and not list_all: break

    return

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project',default=None,
    help="Only volumes for project (tag Project:<name>)")
@click.pass_context
def list_volumes(ctx, project):
    "List EC2 volumes"

    ec2 = start_session(ctx.obj["PROFILE"])
    instances = filter_instances(ec2, project)

    for i in instances:
        for v in i.volumes.all():
            print(" , ".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))

    return

@cli.group()
def instances():
    """Commands for instances"""
@instances.command('snapshot',
    help="Create snapshots of all volumes")
@click.option('--project',default=None,
    help="Only instances for project (tag Project:<name>)")
@click.option('--force',is_flag=True,
    help="All instances")
@click.pass_context
def create_snapshots(ctx, project,force):
    "Create snapshots for EC2 instances"

    ec2 = start_session(ctx.obj["PROFILE"])
    instances = filter_instances(ec2, project)

    if project or force:
        for i in instances:
            print("Stopping {0}...".format(i.id))
            try:
                i.stop()
                i.wait_until_stopped()

                for v in i.volumes.all():
                    if has_pending_snapshot(v):
                        print(" Skipping {0}, snapshot already in progress".format(v.id))
                        continue
                    print("  Creating snapshot of {0}".format(v.id))
                    v.create_snapshot(Description="Created by Shotty")

                print("Starting {0}...".format(i.id))
                i.start()
                i.wait_until_running()

                print("Job's done!")

            except botocore.exceptions.ClientError as e:
                print(" Could not create snapshot for {0}.".format(i.id) + str(e))
                continue
    else:
        print("This command requires a project name. For more info refer to --help")

    return

@instances.command('list')
@click.option('--project',default=None,
    help="Only instances for project (tag Project:<name>)")
@click.pass_context
def list_instances(ctx, project):
    "List EC2 instances"

    ec2 = start_session(ctx.obj["PROFILE"])
    instances = filter_instances(ec2, project)

    if project:
        filters = [{'Name':'tag:Project','Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        print(' , '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
            )))

    return

@instances.command('stop')
@click.option("--project", default=None,
    help="Only instances for project")
@click.option("--force", is_flag=True,
        help="Forces all instance start")
@click.pass_context
def  stop_instances(ctx, project,force):
    "Stop EC2 Instances"

    ec2 = start_session(ctx.obj["PROFILE"])
    instances = filter_instances(ec2, project)

    if project or force:
        for i in instances:
            print("stopping {0}...".format(i.id))
            try:
                i.stop()
            except botocore.exceptions.ClientError as e:
                print(" Could not stop {0}.".format(i.id) + str(e))
                continue
    else:
        print("This command requires a project name. For more info refer to --help")

    return

@instances.command('start')
@click.option("--project", default=None,
    help="Only instances for project")
@click.option("--force", is_flag=True,
    help="Forces all instance start")
@click.pass_context
def start_instances(ctx, project, force):
    "Start EC2 Instances"

    ec2 = start_session(ctx.obj["PROFILE"])
    instances = filter_instances(ec2, project)

    if project or force:
        for i in instances:
            print("starting {0}...".format(i.id))
            try:
                i.start()
            except botocore.exceptions.ClientError as e:
                print(" Could not start {0}.".format(i.id) + str(e))
                continue
    else:
        print("This command requires a project name. For more info refer to --help")

    return

@instances.command('reboot')
@click.option("--project", default=None,
    help="Only instances for project")
@click.option("--force", is_flag=True,
    help="Forces all instance reboot")
@click.pass_context
def reboot_instances(ctx, project, force):
    "Reboot EC2 Instances"

    ec2 = start_session(ctx.obj["PROFILE"])
    instances = filter_instances(ec2, project)

    if project or force:
        for i in instances:
            print("rebooting {0}...".format(i.id))
            try:
                i.reboot()
            except botocore.exceptions.ClientError as e:
                print(" Could not reboot {0}.".format(i.id) + str(e))
                continue
    else:
        print("This command requires a project name. For more info refer to --help")

    return

if __name__ == '__main__':
    cli()
