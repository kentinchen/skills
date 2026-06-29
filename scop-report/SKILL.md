---
name: scop-report
description: 黑鸭子扫描报告。从 SCOP 平台 (scop.iwhalecloud.com) 提取软件组成分析数据，结合外部 CVE 情报生成综合扫描报告。
  触发场景：用户要求生成黑鸭子扫描报告、SCOP 报告、组件安全扫描报告、组件漏洞报告。
---

# scop-report Skill

## 前置条件

本 skill 必须在 `web-access` skill 已加载的情况下使用。

- CDP 浏览器操作通过 web-access 的 CDP Proxy (`localhost:9223`) 执行
- 外部 CVE 调研通过 WebSearch/WebFetch 完成
- CDP API 完整参考见 web-access skill
- 需要一个有效的 SCOP 扫描详情 URL：`https://scop.iwhalecloud.com/scans/detail?projectId=<uuid>&versionId=<uuid>`

## 严格禁止

- **不跳过等待**：每次 click（标签、行、翻页）后必须 `sleep 3`，LayUI 异步渲染需要时间
- **不用未 scoped 的选择器**：`tr[data-index="N"]` 会匹配到错误的表格，必须用 `.layui-table-view[lay-id="xxx"] tr[data-index="N"]`
- **不用 componentVersionDetail 页面取漏洞数据**：该页面只有组件元数据，漏洞详情必须在 Security 标签页点击行展开获取
- **不假设数据已加载**：每次操作后先用 `/eval` 验证目标元素存在，再提取数据

## 严格要求

- **加载平台参考**：操作 SCOP 前必须先读取 `references/scop-platform.md`
- **确认 CDP 就绪**：操作前执行 web-access 的 check-deps
- **等待异步渲染**：每次交互后 `sleep 3`
- **选择器精确性**：所有表格查询必须包含 `lay-id` 属性
- **处理 BSDA**：BDSA ID 无法从公共源查到，报告标注"仅 SCOP 平台数据"
- **报告格式**：按 `references/report-template.md` 生成

## 工作流程

### Phase 0: 准备

1. 读取 `references/scop-platform.md` 获取 SCOP 平台知识
2. 运行 `node "${CLAUDE_SKILL_DIR}/../web-access/scripts/check-deps.mjs"`（或直接 curl localhost:9223 检查）
3. 确定 SCOP URL：
   - 用户直接提供 → 使用
   - 用户说"当前页面" → 检查 `/targets` 中打开的 SCOP 详情页
   - 都没有 → 询问用户

### Phase 1: 导航与概览提取

1. 创建后台 tab 打开 SCOP 详情页：
   ```bash
   curl -s "http://localhost:9223/new?url=<URL_ENCODED_SCOP_URL>"
   ```
2. `sleep 4` 等待 SPA 完全渲染（注意可能先重定向到 / 再跳回）
3. 验证页面加载：检查 `componentTable` 是否存在
4. 提取扫描概览信息：
   - 项目名称（页面标题中的 signature 部分）
   - 风险总览卡片数据：安全风险/许可证风险/运维风险 各等级的计数（严重/高危/中危/低危/安全）
   - 组件总数（从 componentTable 的分页信息获取）

### Phase 2: 安全标签页 — 枚举有漏洞的组件

1. 点击安全标签：
   ```bash
   curl -s -X POST "http://localhost:9223/click?target=<TARGET_ID>" -d 'li.security-tab'
   ```
2. `sleep 3`，验证 `li.security-tab.layui-this` 存在
3. 从 `securityComponentTable` 提取所有行：
   ```js
   var view = document.querySelector('.layui-table-view[lay-id="securityComponentTable"]');
   var rows = view.querySelectorAll('tr[data-index]');
   // 提取每行的组件名、版本和漏洞数
   ```
4. 筛选出漏洞数 > 0 的组件，建立待处理列表

### Phase 3: 逐组件提取漏洞详情（核心迭代）

对当前页每个有漏洞的组件行：

1. 点击行（**必须 scoped**）：
   ```bash
   curl -s -X POST "http://localhost:9223/click?target=<TARGET_ID>" \
     -d '.layui-table-view[lay-id="securityComponentTable"] tr[data-index="N"]'
   ```
2. `sleep 3`
3. 提取展开的详情面板（最后一张 layui-card）：
   ```js
   var cards = document.querySelectorAll(".security-tab-item.layui-show .layui-card");
   var detail = cards[cards.length - 1];
   detail.textContent;  // 获取完整文本
   ```
4. 从文本中解析：
   - CVE/BDSA ID、CVSS 分数、严重等级、发布时间
   - 升级建议：短期版本、长期版本、备选方案
   - 运维风险数据
5. 如有翻页：检查分页控件，点击下一页，重复 Phase 3

### Phase 4: 并行 CVE 外部调研

1. 汇总所有 CVE ID（去重，排除 BDSA）
2. 加载 `references/cve-research.md`
3. 按 web-access 分治策略，将 CVE 分批派给子 Agent：
   - 每批最多 5 个 CVE
   - 每个子 Agent prompt：`必须加载 web-access skill 并遵循指引`
   - 目标：从 NVD/Red Hat 获取每个 CVE 的描述、CVSS 向量、受影响版本
4. 收集子 Agent 返回的摘要，按 CVE ID 合并

### Phase 5: 生成报告

1. 加载 `references/report-template.md`
2. 填充模板：扫描概览 → 风险总览表 → 安全漏洞详情（逐组件）→ 运维风险
3. 外部 CVE 详情关联到对应组件的漏洞表
4. 写入 Markdown 文件到用户指定路径（默认当前目录 `scop-report-<project>.md`）
5. `/close` 清理 CDP tab

## 关键决策点

| 场景 | 处理 |
|------|------|
| URL 来源 | 用户提供 > 当前 tab > 询问 |
| 漏洞组件 > 20 个 | 分批处理，每批后保存中间结果 |
| CVE 总数 > 50 | 仅对 CVSS >= 9.0 做外部调研，其余只列 ID |
| 翻页 | 检测 `.layui-laypage` 控件，逐页遍历 |
| 超时 | CDP 命令 10s 超时重试一次，连续失败 3 次标记"提取失败" |
| 已有 SCOP tab | 复用 `/targets` 中已打开的 SCOP 详情页 |
| 零漏洞 | 跳过 Phase 3-4，报告显示"未发现安全漏洞" |

## Reference 索引

| 文件 | 何时加载 |
|------|---------|
| `references/scop-platform.md` | **必须**在任何 SCOP CDP 操作前加载 |
| `references/report-template.md` | 生成报告时加载 |
| `references/cve-research.md` | 调研 CVE 外部详情时加载 |
