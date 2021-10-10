"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws

aws_ami = pulumi_aws.ec2.get_ami(
    owners=['amazon'],
    most_recent=True,
    filters=[pulumi_aws.ec2.GetAmiFilterArgs(
        name='name',
        values=['amzn2-ami-hvm-2.0.????????-x86_64-gp2'],
    )],
)

vpc = pulumi_aws.ec2.Vpc.get(id='vpc-f4c2ec92', resource_name='default')

consul_server_sg = pulumi_aws.ec2.SecurityGroup(
    'consul-server',
    description='Consul Servers Security Group',
    ingress=[
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp', from_port=8200, to_port=8200, cidr_blocks=[vpc.cidr_block]
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp', from_port=8500, to_port=8500, cidr_blocks=[vpc.cidr_block]
        )
    ]
)

consul_server = pulumi_aws.ec2.Instance(
    'consul-server',
    instance_type='t2.micro',
    ami=aws_ami.id,
    key_name='aws-keypair',
    vpc_security_group_ids=[
        consul_server_sg.id
    ]
)
