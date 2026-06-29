---
domain: scop.iwhalecloud.com
aliases: [SCOP, 黑鸭子, BlackDuck, 软件组成分析]
updated: 2026-04-28
---

## 平台特征

- **框架**：LayUI SPA，所有数据通过 AJAX 异步加载，页面不刷新
- **标签页**：4 个 — 组件、安全、来源、报告，通过 `li` 元素切换，激活态标记为 `layui-this`
- **URL 格式**：`/scans/detail?projectId=<uuid>&versionId=<uuid>`
- **登录态**：通过用户 Chrome 携带，不需要额外认证
- **初始加载**：页面可能先重定向到 `/` 再跳回，需等待 4s 以上
- **表格翻页**：LayUI 分页组件 `.layui-laypage`，每页行索引从 0 开始

## 页面结构

### 标签导航

```html
<div class="layui-tab">
  <ul class="layui-tab-title">
    <li class="component-tab">组件</li>
    <li class="security-tab">安全</li>
    <li>来源</li>
    <li>报告</li>
  </ul>
  <div class="layui-tab-content">
    <div class="layui-tab-item component-tab-item">...</div>
    <div class="layui-tab-item security-tab-item">...</div>
  </div>
</div>
```

- 检测安全标签是否激活：`li.security-tab.layui-this` 存在即为激活
- 安全标签内容容器：`.security-tab-item.layui-show`

### 组件标签页 (Components Tab)

- 表格 `table#componentTable`，LayUI 视图 `[lay-id="componentTable"]`
- 列：组件 | 来源 | 匹配类型 | 使用 | 许可证 | 安全风险 | 运维风险 | 加密 | 依赖引入源 | 备案说明
- 组件名格式：`<namespace>:<group>:<artifact>:<version>`（如 `maven:commons-collections:commons-collections:3.1`）
- 组件名是链接，href 指向 `/scans/componentVersionDetail?...`

### 风险总览卡片

位于组件标签页内容区顶部，3 张卡片：

- 安全风险：严重/高危/中危/低危/安全 计数 + 百分比进度条
- 许可证风险：同上结构
- 运维风险：同上结构

CSS 选择器：`.vulnerability-card`（安全风险卡片）

### 安全标签页 (Security Tab)

结构：
```
.security-tab-item.layui-show
  .background-div
    .layui-card.vulnerability-card  ← 安全风险统计卡片
    .layui-card                     ← 组件列表卡片（含表格和展开详情）
      .layui-card-body
        [搜索表单: .securityForm]
        [表格: #securityComponentTable, lay-id="securityComponentTable"]
        [展开的详情面板: 点击行后出现在 .layui-card-body 内的新 .layui-card]
```

### 安全组件表格 (securityComponentTable)

- 表头：组件 | 来源 | 匹配类型 | 使用 | 许可证 | 安全风险 | 运维风险
- 每行 `tr[data-index="N"]`
- LayUI 视图容器：`.layui-table-view[lay-id="securityComponentTable"]`

### 漏洞详情展开面板

点击安全表格中的组件行后，在 `.security-tab-item.layui-show` 内出现新的 `.layui-card`（追加到 layui-card 列表末尾）。

面板内容结构：
- 组件名和坐标（如 `Apache Commons Collections 3.1 maven:commons-collections:commons-collections:3.1`）
- 已知漏洞数量
- 漏洞详情表格：操作标识符 | 发布时间 | 总体得分 | 等级
  - 标识符格式：`NVD CVE-2015-7501` 或 `BDSA BDSA-2017-2285 (CVE-2017-15708)`
  - 得分：CVSS 数值（如 9.8）
  - 等级：严重/高危/中危/低危
- 升级建议：
  - 短期升级建议：版本号 + 是否有已知漏洞
  - 长期升级建议：版本号 + 是否有已知漏洞
  - 备选升级建议：版本号 + 是否有已知漏洞
- 运维风险表格（可能显示"无数据"）

## 核心 CSS 选择器

| 用途 | 选择器 |
|------|--------|
| 安全标签（点击） | `li.security-tab` |
| 安全标签是否激活 | `li.security-tab.layui-this` |
| 安全标签内容区 | `.security-tab-item.layui-show` |
| 安全组件表格视图 | `.layui-table-view[lay-id="securityComponentTable"]` |
| 安全表格行 | `.layui-table-view[lay-id="securityComponentTable"] tr[data-index]` |
| 点击特定行 | `.layui-table-view[lay-id="securityComponentTable"] tr[data-index="N"]` |
| 安全标签内所有卡片 | `.security-tab-item.layui-show .layui-card` |
| 分页控件 | `.layui-laypage` |
| 下一页按钮 | `.layui-laypage .layui-laypage-next` |
| 组件详情链接 | `a[href*="componentVersionDetail"]` |

## 已验证的 JS 提取代码

### 1. 提取安全表格中所有组件行

```js
var view = document.querySelector('.layui-table-view[lay-id="securityComponentTable"]');
var rows = view.querySelectorAll('.layui-table-body tr[data-index]');
var result = [];
rows.forEach(function(row) {
  result.push({
    index: row.getAttribute('data-index'),
    text: row.textContent.trim().substring(0, 200)
  });
});
JSON.stringify(result);
```

### 2. 查找特定组件行（按名称过滤）

```js
var view = document.querySelector('.layui-table-view[lay-id="securityComponentTable"]');
var rows = view.querySelectorAll('tr[data-index]');
var result = [];
rows.forEach(function(row, i) {
  var t = row.textContent;
  if (t.indexOf('SEARCH_TERM') > -1) {
    result.push({rowIndex: i, dataIndex: row.getAttribute('data-index'), text: t.substring(0, 300)});
  }
});
JSON.stringify(result);
```

### 3. 提取展开的漏洞详情面板

```js
var cards = document.querySelectorAll('.security-tab-item.layui-show .layui-card');
// 最后一张卡片是展开的详情面板
var detailCard = cards[cards.length - 1];
JSON.stringify(detailCard.textContent);
```

### 4. 验证页面加载完成

```js
document.querySelector('table#componentTable') ? 'loaded' : 'not loaded'
```

### 5. 验证安全标签已激活

```js
document.querySelector('li.security-tab.layui-this') ? 'active' : 'not active'
```

### 6. 提取分页信息

```js
var pageEl = document.querySelector('.layui-laypage');
if (pageEl) {
  var counts = pageEl.querySelectorAll('.layui-laypage-count');
  var nextBtn = pageEl.querySelector('.layui-laypage-next');
  JSON.stringify({
    hasNext: nextBtn && !nextBtn.classList.contains('layui-disabled'),
    countText: counts.length > 0 ? counts[0].textContent : ''
  });
} else {
  'no pagination';
}
```

## 已知陷阱

1. **componentVersionDetail 页面无漏洞数据**（2026-04-28）：通过组件行链接打开的 `/scans/componentVersionDetail?...` 页面只显示组件元数据（描述、发布日期、许可证、标签），不包含任何 CVE 详情。漏洞数据必须通过安全标签页的展开面板获取。

2. **`tr[data-index="N"]` 不唯一**（2026-04-28）：页面上有多个 LayUI 表格（componentTable、securityComponentTable 等），都使用 `data-index` 属性。不用 scoped 选择器会点击到错误的表格行。必须加 `[lay-id="xxx"]` 前缀。

3. **异步渲染必须等待**（2026-04-28）：点击标签和行后，LayUI 通过 AJAX 异步渲染内容。不等待 2-3 秒直接 `/eval` 获取到的是旧 DOM 状态。

4. **安全风险列值为 0 不展开**（2026-04-28）：点击安全风险为 0 的组件行不会出现漏洞详情面板，需先检查计数。

5. **翻页后 data-index 重置**（2026-04-28）：LayUI 分页后每页的 data-index 都从 0 开始，需要用组件名而非索引定位。

6. **登录过期重定向**（2026-04-28）：如果 `/eval` 检查不到预期元素，用 `/info` 确认当前 URL——可能已重定向到登录页。

7. **BDSA ID 不可公共查询**（2026-04-28）：BDSA 是 BlackDuck 私有标识符，公共 CVE 数据库查不到。报告中标明"仅 SCOP 平台数据"即可。
