import os
import json
import boto3
import base64
from datetime import datetime, timezone

# 允许访问的 uuid 列表（示例中用两个 uuid）
ALLOWED_UUIDS = {
    "de40bdf4-2861-45fd-bf9e-a073635cbcc2",
    "218f1266-1cb5-4936-8ebe-f05f5ac6b526",
}

# 从环境变量获取配置
INSTANCE_TAG = os.environ.get("INSTANCE_TAG", "MyProxyTag")
AMI_ID = os.environ.get("AMI_ID", "ami-05206bf8aecfc7ae6")
INSTANCE_TYPE = os.environ.get("INSTANCE_TYPE", "t2.micro")
SECURITY_GROUP_ID = os.environ.get("SECURITY_GROUP_ID", "")
PROXY_PORT = os.environ.get("PROXY_PORT", "8080")

EC2_STATE_MAP = {
    'pending': '正在启动',
    'running': '运行中',
    'shutting-down': '正在关闭',
    'stopped': '已停止',
    'terminated': '已终止'
}

VMESSDATA = {
    'v': '2',
    'ps': 'UNKNOWN',
    'add': '0.0.0.0',
    'port': '80',
    'id': '00000000-0000-0000-0000-000000000000',
    'aid': '0',
    'net': 'tcp',
    'scy': 'auto',
    'alpn': '',
    'fp': '',
    'host': '',
    'path': '',
    'sni': '',
    'tls': '',
    'type': 'none',
}

def base64_encode(string:str):
    return base64.b64encode(string.encode()).decode()

def create_server(ec2_client):
    """
    启动新的 EC2 实例，并在用户数据中加入获取实例信息的命令。
    """
    with open("./userdata.sh") as f:
        user_data_template = f.read()
    with open("./config.json") as f:
        config = json.load(f)
    config["inbounds"][0]["port"] = int(PROXY_PORT)
    config["inbounds"][0]["settings"] = [{'clients': [{'id': uuid}]} for uuid in ALLOWED_UUIDS]
    user_data = base64.b64encode(user_data_template.format(json.dumps(config)))

    try:
        response = ec2_client.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            UserData=user_data,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'ProxyService',
                            'Value': INSTANCE_TAG
                        },
                    ]
                },
            ],
            NetworkInterfaces=[
                {
                    "DeviceIndex": 0,
                    "AssociatePublicIpAddress": True,
                    "Groups": [SECURITY_GROUP_ID]
                }
            ]
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Launched new instance: {instance_id}")
    except Exception as e:
        print(f"Error launching instance: {str(e)}")

def lambda_handler(event, context):
    print("Received event:", event)
    query_params = event.get("queryStringParameters") or {}
    user_uuid = query_params.get("uuid")

    # 用户身份验证
    if user_uuid not in ALLOWED_UUIDS:
        return {
            "statusCode": 403,
        }
    
    # 检查运行中的服务
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': [TAGNAME]}])

    # 无可用服务时开启新服务
    if not [i for i in instances if i.state['Name'] != 'terminated']:
        create_server()

    # 生成地址
    vmess_list = []
    for instance in instances:
        vmess = VMESSDATA.copy()
        vmess['ps'] = EC2_STATE_MAP.get(instance.state['Name'], instance.state['Name']) + ' ' + instance.id
        vmess['port'] = PROXY_PORT
        vmess['id'] = user_uuid
        if instance.public_ip_address:
            vmess['add'] = instance.public_ip_address
        vmess_list.append(vmess)

    # 无可用地址时
    if not vmess_list:
        vmess = VMESSDATA.copy()
        vmess['ps'] = '无可用节点'
        vmess_list = [vmess]

    # 组织输出
    vmess_link_list = []
    for vmess in vmess_list:
        vmess_link = 'vmess://' + base64_encode(json.dumps(vmess))
        vmess_link_list.append(vmess_link)
    response = base64_encode('\n'.join(vmess_link_list))

    return {
        "statusCode": 200,
        "body": response
    }
