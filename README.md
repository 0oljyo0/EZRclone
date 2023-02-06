# EZRclone

替代raidrive，一个基于PyQt的rclone管理UI界面。

## 功能简介

- 开机自启动并最小化到系统托盘
- 配置挂载本地驱动器
- 启动后自动挂载

## 使用方法

### EZRclone打包exe

```cmd
pyinstaller -F -w tray.py
```
### 挂载驱动器
先下载rclone，通过rclone配置好远程参数和远程名称，在EZRclone中配置好rclone.exe路径、rclone.conf路径、挂载参数、开机自启动，重启电脑即可自动挂载所有设置好的盘符。

## Buy me a coffee
如果这个项目对您有所帮助，您可以通过下面的方式来支持我们的后续开发，谢谢。
- [Buy me a coffee](https://www.buymeacoffee.com/2542918484K)
- [爱发电](https://afdian.net/a/ezrclone)
