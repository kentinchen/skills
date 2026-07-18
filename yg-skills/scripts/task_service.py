import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yg_base import YgBase


class TaskService(YgBase):
    def get_todo_tasks(self, page_num=1, page_size=10, instance_id=None, instance_name=None,
                       instance_name_two=None, task_id=None, task_name=None):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/task/taskTodoList"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        data = {
            'pageNum': page_num,
            'pageSize': page_size,
            'instanceId': instance_id,
            'instanceName': instance_name,
            'instanceNameTwo': instance_name_two,
            'taskId': task_id,
            'taskName': task_name
        }
        result = self.call_api(url, method='post', headers=headers, json_data=data)
        if result:
            code = result.get('code')
            if code == 200:
                return result
            else:
                print(f"查询待办工单失败: {result.get('msg')}")
        return None

    def get_done_tasks(self, page_num=1, page_size=10):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/task/taskDoneList"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        params = {
            'pageNum': page_num,
            'pageSize': page_size
        }
        result = self.call_api(url, method='get', headers=headers, params=params)
        if result:
            code = result.get('code')
            if code == 200:
                return result
            else:
                print(f"查询完成工单失败: {result.get('msg')}")
        return None


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="工单查询脚本")
    parser.add_argument('--page-num', '--pageNum', type=int, default=1, help='页码')
    parser.add_argument('--page-size', '--pageSize', type=int, default=10, help='每页大小')
    parser.add_argument('--type', choices=['todo', 'done'], default='todo', help='工单类型: todo(待办), done(完成)')
    parser.add_argument('--instance-id', '--instanceId', help='实例ID（待办工单筛选）')
    parser.add_argument('--instance-name', '--instanceName', help='实例名称（待办工单筛选）')
    parser.add_argument('--instance-name-two', '--instanceNameTwo', help='实例名称二（待办工单筛选）')
    parser.add_argument('--task-id', '--taskId', help='任务ID（待办工单筛选）')
    parser.add_argument('--task-name', '--taskName', help='任务名称（待办工单筛选）')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()

    task_service = TaskService()
    task_service.get_token(app_username=args.app_username)

    if args.type == 'todo':
        print(f"查询待办工单: pageNum={args.page_num}, pageSize={args.page_size}")
        result = task_service.get_todo_tasks(
            page_num=args.page_num,
            page_size=args.page_size,
            instance_id=args.instance_id,
            instance_name=args.instance_name,
            instance_name_two=args.instance_name_two,
            task_id=args.task_id,
            task_name=args.task_name
        )
        if result:
            print("\n待办工单查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")
    else:
        print(f"查询完成工单: pageNum={args.page_num}, pageSize={args.page_size}")
        result = task_service.get_done_tasks(page_num=args.page_num, page_size=args.page_size)
        if result:
            print("\n完成工单查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")


if __name__ == "__main__":
    main()
