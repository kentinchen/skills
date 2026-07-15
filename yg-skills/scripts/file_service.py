import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yg_base import YgBase


class FileService(YgBase):
    def get_file_list(self, file_type, page_num=1, page_size=100):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/system/UploadFile/list"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        params = {
            'fileType': file_type,
            'pageNum': page_num,
            'pageSize': page_size
        }
        result = self.call_api(url, method='get', headers=headers, params=params)
        if result:
            code = result.get('code')
            if code == 200:
                return result
            else:
                print(f"查询文件列表失败: {result.get('msg')}")
        return None

    def get_file_resources(self, key, page_number=1, page_size=50, resource=7):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/forFlies"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'Cookie': f'Admin-Token={self.token}'
        }
        data = {
            'key': key,
            'pageNumber': page_number,
            'pageSize': page_size,
            'resource': resource
        }
        result = self.call_api(url, method='post', headers=headers, json_data=data)
        if result:
            code = result.get('code')
            if code == 200:
                return result
            else:
                print(f"查询文件资源失败: {result.get('msg')}")
        return None


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="文件查询脚本")
    parser.add_argument('--type', choices=['list', 'resources'], default='list', help='查询类型: list(文件列表), resources(文件资源)')
    parser.add_argument('--file-type', '--fileType', help='文件类型: 运维工具、业务模板、系统工具（文件列表查询时必填）')
    parser.add_argument('--key', help='资源键（文件资源查询时必填，示例：ResourcesUp）')
    parser.add_argument('--page-num', '--pageNum', type=int, default=1, help='页码')
    parser.add_argument('--page-size', '--pageSize', type=int, default=100, help='每页大小')
    parser.add_argument('--resource', type=int, default=7, help='资源类型（文件资源查询时使用，默认7）')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()

    file_service = FileService()
    file_service.get_token(app_username=args.app_username)

    if args.type == 'resources':
        if not args.key:
            print("错误: 查询文件资源需要提供 --key 参数")
            return

        print(f"查询文件资源: key={args.key}, pageNumber={args.page_num}, pageSize={args.page_size}, resource={args.resource}")
        result = file_service.get_file_resources(args.key, args.page_num, args.page_size, args.resource)
        if result:
            print("\n文件资源查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")
    else:
        if not args.file_type:
            print("错误: 查询文件列表需要提供 --file-type 参数")
            return

        print(f"查询文件列表: fileType={args.file_type}, pageNum={args.page_num}, pageSize={args.page_size}")
        result = file_service.get_file_list(args.file_type, args.page_num, args.page_size)
        if result:
            print("\n文件列表查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")


if __name__ == "__main__":
    main()