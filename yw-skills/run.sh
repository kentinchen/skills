# 首次登录（交互式配置）
python yw-skills/scripts/yw_login.py

# 指定参数登录
python yw-skills/scripts/yw_login.py --username 15208450822 --password Admin@qwer123

# 强制重新登录
python yw-skills/scripts/yw_login.py --force-login

# 使用代理登录
python yw-skills/scripts/yw_login.py --proxy socks5://localhost:20809

# 查询未完成工单数
python yw-skills/scripts/task_service.py --type todo_count

# 查询已办工单
python yw-skills/scripts/task_service.py --type handled

# 查询工单动作表
python yw-skills/scripts/task_service.py --type action_map