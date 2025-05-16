# aws-sam-rayserver

在AWS上快速部署一个仅在使用时开启的XRay代理服务器

使用基础的VMess协议，没有反审查设计。
每次关闭服务器后都会重置IP因此没有被封IP的风险，满足个人日常使用。

# 部署说明

### 1. 使用 `git clone` 下载到本地

### 2. 打开 `app/get_handler.py` 修改允许访问的 uuid 列表
在网上随便找个uuid生成器。
不要把我的测试用的uuid留到生产环境。

### 3. 配置本地AWS-SAM-CLI环境
```
pip install aws-cli aws-sam-cli
```

### 4. 部署到 AWS
命令行执行
```
sam build
sam deploy --guide
```

在Deploy过程中，根据自身需求修改以下参数
- `Port` 连接的端口号，默认8080
- `InstanceTag` 任意字符串，区分不同项目
- `InstanceType` 检查**部署区域**提供的实例类型，实在没把握就填t2.nano
- `AmiId` 必须自行检查，在**部署区域**的[启动实例](https://ap-northeast-1.console.aws.amazon.com/ec2/home?#LaunchInstances:)页面选择AWS Linux，复制其AMI代码。

### 5. V2RayNG 订阅地址

```
Outputs                                                                                                                                                         
-----------------------------------------------------------------------------------
Key                 ProxyApiUrl                                                                                                                                 
Description         API Gateway endpoint URL for proxy GET request                                                                                              
Value               https://1234567890.execute-api.ap-northeast-1.amazonaws.com/Prod/proxy?uuid=de40bdf4-2861-45fd-bf9e-a073635cbcc2                            
-----------------------------------------------------------------------------------
```

如上所示的部署的输出栏中，Value的值就是你的V2RayNG订阅地址，将`uuid=`后的部分改成你的uuid。
