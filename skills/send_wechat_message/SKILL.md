---
name: send_wechat_message
description: 在 macOS 微信中向指定联系人发送消息。当用户说"给XXX发消息"、"告诉XXX"、"发微信给XXX"时使用此技能。
parameters:
  - name: contact
    type: string
    description: 联系人的微信昵称或备注名
  - name: message
    type: string
    description: 要发送的消息内容
output: 返回发送成功或失败的信息
---

# 微信发送消息技能

## 触发条件
- 用户明确要求发送微信消息
- 用户说"给XX发消息"、"告诉XX"、"发微信给XX"
- 用户提供联系人名称和消息内容

## 前置条件
- 微信应用已打开并处于登录状态
- 联系人已在通讯录中

## 执行步骤
1. **激活微信**：如果微信未在前台，调用 `ax_activate_app` 将微信置于前台
2. **打开搜索框**：使用 `ax_click` 点击搜索框（快捷键 `Cmd+F` 或 `Ctrl+F`）
3. **输入联系人**：使用 `ax_type` 输入联系人名称，等待下拉列表出现
4. **选择联系人**：使用 `ax_click` 点击匹配的联系人（如有多条，选择第一个）
5. **输入消息**：在输入框中键入消息内容
6. **发送消息**：按下 `Enter` 键发送

## 错误处理
- 如果微信未运行 → 先调用 `open_wechat` 技能启动微信
- 如果联系人未找到 → 返回 "未找到联系人 XXX，请确认昵称是否正确"
- 如果消息内容为空 → 返回 "消息内容不能为空"

## 输出格式
成功：返回 "消息已发送给 XXX：<消息内容>"
失败：返回具体错误信息

## 依赖工具
- ax_activate_app
- ax_click
- ax_type
- ax_press_key
- ax_find_element