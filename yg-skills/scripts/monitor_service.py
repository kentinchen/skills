import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yg_base import YgBase


class MonitorService(YgBase):
    def get_every_day_access_total(self, supplier_code, time):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/cloud/monitoring/host/overview/everyDayAccessTotal"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        data = {
            'supplierCode': supplier_code,
            'time': time
        }
        result = self.call_api(url, method='post', headers=headers, json_data=data)
        if result:
            code = result.get('code')
            if code == 200:
                return result.get('data')
            else:
                print(f"查询每天统计失败: {result.get('msg')}")
        return None

    def get_monitoring_overview(self):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/cloud/monitoring/host/overview/getAccessDataSourceOverview"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        result = self.call_api(url, method='get', headers=headers)
        if result:
            code = result.get('code')
            if code == 200:
                return result
            else:
                print(f"查询监控概览失败: {result.get('msg')}")
        return None


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="监控查询脚本")
    parser.add_argument('--type', choices=['overview', 'daily'], default='overview', help='查询类型: overview(监控概览), daily(每天统计)')
    parser.add_argument('--supplier-code', '--supplierCode', help='供应商编码（每天统计查询时必填）')
    parser.add_argument('--time', help='日期（每天统计查询时必填，格式：YYYY-MM-DD）')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()

    monitor_service = MonitorService()
    monitor_service.get_token(app_username=args.app_username)

    if args.type == 'daily':
        if not args.supplier_code or not args.time:
            print("错误: 查询每天统计需要提供 --supplier-code 和 --time 参数")
            return

        print(f"查询每天统计: supplierCode={args.supplier_code}, time={args.time}")
        result = monitor_service.get_every_day_access_total(args.supplier_code, args.time)
        if result:
            print("\n每天统计查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")
    else:
        print("查询监控概览")
        result = monitor_service.get_monitoring_overview()
        if result:
            print("\n监控概览查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")


if __name__ == "__main__":
    main()