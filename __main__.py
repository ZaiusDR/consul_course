import json

import pulumi
import pulumi_aws
import pulumi_aws.iam

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
            protocol='tcp', from_port=22, to_port=22, cidr_blocks=['139.47.112.75/32']
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp', from_port=8500, to_port=8500, cidr_blocks=['139.47.112.75/32']
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp', from_port=8600, to_port=8600, cidr_blocks=[vpc.cidr_block]
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='udp', from_port=8600, to_port=8600, cidr_blocks=[vpc.cidr_block]
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp', from_port=8500, to_port=8500, cidr_blocks=[vpc.cidr_block]
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp', from_port=8301, to_port=8301, cidr_blocks=[vpc.cidr_block]
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='udp', from_port=8301, to_port=8301, cidr_blocks=[vpc.cidr_block]
        ),
        pulumi_aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp', from_port=8300, to_port=8300, cidr_blocks=[vpc.cidr_block]
        )
    ],
    egress=[
        pulumi_aws.ec2.SecurityGroupEgressArgs(
            protocol='all', from_port=0, to_port=65535, cidr_blocks=['0.0.0.0/0']
        )
    ]
)

instance_profile_role = pulumi_aws.iam.Role(
    'consul',
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Sid": "",
            "Principal": {
                "Service": "ec2.amazonaws.com",
            },
        }],
    }),
    inline_policies=[
        pulumi_aws.iam.RoleInlinePolicyArgs(
            name="consul-server-describe-instances",
            policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": ["ec2:DescribeInstances"],
                    "Effect": "Allow",
                    "Resource": "*",
                }],
            })
        )
    ]
)

instance_profile = pulumi_aws.iam.InstanceProfile(
    'consul-server',
    role=instance_profile_role.name
)

with open('./cloud-init/server-agent.yml') as f:
    user_data = f.read()


for i in range(1, 4):
    consul_server = pulumi_aws.ec2.Instance(
        f'consul-server-{i}',
        instance_type='t2.micro',
        ami=aws_ami.id,
        key_name='aws-keypair',
        vpc_security_group_ids=[
            consul_server_sg.id
        ],
        tags={
            'Name': f'consul-server-{i}',
            'Consul': 'consul-server'
        },
        user_data=user_data,
        iam_instance_profile=instance_profile.name
    )
