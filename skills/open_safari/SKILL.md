---
name: open_safari
description: 打开 macOS Safari 浏览器，可指定访问某个网址。当用户说"打开Safari"、"打开浏览器"、"打开网页"时使用此技能。
parameters:
  - name: url
    type: string
    description: 要访问的网址，如 "https://www.baidu.com"。如果不提供，则只打开 Safari 空白页。
output: 返回 Safari 启动状态和访问的网址
---

# 打开 Safari 浏览器技能

## 触发条件
- 用户明确要求打开 Safari 或浏览器
- 用户说"打开网页"、"访问XXX"
- 用户提到需要浏览网页

## 执行步骤
1. **启动 Safari**：调用 `ax_launch_app`，参数 `app_name="Safari"`
2. **等待窗口加载**：等待 2-3 秒，确保 Safari 窗口已显示
3. **处理新标签页**（可选）：
   - 如果 Safari 已运行，调用 `ax_click` 点击「新建标签页」按钮
   - 或使用快捷键 `Cmd+T` 打开新标签
4. **输入网址**（如果用户提供了 URL）：
   - 使用 `ax_click` 点击地址栏
   - 使用 `ax_type` 输入网址
   - 按下 `Enter` 导航

## 错误处理
- 如果 Safari 未安装 → 返回 "Safari 未安装，请检查系统"
- 如果网址无效 → 返回 "网址格式不正确，请提供有效 URL"
- 如果网络不可用 → 返回 "网络连接不可用，请检查网络设置"

## 输出格式
成功：返回 "Safari 已启动" 或 "Safari 已打开并访问 <网址>"
失败：返回具体错误信息

## 依赖工具
- ax_launch_app
- ax_activate_app
- ax_click
- ax_type
- ax_press_key