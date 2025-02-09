# AstrBot 图像标签识别插件

## 简介
这是一个基于AstrBot的图像标签识别插件，可以帮助你识别图片并生成AI绘画标签。插件使用了SmilingWolf开发的wd-tagger-v3模型，能够准确识别图像中的各种元素。

## 如何使用
1. 发送 `/tag` 命令
2. 在60秒内发送一张想要分析的图片
3. 机器人会返回识别出的标签列表

## 主要特点
- 支持多种图片格式（PNG、JPG等）
- 采用高质量的wd-tagger-v3模型
- 快速准确的标签识别能力
- 支持QQ平台的图片识别

## 安装说明
1. 下载插件并解压
2. 将插件文件夹放入AstrBot的plugins目录
3. 重启机器人即可使用

## 环境要求
- AstrBot v0.1.5.4或更高版本
- Python 3.7+
- aiohttp库（用于网络请求）

## 关于作者
- 作者：yudengghost
- 项目地址：https://github.com/yudengghost/astrbot_plugin_tagger
- 问题反馈：如有问题请在GitHub提交issue

## 更新日志
### v1.0 (2025-02-09)
- 首次发布
- 实现基础的图像标签识别功能
- 支持QQ平台图片识别
- 添加中文交互界面
