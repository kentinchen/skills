#!/usr/bin/env bash
# 批量创建 TraeWork 全局 Skills 目录符号链接 (Linux/macOS)
# 将源目录下每个含 SKILL.md 的子目录软链接到 ~/.trae-cn/skills
# 参考 link-skills.ps1 的逻辑

set -euo pipefail

# ========== 配置（可按需修改） ==========
SOURCE_ROOT="${SOURCE_ROOT:-$HOME/project/skills}"
TARGET_ROOT="${TARGET_ROOT:-$HOME/.trae-cn/skills}"

# 跳过的目录名（非 Skill 目录）
SKIP_DIRS=(".idea" ".lh" ".git")
# =======================================

# 颜色定义
C_CYAN='\033[36m'
C_GREEN='\033[32m'
C_YELLOW='\033[33m'
C_GRAY='\033[90m'
C_RED='\033[31m'
C_DARK_CYAN='\033[36;1m'
C_RESET='\033[0m'

echo -e "${C_CYAN}===== TraeWork Skills Symlink Batch Script =====${C_RESET}"
echo -e "Source: ${SOURCE_ROOT}"
echo -e "Target: ${TARGET_ROOT}"
echo ""

# ---------- 1. 存在性检查 ----------
if [[ ! -d "$SOURCE_ROOT" ]]; then
    echo -e "${C_RED}[ERROR] Source directory does not exist: ${SOURCE_ROOT}${C_RESET}" >&2
    exit 1
fi

if [[ ! -d "$TARGET_ROOT" ]]; then
    echo -e "${C_YELLOW}[CREATE] Target dir missing, creating: ${TARGET_ROOT}${C_RESET}"
    mkdir -p "$TARGET_ROOT"
fi

# ---------- 2. 枚举源 Skill 目录 ----------
skill_names=()
while IFS= read -r -d '' subdir; do
    name="$(basename "$subdir")"
    # 跳过指定目录
    skip=0
    for s in "${SKIP_DIRS[@]}"; do
        if [[ "$name" == "$s" ]]; then skip=1; break; fi
    done
    [[ $skip -eq 1 ]] && continue
    # 只处理含 SKILL.md 的目录
    if [[ -f "$subdir/SKILL.md" ]]; then
        skill_names+=("$name")
    fi
done < <(find "$SOURCE_ROOT" -mindepth 1 -maxdepth 1 -type d -print0)

if [[ ${#skill_names[@]} -eq 0 ]]; then
    echo -e "${C_YELLOW}[WARN] No skill directories with SKILL.md found under ${SOURCE_ROOT}${C_RESET}"
    exit 0
fi

echo -e "${C_GREEN}[SCAN] Found ${#skill_names[@]} skill directories:${C_RESET}"
for n in "${skill_names[@]}"; do
    echo -e "  - ${n}"
done
echo ""

# ---------- 3. 逐个创建软链接 ----------
success_count=0
skip_count=0
fail_count=0

for name in "${skill_names[@]}"; do
    link_path="${TARGET_ROOT}/${name}"
    target_path="${SOURCE_ROOT}/${name}"

    echo -e "${C_CYAN}[${name}]${C_RESET} ${target_path}"

    need_create=1

    # 检查链接路径是否已存在
    if [[ -e "$link_path" || -L "$link_path" ]]; then
        if [[ -L "$link_path" ]]; then
            # 是符号链接，比较目标
            current_target="$(readlink "$link_path")"
            # 规范化为绝对路径
            nc="$(readlink -f "$link_path" 2>/dev/null || echo "$current_target")"
            ne="$(readlink -f "$target_path" 2>/dev/null || echo "$target_path")"

            if [[ "$nc" == "$ne" ]]; then
                echo -e "  ${C_GRAY}[SKIP] Symlink exists and points correctly${C_RESET}"
                skip_count=$((skip_count + 1))
                need_create=0
            else
                echo -e "  ${C_YELLOW}[RECREATE] Wrong target: current=${current_target} , expected=${target_path}${C_RESET}"
                rm -f "$link_path"
                need_create=1
            fi
        else
            # 是普通文件/目录，不是链接 → 备份
            ts="$(date +%Y%m%d%H%M%S)"
            backup_path="${link_path}.bak.${ts}"
            echo -e "  ${C_YELLOW}[BACKUP] Non-link item exists, backed up to: ${backup_path}${C_RESET}"
            mv "$link_path" "$backup_path"
            need_create=1
        fi
    fi

    [[ $need_create -eq 0 ]] && continue

    # 创建符号链接
    if ln -s "$target_path" "$link_path" 2>/dev/null; then
        # 验证
        if [[ -L "$link_path" ]]; then
            echo -e "  ${C_GREEN}[OK] Symlink created -> ${target_path}${C_RESET}"
            success_count=$((success_count + 1))
        else
            echo -e "  ${C_RED}[FAIL] Post-create check: not a symlink${C_RESET}"
            fail_count=$((fail_count + 1))
        fi
    else
        echo -e "  ${C_RED}[FAIL] ln -s failed${C_RESET}"
        # 权限提示（部分系统对非 root 用户限制创建符号链接）
        if [[ "$(id -u)" != "0" ]]; then
            echo -e "      ${C_YELLOW}-> TIP: If symlink creation is restricted, re-run with sudo or check fs.protected_symlinks.${C_RESET}"
        fi
        fail_count=$((fail_count + 1))
    fi
done

# ---------- 4. 汇总 ----------
echo ""
echo -e "${C_CYAN}===== DONE =====${C_RESET}"
echo -e "  ${C_GREEN}Success: ${success_count}${C_RESET}"
echo -e "  ${C_GRAY}Skipped: ${skip_count}${C_RESET}"
if [[ $fail_count -gt 0 ]]; then
    echo -e "  ${C_RED}Failed : ${fail_count}${C_RESET}"
else
    echo -e "  ${C_GRAY}Failed : ${fail_count}${C_RESET}"
fi
echo ""
echo -e "${C_DARK_CYAN}Next step: Restart TraeWork, then check Settings -> Skills & Commands -> Skills.${C_RESET}"
