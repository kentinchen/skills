#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 设置变量
DOWNLOAD_URL="https://dc.iwhalecloud.com/api/skillMarket/skill/107/download?jobnum=113100&version=1.0"
ZIP_FILE="zcm-translator.zip"
TARGET_DIR="../../skills"
SKILL_DIR="$TARGET_DIR/zcm-translator"

# 需要检查的文件列表
CHECK_FILES=(
    "$SKILL_DIR/SKILL.md"
    "$SKILL_DIR/scripts/common.sh"
    "$SKILL_DIR/scripts/translate.sh"
)

# 检查目录和文件是否都存在
echo "=== 检查 zcm-translator 是否已安装 ===" >&2

# 先检查目录是否存在
if [[ ! -d "$SKILL_DIR" ]]; then
    echo "✗ 目录不存在: $SKILL_DIR" >&2
    echo "需要重新下载安装" >&2
    NEED_DOWNLOAD=true
else
    echo "✓ 目录存在: $SKILL_DIR" >&2
    
    # 检查所有必需文件
    NEED_DOWNLOAD=false
    for file in "${CHECK_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo "✗ 文件不存在: $file" >&2
            NEED_DOWNLOAD=true
        else
            echo "✓ 文件存在: $file" >&2
        fi
    done
fi

# 如果所有文件都存在，直接退出
if [[ "$NEED_DOWNLOAD" != "true" ]]; then
    echo "" >&2
    echo "=== zcm-translator 已完整安装，无需下载 ===" >&2
    exit 0
fi

echo "" >&2
echo "=== 开始下载研发云术语翻译服务 ===" >&2

# 创建目标目录（如果不存在）
mkdir -p "$TARGET_DIR"

# 使用 curl 下载文件
# -L: 跟随重定向
# -o: 指定输出文件名
# -f: 下载失败时返回非零退出码
# --progress-bar: 显示进度条
if curl -L -f -o "$ZIP_FILE" "$DOWNLOAD_URL"; then
    echo "✓ 下载成功: $ZIP_FILE" >&2
else
    echo "✗ 下载失败" >&2
    exit 1
fi

echo "" >&2
echo "=== 开始解压文件 ===" >&2

# 解压到目标目录（覆盖已有文件）
if unzip -o "$ZIP_FILE" -d "$TARGET_DIR"; then
    echo "✓ 解压成功到: $TARGET_DIR" >&2
else
    echo "✗ 解压失败" >&2
    rm -f "$ZIP_FILE"
    exit 1
fi

echo "" >&2
echo "=== 清理临时文件 ===" >&2
rm -f "$ZIP_FILE"
echo "✓ 已删除: $ZIP_FILE" >&2

echo "" >&2
echo "=== 完成 ===" >&2
ls -la "$SKILL_DIR"
