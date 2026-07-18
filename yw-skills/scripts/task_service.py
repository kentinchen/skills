import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yw_base import YwBase


class TaskService(YwBase):
    def get_todo_count(self, view_id="MY_TODO"):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/gateway/dosm/api/v2/biz/workOrder/count"
        params = {'viewId': view_id}
        return self.call_api(url, method='get', params=params)

    def get_handled_workorders(self, view_id="MY_HANDLER"):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/gateway/dosm/api/v2/customView/getById"
        params = {'id': view_id}
        return self.call_api(url, method='get', params=params)

    def get_action_map(self):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/gateway/dosm/api/v2/custom/butt/action/getActionMap"
        return self.call_api(url, method='get')

    def get_workorder_history(self, work_order_id, current_node_id, data_types=None):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/gateway/dosm/api/v2/biz/mdl/history"
        if data_types is None:
            data_types = ["approve", "modify", "history", "counterSigned"]
        json_data = {
            'workOrderId': work_order_id,
            'currentNodeId': current_node_id,
            'dataType': data_types,
            'nodeIds': None,
            'operationTypes': None,
            'userIds': None,
            'groupIds': None
        }
        return self.call_api(url, method='post', json_data=json_data)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="yw系统工单服务")
    parser.add_argument('--type', choices=['todo_count', 'handled', 'action_map', 'history'],
                        default='todo_count', help='查询类型')
    parser.add_argument('--view-id', '--viewId', default='MY_TODO', help='视图ID（待办工单用MY_TODO，已办工单用MY_HANDLER）')
    parser.add_argument('--work-order-id', '--workOrderId', help='工单ID（查询处理记录时必填）')
    parser.add_argument('--current-node-id', '--currentNodeId', help='当前节点ID（查询处理记录时必填）')
    parser.add_argument('--data-types', '--dataTypes', nargs='+', default=["approve", "modify", "history", "counterSigned"],
                        help='数据类型（查询处理记录时使用，如approve modify history counterSigned）')
    args = parser.parse_args()

    task_service = TaskService()
    task_service.get_token()

    if args.type == 'todo_count':
        print(f"查询待办工单数量: viewId={args.view_id}")
        result = task_service.get_todo_count(view_id=args.view_id)
        if result:
            print("\n待办工单数量查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if 'data' in result:
                count = result['data']
                print(f"\n📊 未完成工单数: {count}")
            elif 'datas' in result:
                count = result['datas']
                print(f"\n📊 未完成工单数: {count}")
        else:
            print("\n查询失败")

    elif args.type == 'handled':
        print(f"查询已办工单: viewId={args.view_id}")
        result = task_service.get_handled_workorders(view_id=args.view_id)
        if result:
            print("\n已办工单查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")

    elif args.type == 'action_map':
        print("查询工单动作表")
        result = task_service.get_action_map()
        if result:
            print("\n工单动作表查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")

    elif args.type == 'history':
        if not args.work_order_id or not args.current_node_id:
            print("错误: 查询处理记录需要提供 --work-order-id 和 --current-node-id 参数")
            sys.exit(1)
        print(f"查询处理记录: workOrderId={args.work_order_id}, currentNodeId={args.current_node_id}")
        result = task_service.get_workorder_history(
            work_order_id=args.work_order_id,
            current_node_id=args.current_node_id,
            data_types=args.data_types
        )
        if result:
            print("\n处理记录查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")


if __name__ == "__main__":
    main()