import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yg_base import YgBase


class CustomerService(YgBase):
    def get_user_profile(self):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/system/user/profile"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        result = self.call_api(url, method='get', headers=headers)
        if result:
            code = result.get('code')
            if code == 200:
                return result.get('data')
            else:
                print(f"查询用户画像失败: {result.get('msg')}")
        return None

    def get_dept_tree(self):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/system/dept/treeselect"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        result = self.call_api(url, method='get', headers=headers)
        if result:
            code = result.get('code')
            if code == 200:
                return result.get('data')
            else:
                print(f"查询部门树失败: {result.get('msg')}")
        return None


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="客户服务查询脚本")
    parser.add_argument('--type', choices=['profile', 'dept'], default='profile', help='查询类型: profile(用户画像), dept(部门树)')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()

    customer_service = CustomerService()
    customer_service.get_token(app_username=args.app_username)

    if args.type == 'dept':
        print("查询部门树")
        result = customer_service.get_dept_tree()
        if result:
            print("\n部门树查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")
    else:
        print("查询用户画像")
        result = customer_service.get_user_profile()
        if result:
            print("\n用户画像查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")


if __name__ == "__main__":
    main()