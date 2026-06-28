#!/bin/bash
# setup_permissions.sh
# macOS 辅助功能权限自动设置脚本
# 用于 MacAgent 项目 — 为终端应用授予辅助功能权限

set -e

# -------- 颜色定义 --------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -------- 辅助函数 --------
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# -------- 检测当前使用的终端应用 --------
detect_terminal_app() {
    local parent_pid=$PPID
    local parent_name=$(ps -p $parent_pid -o comm= 2>/dev/null | xargs basename 2>/dev/null)
    
    # 如果父进程是 zsh/bash，继续向上查找
    if [[ "$parent_name" == "zsh" || "$parent_name" == "bash" || "$parent_name" == "sh" ]]; then
        parent_pid=$(ps -p $parent_pid -o ppid= 2>/dev/null | xargs)
        parent_name=$(ps -p $parent_pid -o comm= 2>/dev/null | xargs basename 2>/dev/null)
    fi
    
    # 常见终端应用列表
    local terminals=(
        "Terminal"
        "iTerm2"
        "Visual Studio Code"
        "Code"
        "Cursor"
        "Warp"
        "Alacritty"
        "Hyper"
        "Kitty"
    )
    
    for term in "${terminals[@]}"; do
        if [[ "$parent_name" == "$term" ]] || [[ "$parent_name" == *"$term"* ]]; then
            echo "$term"
            return 0
        fi
    done
    
    # 如果无法自动检测，返回当前进程名
    echo "$(ps -p $$ -o comm= 2>/dev/null | xargs basename 2>/dev/null)"
    return 1
}

# -------- 获取应用的 Bundle ID --------
get_bundle_id() {
    local app_name="$1"
    local app_path=""
    
    case "$app_name" in
        "Terminal")
            app_path="/System/Applications/Utilities/Terminal.app"
            ;;
        "iTerm2")
            app_path="/Applications/iTerm.app"
            ;;
        "Visual Studio Code"|"Code")
            app_path="/Applications/Visual Studio Code.app"
            ;;
        "Cursor")
            app_path="/Applications/Cursor.app"
            ;;
        "Warp")
            app_path="/Applications/Warp.app"
            ;;
        *)
            # 尝试在 /Applications 中查找
            if [[ -d "/Applications/$app_name.app" ]]; then
                app_path="/Applications/$app_name.app"
            elif [[ -d "/System/Applications/Utilities/$app_name.app" ]]; then
                app_path="/System/Applications/Utilities/$app_name.app"
            fi
            ;;
    esac
    
    if [[ -n "$app_path" && -d "$app_path" ]]; then
        # 从 Info.plist 读取 Bundle ID
        local bundle_id=$(defaults read "$app_path/Contents/Info" CFBundleIdentifier 2>/dev/null)
        if [[ -n "$bundle_id" ]]; then
            echo "$bundle_id"
            return 0
        fi
    fi
    
    # 如果无法获取 Bundle ID，返回应用名（用于显示）
    echo "$app_name"
    return 1
}

# -------- 检查权限是否已授予 --------
check_permission() {
    local bundle_id="$1"
    
    # 使用 tccutil 检查权限（macOS 13.3+ 支持 list 命令）
    if tccutil list Accessibility 2>/dev/null | grep -q "$bundle_id"; then
        return 0
    fi
    
    # 备用检查：使用 sqlite3 直接查询 TCC 数据库（需要 SIP 部分禁用）
    local tcc_db="$HOME/Library/Application Support/com.apple.TCC/TCC.db"
    if [[ -f "$tcc_db" ]]; then
        local result=$(sqlite3 "$tcc_db" "SELECT 1 FROM access WHERE service='kTCCServiceAccessibility' AND client='$bundle_id' AND auth_value=2;" 2>/dev/null)
        if [[ "$result" == "1" ]]; then
            return 0
        fi
    fi
    
    return 1
}

# -------- 尝试自动添加权限（需要用户确认） --------
try_auto_add_permission() {
    local bundle_id="$1"
    local app_name="$2"
    
    print_info "尝试自动添加 $app_name 到辅助功能列表..."
    
    # 方法1: 使用 AppleScript 触发权限对话框
    osascript <<EOF
tell application "System Events"
    -- 尝试通过打开隐私面板来触发权限请求
    tell application "System Preferences"
        activate
        reveal pane id "com.apple.preference.security"
    end tell
end tell
EOF
    
    print_info "已打开系统设置 > 隐私与安全性"
    print_info "请手动找到 '辅助功能'，然后添加 $app_name"
    print_warning "自动添加权限需要 SIP 部分禁用，推荐手动操作"
    
    return 1
}

# -------- 显示手动操作指引 --------
show_manual_guide() {
    local app_name="$1"
    
    print_step "📋 手动操作指引"
    
    echo ""
    echo "请按以下步骤手动授予辅助功能权限："
    echo ""
    echo "  1. 打开 ${BLUE}系统设置${NC}"
    echo "  2. 点击 ${BLUE}隐私与安全性${NC}"
    echo "  3. 在右侧找到并点击 ${BLUE}辅助功能${NC}"
    echo "  4. 点击底部的 ${BLUE}+ 按钮${NC}"
    echo "  5. 在弹出窗口中找到并选择 ${BLUE}$app_name${NC}"
    echo "  6. 确保 $app_name 旁边的开关已 ${BLUE}开启${NC}"
    echo ""
    echo "  如果列表中已有 $app_name 但未勾选，直接勾选即可。"
    echo ""
    echo "  快捷方式："
    echo "  系统设置 → 隐私与安全性 → 辅助功能 → 点击 + 添加"
    echo ""
    
    print_info "添加完成后，请重新运行此脚本验证，或直接启动 MacAgent。"
}

# -------- 验证权限 --------
verify_permission() {
    local app_name="$1"
    local bundle_id="$2"
    
    print_step "🔍 验证权限"
    
    if check_permission "$bundle_id"; then
        print_success "✅ $app_name 已获得辅助功能权限！"
        return 0
    else
        print_error "❌ $app_name 尚未获得辅助功能权限"
        return 1
    fi
}

# -------- 主流程 --------
main() {
    print_step "🛠️  MacAgent 辅助功能权限设置"
    echo ""
    
    # 检测当前终端应用
    print_info "正在检测当前终端应用..."
    local app_name=$(detect_terminal_app)
    print_info "检测到终端应用: $app_name"
    
    # 获取 Bundle ID
    local bundle_id=$(get_bundle_id "$app_name")
    print_info "Bundle ID: $bundle_id"
    
    echo ""
    
    # 检查当前权限状态
    print_info "正在检查权限状态..."
    if check_permission "$bundle_id"; then
        print_success "✅ $app_name 已拥有辅助功能权限！"
        echo ""
        print_info "可以直接运行 MacAgent 了。"
        exit 0
    else
        print_warning "⚠️ $app_name 尚未拥有辅助功能权限"
    fi
    
    echo ""
    
    # 询问用户操作方式
    print_step "选择操作方式"
    echo ""
    echo "  1) 显示手动操作指引（推荐）"
    echo "  2) 尝试自动打开权限设置面板"
    echo "  3) 重置所有辅助功能权限（谨慎使用）"
    echo "  4) 退出"
    echo ""
    read -p "请选择 [1-4]: " choice
    
    case $choice in
        1)
            show_manual_guide "$app_name"
            ;;
        2)
            try_auto_add_permission "$bundle_id" "$app_name"
            show_manual_guide "$app_name"
            ;;
        3)
            print_warning "⚠️ 警告：此操作将重置所有应用的辅助功能权限"
            read -p "确认继续？(y/N): " confirm
            if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
                print_info "正在重置辅助功能权限..."
                sudo tccutil reset Accessibility
                print_info "权限已重置，请重新启动应用并授权。"
                show_manual_guide "$app_name"
            else
                print_info "已取消"
            fi
            ;;
        4)
            print_info "退出"
            exit 0
            ;;
        *)
            print_error "无效选项"
            exit 1
            ;;
    esac
    
    echo ""
    print_info "设置完成后，请重新运行此脚本验证权限。"
}

# -------- 执行主流程 --------
main "$@"