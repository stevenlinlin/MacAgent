---
name: control_volume
description: 调节 macOS 系统音量。支持“调高”、“调低”、“静音”、“设为 X%”等操作。
parameters:
  - name: action
    type: string
    description: 操作类型，可选值：'up'（调高）、'down'（调低）、'mute'（静音）、'set'（设置为指定值）
  - name: value
    type: integer
    description: 当 action 为 'set' 时的目标音量值（0-100），其他操作忽略此参数
output: 返回调节结果信息
---

# 音量调节技能

## 触发条件
- 用户要求调节音量，例如“音量调高”、“把音量调到 50%”、“静音”、“音量调小”
- 用户提及音量相关词汇

## 执行步骤
1. 解析用户指令，提取操作类型（up/down/mute/set）和目标值（如有）
2. 调用 MCP 工具 `volume_control`，传入 action 和 value
3. 返回操作结果

## 错误处理
- 如果音量值超出 0-100 范围：返回 “音量值必须在 0 到 100 之间”
- 如果系统音频服务异常：返回 “调节失败，请检查系统设置”

## 输出格式
成功：返回 “音量已调高” 或 “音量已设为 X%”
失败：返回具体错误信息