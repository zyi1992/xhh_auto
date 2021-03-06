### 本项目仅供学习使用，并遵循GPL v3.0协议

## **小黑盒使用JNI加密了Hkey的计算方法，本脚本暂未适配**
## 如果脚本提示"[参数错误]"，请将`heybox_client.py`最后一行改成`pass`临时解决

#### 当前最新版本`v0.69`
#### 欢迎加入官方群: `916945024`

## 安装方法
1. 从[releases](https://github.com/chr233/xhh_auto/releases)下载最新的脚本
1. 解压,并切换到脚本所在目录
1. 打开`accounts_sample.json`,填入自己的账号凭据,保存为`accounts.json`
1. 打开`settings_sample.json`,填入FtqqSKEY[获取地址](http://sc.ftqq.com/)(可选,用于发送统计信息到微信)
1. Linux用户按`Ctrl+Alt+T`打开终端,Windows用户按住`Shift`在目录背景按右键->`在此打开命令行`
1. 执行`pip install -r ./requirements.txt`
 * Linux用户记得先赋予脚本执行权限`chmod 755 *.py`

## 凭据获取方法
* **[安卓手机端抓取教程](https://blog.chrxw.com/archives/2019/10/19/390.html)**【推荐】
* **[Fiddler抓取教程](https://blog.chrxw.com/archives/2019/10/20/437.html)**

* 抓取小黑盒数据后，填入accounts.json即可使用本脚本。

## 使用方法
1. Linux用户按`Ctrl+Alt+T`打开终端,Windows用户按住`Shift`在目录背景按右键->`在此打开命令行`
1. 执行`python3 ./start.py`


PS:本脚本支持多账户,将json配置成下面这样即可(请注意格式)

account.json:
```json
{
  "accounts": [
    {
      "pkey": "第一个账号的pkey",
      "imei": "第一个账号的imei",
      "heybox_id": "第一个账号的数字ID"
    },
    {
      "pkey": "第二个账号的pkey",
      "imei": "第二个账号的imei",
      "heybox_id": "第二个账号的ID"
    }
  ]
}
```

PS:settings.json注释

settings.json:
```json
{
  "CfgVer": "1",//配置版本,无需关心
  "Debug": false,//是否开启调试模式,如果不知道在做什么请不要更改
  "UpdateCheck": true,//是否允许脚本检查更新,设置为false禁用,**不建议禁用**
  "EnableFtqq": true,//是否启用方糖微信推送功能,设置为false关闭该功能
  "FtqqSKEY": null//方糖的SKEY[获取地址](http://sc.ftqq.com/),填写的时候记得在Skey外侧加双引号("FtqqSKEY": "你的SKEY")
}
```

## TODO LIST
- [ ] 简单好用的账户管理器
- [ ] 支持直接登陆小黑盒账号
- [ ] 实现小黑盒客户端的大部分功能
- [ ] ~~自动参加ROLL房~~
 * 受steam影响，小黑盒貌似开始转卖点卡了。对2和4的支持计划延后
