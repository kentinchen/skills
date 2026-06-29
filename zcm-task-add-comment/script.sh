#!/bin/bash

# ============================================
# 研发云单子添加评论
# 用法: bash script.sh <taskNo> <comment>
# ============================================

set -e

# 加载Token管理工具库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 获取操作系统内核类型
OS_TYPE=$(uname -s)

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || -n "$MSYSTEM" || "$OS" == "Windows_NT" || "$OSTYPE" == "darwin"* ]]; then
    # 注意: macOS 的 OSTYPE 通常是 "darwin18", "darwin19" 等，所以用 "darwin"* 通配
    echo "当前为个人电脑，从skill当前目录加载local-skill-config.sh工具库" >&2

    # 配置文件的完整路径
    LOCAL_CONFIG="${SCRIPT_DIR}/local-skill-config.sh"

    # 检查skills的加载目录下有没有脚本
    if [ -f "$LOCAL_CONFIG" ]; then
        source "$LOCAL_CONFIG"

        # 检查环境变量是否有配置
        if ! check_user_env_config; then
            exit 1
        fi

    # 如果配置文件不存在，提醒用户重新安装
    else
        echo "错误: 本地的skills目录未找到local-skill-config.sh工具库，请重新安装该技能" >&2
        exit 1
    fi

else
    echo "非个人电脑，从Token管理工具库中加载config.sh工具库" >&2
    if [ -f "/cloud-utils/config.sh" ]; then
        source "/cloud-utils/config.sh"
    elif [ -f "/workspace/.config/cloud-utils/config.sh" ]; then
        source "/workspace/.config/cloud-utils/config.sh"
    else
        echo "错误: 未找到config.sh工具库" >&2
        exit 1
    fi
fi






# API 配置
API_BASE="https://dev.iwhalecloud.com/portal/ai-gateway/devspace/rpc/v3"
CANARY_PARAM="?zcm-feature-canary=true"

# 检查参数
if [ $# -lt 2 ]; then
    echo "错误: 参数不足" >&2
    echo "用法: bash script.sh <taskNo> <comment>" >&2
    echo "示例: bash script.sh 51856683 这是评论" >&2
    exit 1
fi

TASK_NO="$1"
COMMENT="$2"
CURRENT_AGENT=$(get_agent_id)
if [ $? -ne 0 ]; then
    exit 1
fi

# 获取研发云Token
access_token=$(get_cloud_token_only)
if [ $? -ne 0 ]; then
    exit 1
fi

echo "正在为 ${TASK_NO} 添加评论 ${COMMENT}..."

# 调用tool
RESPONSE=$(jq -n --arg comments "$COMMENT" '{"comments": $comments}' | \
    curl -s -X POST \
    "${API_BASE}/task/task-no/${TASK_NO}/comment${CANARY_PARAM}" \
    -H "Authorization: Bearer ${access_token}" \
    -H "X-Operate-User-Code: ${CURRENT_AGENT}" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary @-)

# 检查响应
if echo "$RESPONSE" | jq empty 2>/dev/null; then
    CODE=$(echo "$RESPONSE" | jq -r '.code // empty')
    MSG=$(echo "$RESPONSE" | jq -r '.message // .msg // empty')
    HTTP_STATUS=$(echo "$RESPONSE" | jq -r '.status // empty')

    if [ -n "$HTTP_STATUS" ] && [ "$HTTP_STATUS" != "200" ]; then
        echo "❌ 添加评论失败：HTTP $HTTP_STATUS" >&2
        echo "错误信息：${MSG:-未知错误}" >&2
        echo "完整响应：" >&2
        echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE" >&2
        exit 1
    fi

    if [ -n "$CODE" ] && [ "$CODE" != "9999" ]; then
        echo "❌ 添加评论失败" >&2
        echo "API 错误码：$CODE" >&2
        echo "错误信息：${MSG:-无}" >&2
        echo "完整响应：" >&2
        echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE" >&2
        exit 1
    fi


    echo "✅ 添加评论成功" >&2

else
    echo "❌ 添加评论失败：响应不是有效的 JSON 格式" >&2
    echo "原始响应：" >&2
    echo "$RESPONSE" >&2
    exit 1
fi