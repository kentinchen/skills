#!/bin/bash

# ============================================
# Local Cloud Token Management Library
# 研发云本地Token和AgentId统一管理工具库
# ============================================

# 缓存变量
__LOCAL_TOKEN=$DEV_USER_API_TOKEN
__LOCAL_AGENT_ID=$DEV_USER_AGENT

# 如果Token不为空，去掉Bearer
if [ -n "$__LOCAL_TOKEN" ]; then
    __LOCAL_TOKEN="${__LOCAL_TOKEN#Bearer }"
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 个人电脑首次加载时检查用户环境变量中是否配置了DEV_USER_API_TOKEN 和 DEV_USER_AGENT
check_user_env_config() {
    if [ -z "$__LOCAL_AGENT_ID" ] && [ -z "$__LOCAL_TOKEN" ]; then
        echo -e "${RED}错误: 运行Skill前，请先在本地配置两组环境变量\r\n- 第一组： Key为DEV_USER_AGENT，值为您的工号。\r\n- 第二组：Key为DEV_USER_API_TOKEN，值为您在研发云“开放API”平台上申请的Token\r\n[点我查看](https://docs.iwhalecloud.com/doi/nk4/prod-intro/fea-func/sr8vryPG)配置完后需重启客户端${NC}" >&2
        return 1
    elif [ -z "$__LOCAL_AGENT_ID" ]; then
        echo -e "${RED}错误: 未找到 AgentId，请在本地配置Key为DEV_USER_AGENT的环境变量，值为您的工号。${NC}" >&2
        return 1
    elif [ -z "$__LOCAL_TOKEN" ]; then
        echo -e "${RED}错误: 未找到研发云Api Token，请在本地配置Key为DEV_USER_API_TOKEN的环境变量，值为您在研发云“开放API”平台上申请的Token${NC}" >&2
        return 1
    fi
	
	return 0
	
}

# 获取系统环境变量中读取用户agentId
# 返回值：echo 输出 agentId，成功返回0，失败返回1
get_agent_id() {
    if [ -z "$__LOCAL_AGENT_ID" ]; then
        echo -e "${RED}错误: 未找到 AgentId，请在本地配置Key为DEV_USER_AGENT的环境变量，值为您的工号。${NC}" >&2
        return 1
	fi
    echo "$__LOCAL_AGENT_ID"
    return 0
}

# 仅获取Token（不做AgentId校验）
# 返回值：echo输出token，成功返回0，失败返回1
get_cloud_token_only() {
    if [ -z "$__LOCAL_TOKEN" ]; then
        echo -e "${RED}错误: 未找到研发云Api Token，请在本地配置Key为DEV_USER_API_TOKEN的环境变量，值为您在研发云“开放API”平台上申请的Token${NC}" >&2
        return 1
    fi

    # [修复] 修正了变量名，从 __CACHED_TOKEN 改为 __LOCAL_TOKEN
    echo "$__LOCAL_TOKEN"
    return 0
}

# 获取环境变量中的Token（包含身份完整性校验）
# 逻辑：先检查 AgentId 是否存在，确保身份完整，再返回 Token
# 返回值：echo输出token，成功返回0，失败返回1
get_cloud_token() {
    # [修复] 先调用 get_agent_id 检查身份，如果失败则直接返回错误
    if ! get_agent_id > /dev/null 2>&1; then
        # 错误信息已在 get_agent_id 中打印，这里直接返回错误码
        return 1
    fi

    # 身份验证通过，输出 Token
    echo "$__LOCAL_TOKEN"
    return 0
}

# 用户配置Token，暂不考虑，只支持从环境变量中读取
user_config() {
    echo "当前版本仅支持从环境变量读取配置。" >&2
    return 0
}
