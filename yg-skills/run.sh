python yg-skills/scripts/sso_login.py --username 18208151273 --password Admin@qwer123 --sso-url https://zwwsfrz.cdmbc.cn --app-url https://10.190.227.110 --app-code 2a06bab333f5257deb664b8b16a30f23 --login-device-info a8799d06d5e4b4bf4b8efe54b5086f7c  --proxy socks5://localhost:20809 

python yg-skills/scripts/notice_service.py
python yg-skills/scripts/notice_service.py --notice-id 46f0e445b4aec2be0a473d4e37c5152e

# 查询待办工单
python yg-skills/scripts/task_service.py --type todo --page-num 1 --page-size 10
# 查询完成工单
python yg-skills/scripts/task_service.py --type done --page-num 1 --page-size 10
# 带筛选条件查询待办工单
python yg-skills/scripts/task_service.py --type todo --instance-name "工单名称" --task-name "任务名称"

# 查询监控概览
python yg-skills/scripts/monitor_service.py --type overview
# 查询每天统计
python yg-skills/scripts/monitor_service.py --type daily --supplier-code "chengyun" --time "2026-06-15"

# 查询资源变化
python yg-skills/scripts/resource_service.py --type change --time "2026-07-06--2026-07-12" --supplier "H3C_outside"
# 查询云商资源
python yg-skills/scripts/resource_service.py --type supplier --supplier-code "chengyun" --date-offset 7

# 查询文件列表
python yg-skills/scripts/file_service.py --type list --file-type "运维工具"
# 查询文件资源
python yg-skills/scripts/file_service.py --type resources --key "ResourcesUp" --resource 7

# 查询账单系数
python yg-skills/scripts/billing_service.py --cloud-supplier "chengyun" --time-tag "2026-07-15"
