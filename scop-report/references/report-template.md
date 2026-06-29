# 黑鸭子扫描报告模板

生成报告时，用实际数据替换 `{{...}}` 占位符。无数据的 section 标"（无）"或省略。

---

# 黑鸭子扫描报告

## 扫描概览

| 项目 | 内容 |
|------|------|
| **项目名称** | {{PROJECT_NAME}} |
| **扫描时间** | {{SCAN_TIME}} |
| **组件总数** | {{TOTAL_COMPONENTS}} |
| **有漏洞组件数** | {{VULN_COMPONENT_COUNT}} |
| **漏洞总数** | {{TOTAL_VULN_COUNT}} |

## 风险总览

| 风险类型 | 严重 | 高危 | 中危 | 低危 | 安全 |
|---------|------|------|------|------|------|
| 安全风险 | {{SEC_CRITICAL}} | {{SEC_HIGH}} | {{SEC_MEDIUM}} | {{SEC_LOW}} | {{SEC_SAFE}} |
| 许可证风险 | {{LIC_CRITICAL}} | {{LIC_HIGH}} | {{LIC_MEDIUM}} | {{LIC_LOW}} | {{LIC_SAFE}} |
| 运维风险 | {{OPS_CRITICAL}} | {{OPS_HIGH}} | {{OPS_MEDIUM}} | {{OPS_LOW}} | {{OPS_SAFE}} |

## 安全漏洞详情

> 以下列出所有存在安全漏洞的组件及其详情。

{{#each COMPONENTS_WITH_VULNS}}

### {{COMPONENT_NAME}} {{VERSION}}

- **组件坐标**：`{{COORDINATE}}`
- **已知漏洞数**：{{VULN_COUNT}}
- **许可证**：{{LICENSE}}

#### 漏洞列表

| 来源 | 标识符 | CVSS | 等级 | 发布时间 | 描述 |
|------|--------|------|------|----------|------|
{{#each VULNERABILITIES}}
| {{SOURCE}} | [{{CVE_ID}}]({{NVD_URL}}) | {{CVSS_SCORE}} | {{SEVERITY}} | {{PUBLISH_DATE}} | {{DESCRIPTION}} |
{{/each}}

#### 升级建议

| 类型 | 建议版本 | 坐标 | 是否有已知漏洞 |
|------|---------|------|---------------|
| 短期升级 | {{SHORT_TERM_VERSION}} | {{SHORT_TERM_COORD}} | {{SHORT_TERM_VULN_STATUS}} |
| 长期升级 | {{LONG_TERM_VERSION}} | {{LONG_TERM_COORD}} | {{LONG_TERM_VULN_STATUS}} |
| 备选方案 | {{ALT_VERSION}} | {{ALT_COORD}} | {{ALT_VULN_STATUS}} |

#### 运维风险

{{#if OPS_RISKS}}
| 风险描述 | 等级 |
|----------|------|
{{#each OPS_RISKS}}
| {{DESCRIPTION}} | {{LEVEL}} |
{{/each}}
{{else}}
（无运维风险记录）
{{/if}}

---

{{/each}}

## 外部 CVE 参考来源

{{#each CVE_REFERENCES}}
- [{{CVE_ID}}]({{URL}}) — {{SOURCE_NAME}}
{{/each}}

---

> 报告生成时间：{{REPORT_GENERATION_TIME}}
> 数据来源：SCOP 平台 (scop.iwhalecloud.com) + NVD (nvd.nist.gov) + 厂商安全公告
