import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yg_base import YgBase


class ResourceService(YgBase):
    def get_resource_change(self, time, supplier):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/resource/mes/vos"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        params = {
            'time': time,
            'supplier': supplier
        }
        result = self.call_api(url, method='get', headers=headers, params=params)
        if result:
            code = result.get('code')
            if code == 200:
                return result.get('data')
            else:
                print(f"查询资源变化失败: {result.get('msg')}")
        return None

    def get_supplier_resource(self, supplier_code, date_offset=7):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/homepage/supplier"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        params = {
            'supplierCode': supplier_code,
            'dateOffset': date_offset
        }
        result = self.call_api(url, method='get', headers=headers, params=params)
        if result:
            code = result.get('code')
            if code == 200:
                return result.get('data')
            else:
                print(f"查询云商资源失败: {result.get('msg')}")
        return None


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="资源查询脚本")
    parser.add_argument('--type', choices=['change', 'supplier'], default='change',
                        help='查询类型: change(资源变化), supplier(云商资源)')
    parser.add_argument('--time', help='时间范围（资源变化查询时必填，格式：YYYY-MM-DD--YYYY-MM-DD）')
    parser.add_argument('--supplier', help='供应商（资源变化查询时必填）')
    parser.add_argument('--supplier-code', '--supplierCode', help='供应商编码（云商资源查询时必填）')
    parser.add_argument('--date-offset', '--dateOffset', type=int, default=7,
                        help='日期偏移天数（云商资源查询时使用，默认7天）')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()

    resource_service = ResourceService()
    resource_service.get_token(app_username=args.app_username)

    if args.type == 'change':
        if not args.time or not args.supplier:
            print("错误: 查询资源变化需要提供 --time 和 --supplier 参数")
            return

        print(f"查询资源变化: time={args.time}, supplier={args.supplier}")
        result = resource_service.get_resource_change(args.time, args.supplier)
        if result:
            print("\n资源变化查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")
    else:
        if not args.supplier_code:
            print("错误: 查询云商资源需要提供 --supplier-code 参数")
            return

        print(f"查询云商资源: supplierCode={args.supplier_code}, dateOffset={args.date_offset}")
        result = resource_service.get_supplier_resource(args.supplier_code, args.date_offset)
        if result:
            print("\n云商资源查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")


if __name__ == "__main__":
    main()
