---
name: open_wechat
description: 打开 macOS 微信应用。当用户说"打开微信"、"启动微信"时使用此技能。
parameters:
  - name: app_name
    type: string
    description: 应用名称，默认为 "WeChat"
---

# 打开微信技能

## 触发条件
- 用户明确要求打开微信
- 用户说"我要用微信"、"帮我启动微信"

## 执行步骤
1. 调用 `ax_launch_app` 工具，参数 `app_name="WeChat"`
2. 等待应用启动（2-3 秒）
3. 如果应用已在运行，则调用 `ax_activate_app` 将其置于前台

## 错误处理
- 如果应用未安装：返回 "微信未安装，请先安装微信"
- 如果权限不足：提示用户授予辅助功能权限

## 输出格式
成功：返回 "微信已成功打开"
失败：返回具体错误信息