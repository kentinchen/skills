import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yg_base import YgBase


class NoticeService(YgBase):
    def get_notice_list(self, page_num=1, page_size=5, notice_type=1):
        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/noToken/notice/mylist"
        params = {
            'pageNum': page_num,
            'pageSize': page_size,
            'noticeType': notice_type
        }
        headers = {
            'Content-Type': 'application/json'
        }
        result = self.call_api(url, method='get', headers=headers, params=params)
        if result:
            code = result.get('code')
            if code == 200:
                return result.get('msg')
            else:
                print(f"查询通知清单失败: {result.get('msg')}")
        return None

    def get_notice_detail(self, notice_id):
        if not self.token:
            print("错误: 未获取到token，请先调用get_token()")
            return None

        app_url = self.get_app_url()
        url = f"{app_url}/prod-api/system/notice/noToken/{notice_id}"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'Admin-Token={self.token}'
        }
        result = self.call_api(url, method='get', headers=headers)
        if result:
            code = result.get('code')
            if code == 200:
                return result.get('data')
            else:
                print(f"查询通知详情失败: {result.get('msg')}")
        return None


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="通知查询脚本")
    parser.add_argument('--page-num', '--pageNum', type=int, default=1, help='页码')
    parser.add_argument('--page-size', '--pageSize', type=int, default=5, help='每页大小')
    parser.add_argument('--notice-type', '--noticeType', type=int, default=1, help='通知类型: 普通公告1、安全情报2、资源变化')
    parser.add_argument('--notice-id', '--noticeId', help='通知ID（查询通知详情时使用）')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()

    notice_list = NoticeService()
    notice_list.get_token(app_username=args.app_username)

    if args.notice_id:
        print(f"查询通知详情: noticeId={args.notice_id}")
        result = notice_list.get_notice_detail(args.notice_id)
        if result:
            print("\n通知详情查询结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n查询失败")
    else:
        print(f"查询通知清单: pageNum={args.page_num}, pageSize={args.page_size}, noticeType={args.notice_type}")
        result = notice_list.get_notice_list(args.page_num, args.page_size, args.notice_type)
        if result:
            print("\n通知清单查询结果:")
            print(result)
        else:
            print("\n查询失败")


if __name__ == "__main__":
    main()
