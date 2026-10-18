# -*- coding: utf-8 -*-
"""极空间NAS巡检文件上传（巡检记录/签到表/交班表）。

用法:
  python upload_xunjian.py --file <图片路径> [--type xunjian|qiandao|jiaoban] [--time "YYYY-MM-DD HH:MM:SS"]
  python upload_xunjian.py --latest [--wait 60] [--type xunjian]        # 自动取Trae附件目录最新图片
  python upload_xunjian.py --list 202610                                # 查看目录文件及北京时间

说明:
  - 手机Trae App发的图片会同步到 %USERPROFILE%\\.trae-cn\\attachments（可能延迟），--latest 自动取最新图片。
  - 拍摄时间优先级: --time 参数 > 图片EXIF > 文件名(IMG/MVIMG_YYYYMMDD_HHMMSS) > 文件修改时间。
  - 上传时按北京时间换算UTC时间戳写入 crtime/modify_time，并写EXIF时间，页面显示即北京时间。
  - 目标文件已存在时会报错提示（需先删除旧文件，覆盖上传不会更新修改时间）。
"""
import argparse
import calendar
import datetime
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from urllib.parse import quote, unquote

from PIL import Image

BASE = "/sata1/public/阿里云/成都城运云"
ATTACH_DIR = os.path.join(os.path.expanduser("~"), ".trae-cn", "attachments")

# 类别 -> (目标目录模板, 文件名模板)  {} 处: YYYYMM / YYYYMMDD / HH
CATEGORIES = {
    "xunjian": (BASE + "/巡检日报/{YYYYMM}", "城运云平台系统日常巡检记录{YYYYMMDD}-{HH}.jpg"),
    "qiandao": (BASE + "/签到表", "签到表{YYYYMMDD}.jpg"),
    "jiaoban": (BASE + "/每日交接班记录及事件记录", "交班表{YYYYMMDD}.jpg"),
}


def load_auth():
    cookie_file = os.path.join(os.path.expanduser("~"), ".jkj", "cookie.txt")
    with open(cookie_file, "r", encoding="utf-8") as f:
        cookie_str = f.read().strip()

    def cv(k):
        for p in cookie_str.split(";"):
            p = p.strip()
            if p.startswith(k + "="):
                return unquote(p.split("=", 1)[1])
        return ""

    token, device_id = cv("zenithtoken"), cv("device_id")
    nas_id, username = cv("nas_id"), cv("username")
    userid, version = cv("userid"), cv("version")
    cookie_send = (f"webagent=v2; nas_id={nas_id}; zenithtoken={token}; username={username};"
                   f" userid={userid}; plat=web; app=file; device=PC; version={version}; device_id={device_id}")
    return token, nas_id, version, device_id, cookie_send


def bj_to_unix(dt_bj):
    """北京时间 datetime -> UTC Unix 时间戳"""
    return calendar.timegm((dt_bj - datetime.timedelta(hours=8)).timetuple())


def detect_time(src, time_arg):
    if time_arg:
        return datetime.datetime.strptime(time_arg, "%Y-%m-%d %H:%M:%S")
    # EXIF
    try:
        img = Image.open(src)
        exif = img.getexif()
        for tag in (0x9003, 0x0132):
            v = exif.get(tag)
            if v:
                s = str(v).strip()
                m = re.match(r"(\d{4})[:\-](\d{2})[:\-](\d{2})[ T](\d{2}):(\d{2}):(\d{2})", s)
                if m:
                    img.close()
                    return datetime.datetime(*map(int, m.groups()))
        img.close()
    except Exception:
        pass
    # 文件名 IMG_20261014_010113 / MVIMG_20261013_210155
    m = re.search(r"(?:MVIMG|IMG)_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", os.path.basename(src))
    if m:
        return datetime.datetime(*map(int, m.groups()))
    # 文件修改时间（按本地时区）
    return datetime.datetime.fromtimestamp(os.path.getmtime(src))


def pick_latest(wait_sec, min_size=30000):
    """从Trae附件目录取最新图片；--wait 秒内轮询等待新文件出现"""
    def snap():
        if not os.path.isdir(ATTACH_DIR):
            return {}
        return {f: os.path.getmtime(os.path.join(ATTACH_DIR, f))
                for f in os.listdir(ATTACH_DIR)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))}

    before = snap()
    deadline = time.time() + wait_sec
    while True:
        cur = snap()
        new = {f for f, t in cur.items() if f not in before and t > time.time() - 86400}
        cand = new if new else set(cur)
        cand = [f for f in cand if os.path.getsize(os.path.join(ATTACH_DIR, f)) >= min_size]
        if cand:
            cand.sort(key=lambda f: os.path.getmtime(os.path.join(ATTACH_DIR, f)), reverse=True)
            return os.path.join(ATTACH_DIR, cand[0]), bool(new)
        if time.time() >= deadline:
            return None, False
        time.sleep(3)


def list_dir(sub, auth):
    token, nas_id, version, device_id, cookie_send = auth
    body = ("path=" + quote(BASE + sub, safe="") +
            "&start=0&num=1000&sortby=mtime&ftype=0&app=file&order=desc&show_hidden=0&dup=0")
    r = subprocess.run([
        "curl.exe", "-s", "-X", "POST",
        "https://www.zconnect.cn/v2/file/list/stream?remote_port=8050&webagent=v2",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-H", f"token: {token}", "-H", "plat: web", "-H", f"nasid: {nas_id}",
        "-H", f"version: {version}", "-H", f"device_id: {device_id}",
        "-H", f"Cookie: {cookie_send}", "--data", body, "--max-time", "30",
    ], capture_output=True, text=True, encoding="utf-8")
    files = []
    for m in re.finditer(r'\{[^{}]*?"n":"[^"]*"[^{}]*?\}', r.stdout):
        try:
            d = json.loads(m.group(0))
        except Exception:
            continue
        if not d.get("di"):
            files.append(d)
    return files


def upload(src, cat, dt_bj, auth, dry=False):
    token, nas_id, version, device_id, cookie_send = auth
    name_tpl, dir_tpl = CATEGORIES[cat][1], CATEGORIES[cat][0]
    fields = {
        "YYYYMM": dt_bj.strftime("%Y%m"),
        "YYYYMMDD": dt_bj.strftime("%Y%m%d"),
        "HH": dt_bj.strftime("%H"),
    }
    target_name = name_tpl.format(**fields)
    target_dir = dir_tpl.format(**fields)
    target_path = f"{target_dir}/{target_name}"
    unix_time = bj_to_unix(dt_bj)
    exif_str = dt_bj.strftime("%Y:%m:%d %H:%M:%S")
    print(f"类别: {cat}\n目标: {target_path}\n北京时间: {exif_str}  Unix: {unix_time}")
    if dry:
        print("(dry-run 未上传)")
        return 0

    # 检查是否已存在
    for d in list_dir(target_dir[len(BASE):], auth):
        if d.get("n") == target_name:
            print(f"错误: 目标文件已存在 (大小{d.get('s')}B)。覆盖上传不会更新修改时间，请先删除旧文件再传。")
            return 2

    # 写EXIF
    tmp = os.path.join(os.path.expandvars("%TEMP%"), f"xj_up_{int(time.time())}.jpg")
    img = Image.open(src)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")  # PNG等转JPEG
    exif = img.getexif()
    if exif is None:
        exif = Image.Exif()
    for tag in (0x0132, 0x9003, 0x9004):
        exif[tag] = exif_str
    try:
        img.save(tmp, "JPEG", quality=95, exif=exif.tobytes())
    except Exception:
        img.save(tmp, "JPEG", quality=95)
    img.close()
    file_size = os.path.getsize(tmp)

    with open(tmp, "rb") as f:
        uuid = hashlib.sha1(f.read()).hexdigest()
    rnd = f"{int(time.time() * 1000)}_{random.randint(0, 9999)}"
    r = subprocess.run([
        "curl.exe", "-s", "-X", "POST",
        f"https://www.zconnect.cn/v2/file/upload?remote_port=8050&rnd={rnd}&webagent=v2",
        "-H", "Content-Type: application/octet-stream",
        "-H", f"path: {quote(target_path)}",
        "-H", f"size: {file_size}",
        "-H", f"uuid: {uuid}",
        "-H", "seek: 0",
        "-H", f"crtime: {unix_time}",
        "-H", f"modify_time: {unix_time}",
        "-H", "rename: 0",
        "-H", f"token: {token}", "-H", "plat: web", "-H", f"nasid: {nas_id}",
        "-H", f"version: {version}", "-H", f"device_id: {device_id}",
        "-H", "device: PC (Chrome/151.0.0.0)", "-H", "remote-port: 8050",
        "-H", "request-purpose: 4", "-H", "device-type: web", "-H", "split: 1",
        "-H", f"Cookie: {cookie_send}",
        "--data-binary", f"@{tmp}", "-w", "\nHTTP_CODE:%{http_code}", "--max-time", "180",
    ], capture_output=True, text=True, encoding="utf-8")
    try:
        os.remove(tmp)
    except OSError:
        pass
    ok = "HTTP_CODE:200" in r.stdout and '"code":"0"' in r.stdout.replace('"code":0', '"code":"0"') or "HTTP_CODE:200" in r.stdout
    print("上传响应:", r.stdout[-200:].replace("\n", " "))

    # 核对
    if ok:
        time.sleep(1)
        for d in list_dir(target_dir[len(BASE):], auth):
            if d.get("n") == target_name:
                mt = int(d.get("mt", 0))
                shown = datetime.datetime.fromtimestamp(mt, datetime.timezone.utc) + datetime.timedelta(hours=8)
                print(f"核对: {target_name} 大小={d.get('s')}B 修改时间(北京)={shown:%Y-%m-%d %H:%M}")
                if abs(mt - unix_time) <= 120:
                    print("SUCCESS: 时间正确")
                    return 0
                print("警告: 页面修改时间与预期不符")
                return 3
        print("警告: 上传返回200但列表未找到文件")
        return 3
    print("FAIL")
    return 1


def main():
    ap = argparse.ArgumentParser(description="极空间巡检文件上传")
    ap.add_argument("--file", help="本地图片路径")
    ap.add_argument("--latest", action="store_true", help="自动取Trae附件目录最新图片(手机端发的图会同步到这里)")
    ap.add_argument("--wait", type=int, default=0, help="配合--latest: 等待新文件出现的秒数")
    ap.add_argument("--type", dest="cat", choices=list(CATEGORIES), default="xunjian",
                    help="类别: xunjian巡检记录/qiandao签到表/jiaoban交班表 (默认xunjian)")
    ap.add_argument("--time", help='拍摄时间(北京时间) "YYYY-MM-DD HH:MM:SS"，缺省自动识别')
    ap.add_argument("--dry", action="store_true", help="只解析不上传")
    ap.add_argument("--list", dest="ls", metavar="子目录", help='列目录，如 /巡检日报/202610')
    args = ap.parse_args()

    auth = load_auth()
    if args.ls:
        for d in list_dir(args.ls, auth):
            mt = int(d.get("mt", 0))
            bj = datetime.datetime.fromtimestamp(mt, datetime.timezone.utc) + datetime.timedelta(hours=8)
            print(f'{d["n"]}  {d.get("s")}B  {bj:%Y-%m-%d %H:%M}')
        return 0

    src = args.file
    if args.latest:
        found, is_new = pick_latest(args.wait)
        if not found:
            print(f"附件目录 {ATTACH_DIR} 中没有找到图片文件（等待{args.wait}秒超时）")
            return 2
        print(f"附件目录最新图片: {os.path.basename(found)}" + ("（新到达）" if is_new else ""))
        src = found
    if not src or not os.path.exists(src):
        print("错误: 需要 --file 或 --latest")
        return 2

    dt_bj = detect_time(src, args.time)
    print(f"源文件: {src}\n识别时间(北京): {dt_bj}")
    return upload(src, args.cat, dt_bj, auth, dry=args.dry)


if __name__ == "__main__":
    sys.exit(main())
