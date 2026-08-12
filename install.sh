#!/usr/bin/env bash
# TraeWork / TraeCode 技能插件一键安装脚本 (Linux / macOS)
# 用法:
#   ./install.sh                    # 默认: 安装到全局 ~/.trae-cn/skills (软链接模式)
#   ./install.sh copy               # 复制模式 (不链接, 离线)
#   ./install.sh project /path/ws   # 安装到指定项目的 .trae/skills (复制模式)
#   SOURCE_ROOT=/abs/here ./install.sh     # 自定义源目录(脚本所在目录为默认值)

set -euo pipefail

# ---- 解析参数 ----
MODE="${1:-link}"           # link | copy | project
PROJECT_DIR="${2:-}"

# ---- 源目录自动定位(跟随脚本所在目录) ----
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SOURCE_ROOT="${SOURCE_ROOT:-$SCRIPT_DIR}"

# ---- 跳过的目录 ----
SKIP_DIRS=(".idea" ".lh" ".git")

# ---- 颜色 ----
C_CYAN='\033[36m'
C_GREEN='\033[32m'
C_YELLOW='\033[33m'
C_GRAY='\033[90m'
C_RED='\033[31m'
C_DARK_CYAN='\033[36;1m'
C_RESET='\033[0m'

# ---- 确定目标目录 ----
if [[ "$MODE" == "project" ]]; then
    if [[ -z "$PROJECT_DIR" ]]; then
        echo -e "${C_RED}[ERROR] project 模式需要第二个参数传入项目目录${C_RESET}" >&2
        exit 1
    fi
    TARGET_ROOT="$PROJECT_DIR/.trae/skills"
    FORCE_COPY=1
    MODE_LABEL="project(copy): $PROJECT_DIR"
else
    TARGET_ROOT="${TARGET_ROOT:-$HOME/.trae-cn/skills}"
    if [[ "$MODE" == "copy" ]]; then
        FORCE_COPY=1
        MODE_LABEL="global(copy)"
    else
        FORCE_COPY=0
        MODE_LABEL="global(symlink)"
    fi
fi

echo -e "${C_CYAN}===== TraeWork Skills Installer (Unix) =====${C_RESET}"
echo -e "Plugin root : ${SOURCE_ROOT}"
echo -e "Install mode: ${MODE_LABEL}"
echo -e "Target dir  : ${TARGET_ROOT}"
echo ""

# ---- 存在性检查 ----
if [[ ! -d "$SOURCE_ROOT" ]]; then
    echo -e "${C_RED}[ERROR] Source root not found: ${SOURCE_ROOT}${C_RESET}" >&2
    exit 1
fi

if [[ ! -d "$TARGET_ROOT" ]]; then
    echo -e "${C_YELLOW}[CREATE] Target dir missing, creating: ${TARGET_ROOT}${C_RESET}"
    mkdir -p "$TARGET_ROOT"
fi

# ---- 枚举 skills ----
skill_names=()
while IFS= read -r -d '' subdir; do
    name="$(basename "$subdir")"
    skip=0
    for s in "${SKIP_DIRS[@]}"; do [[ "$name" == "$s" ]] && skip=1 && break; done
    [[ $skip -eq 1 ]] && continue
    if [[ -f "$subdir/SKILL.md" ]]; then
        skill_names+=("$name")
    fi
done < <(find "$SOURCE_ROOT" -mindepth 1 -maxdepth 1 -type d -print0)

if [[ ${#skill_names[@]} -eq 0 ]]; then
    echo -e "${C_YELLOW}[WARN] No SKILL.md subdirs under ${SOURCE_ROOT}${C_RESET}"
    exit 0
fi

echo -e "${C_GREEN}[SCAN] Found ${#skill_names[@]} skills:${C_RESET}"
for n in "${skill_names[@]}"; do echo -e "  - ${n}"; done
echo ""

# ---- 通用: 拷贝目录函数 ----
copy_skill() {
    local src="$1" dst="$2"
    # rsync 优先, 否则 cp -R
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' "$src/" "$dst/"
    else
        mkdir -p "$dst"
        cp -R "$src"/* "$dst"/ 2>/dev/null || true
        # 清理 __pycache__
        find "$dst" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    fi
}

# ---- 安装每个 skill ----
succ=0; skip=0; fail=0
for name in "${skill_names[@]}"; do
    src="${SOURCE_ROOT}/${name}"
    dst="${TARGET_ROOT}/${name}"

    echo -e "${C_CYAN}[${name}]${C_RESET} ${src}"

    need_install=1

    # 目标已存在处理
    if [[ -e "$dst" || -L "$dst" ]]; then
        if [[ $FORCE_COPY -eq 0 && -L "$dst" ]]; then
            cur="$(readlink -f "$dst" 2>/dev/null || readlink "$dst")"
            exp="$(readlink -f "$src" 2>/dev/null || echo "$src")"
            if [[ "$cur" == "$exp" ]]; then
                echo -e "  ${C_GRAY}[SKIP] Symlink OK${C_RESET}"
                skip=$((skip+1)); need_install=0
            else
                echo -e "  ${C_YELLOW}[RECREATE] symlink target changed${C_RESET}"
                rm -f "$dst"
            fi
        else
            ts="$(date +%Y%m%d%H%M%S)"
            bak="${dst}.bak.${ts}"
            echo -e "  ${C_YELLOW}[BACKUP] Existing item -> ${bak}${C_RESET}"
            mv "$dst" "$bak"
        fi
    fi

    [[ $need_install -eq 0 ]] && continue

    # 实际动作
    if [[ $FORCE_COPY -eq 1 ]]; then
        if copy_skill "$src" "$dst" 2>/tmp/trae_install_err; then
            echo -e "  ${C_GREEN}[OK] Copied${C_RESET}"
            succ=$((succ+1))
        else
            err_msg="$(cat /tmp/trae_install_err 2>/dev/null || echo 'copy failed')"
            echo -e "  ${C_RED}[FAIL] ${err_msg}${C_RESET}"
            fail=$((fail+1))
        fi
    else
        if ln -s "$src" "$dst" 2>/tmp/trae_install_err; then
            [[ -L "$dst" ]] && { echo -e "  ${C_GREEN}[OK] Symlinked${C_RESET}"; succ=$((succ+1)); } \
                             || { echo -e "  ${C_RED}[FAIL] post-check symlink${C_RESET}"; fail=$((fail+1)); }
        else
            err_msg="$(cat /tmp/trae_install_err 2>/dev/null || echo 'ln failed')"
            echo -e "  ${C_RED}[FAIL] ${err_msg}${C_RESET}"
            if [[ "$(id -u)" != "0" ]]; then
                echo -e "      ${C_YELLOW}-> TIP: retrying with copy mode: ./install.sh copy${C_RESET}"
            fi
            fail=$((fail+1))
        fi
    fi
done

# ---- 汇总 ----
fclr=$([[ $fail -gt 0 ]] && echo "$C_RED" || echo "$C_GRAY")
echo ""
echo -e "${C_CYAN}===== DONE =====${C_RESET}"
echo -e "  ${C_GREEN}Success: ${succ}${C_RESET}"
echo -e "  ${C_GRAY}Skipped: ${skip}${C_RESET}"
echo -e "  ${fclr}Failed : ${fail}${C_RESET}"
echo ""
echo -e "${C_DARK_CYAN}Next step: Restart TraeWork / TraeCode, then Settings -> Skills & Commands -> Skills.${C_RESET}"
echo -e "         Or for project-mode: re-open project in TraeCode.${C_RESET}"
