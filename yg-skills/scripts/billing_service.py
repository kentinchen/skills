import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yg_base import YgBase


class BillingService(YgBase):
    def get_billing_coefficient(self, cloud_supplier, time_tag, page_num=1, page_size=10):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/cloud/disk/billing"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        params = {
            'pageNum': page_num,
            'pageSize': page_size,
            'cloudSupplier': cloud_supplier,
            'timeTag': time_tag
        }
        result = self.call_api(url, method='get', headers=headers, params=params)
        if result:
            code = result.get('code')
            if code == 200:
                return result
            else:
                print(f"查询账单系数失败: {result.get('msg')}")
        return None


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="账单查询脚本")
    parser.add_argument('--cloud-supplier', '--cloudSupplier', required=True, help='云供应商编码（示例：chengyun）')
    parser.add_argument('--time-tag', '--timeTag', required=True, help='时间标签（格式：YYYY-MM-DD）')
    parser.add_argument('--page-num', '--pageNum', type=int, default=1, help='页码')
    parser.add_argument('--page-size', '--pageSize', type=int, default=10, help='每页大小')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()

    billing_service = BillingService()
    billing_service.get_token(app_username=args.app_username)

    print(
        f"查询账单系数: cloudSupplier={args.cloud_supplier}, timeTag={args.time_tag}, pageNum={args.page_num}, pageSize={args.page_size}")
    result = billing_service.get_billing_coefficient(args.cloud_supplier, args.time_tag, args.page_num, args.page_size)
    if result:
        print("\n账单系数查询结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n查询失败")


if __name__ == "__main__":
    main()
