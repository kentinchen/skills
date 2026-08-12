# AGENTS.md — Local Skills Bundle 索引

> TraeWork / TraeCode 会在启动/开项目时读取 AGENTS.md，把这里登记的 skills 作为优先匹配候选。
> 放在插件包根目录或项目根目录都能生效。

## 已注册技能一览

| 触发关键词示例 | Skill 名 | 版本 | 脚本/服务 |
|---|---|---|---|
| "cpolar 隧道"、"SSH 公网地址"、"代理链"、"20808 端口" | [cpolar-tunnel](./cpolar-tunnel/SKILL.md) | 1.0.0 | `cpolar_ssh_public_url.py` / `dynamic_proxy_script.py` / `twin_dynamic_proxy_script.py` |
| "识别验证码"、"滑动验证码"、"OCR 检测目标" | [dddd-ocr](./dddd-ocr/SKILL.md) | 1.0.0 | `scripts/ocr_client.py`（需 ddddocr-fastapi 服务） |
| "加入知识库"、"ingest 文档"、"创建 wiki 页"、"Karpathy KB" | [knowbase-ingest](./knowbase-ingest/SKILL.md) | 1.0.0 | 模板+流程：`references/schema-guide.md` / `wiki-page-template.md` |
| "哪吒监控"、"Nezha 服务器"、"查服务器清单" | [nazha-skills](./nazha-skills/SKILL.md) | 1.0.0 | `nazha_login.py` / `server_service.py` |
| "黑鸭子报告"、"SCOP 扫描"、"组件漏洞报告"、"CVE 扫描" | [scop-report](./scop-report/SKILL.md) | 1.0.0 | 参考模板 `references/report-template.md`，依赖 web-access CDP Proxy |
| "发布到 WCT 市场"、"更新 WCT 技能"、"上传 dc.iwhalecloud" | [wct-skill-publish](./wct-skill-publish/SKILL.md) | 1.0.0 | `references/api-reference.md` |
| "YG 工单"、"云管通知"、"YG 账单"、"云管监控概览"、"客户画像" | [yg-services](./yg-skills/SKILL.md) | 2.0.0 | `scripts/{notice,task,monitor,resource,file,billing,customer}_service.py` |
| "YW 工单"、"云网 SSO 登录"、"APP token"、"系统清单" | [yw-services](./yw-skills/SKILL.md) | 1.1.0 | `scripts/yw_login.py` / `task_service.py` / `sso_utils.py` |
| "给 ZCM 单子加评论"、"浩鲸研发云评论"、"需求/任务/缺陷 评论" | [zcm-task-add-comment](./zcm-task-add-comment/SKILL.md) | 1.0.0 | `script.sh` / `local-skill-config.sh` |

## 使用提示

1. 优先用**自然语言**触发，例如：
   - > "帮我查下 YG 系统今天的待办工单"
   - > "这张截图里有个验证码，帮我用 dddd-ocr 识别一下"
2. 命令面板方式：在对话框输入 `/` 后选择对应技能的触发词。
3. 配置型技能首次使用会提示配置文件路径：
   - YG：`~/.yg-skills/config.yml`
   - YW：通过 sso_utils.py 完成 SSO 登录缓存
   - Nazha：`nazha-skills/config/nazha_config.json`
   - cpolar：`~/.cpolar/auth.yaml`
