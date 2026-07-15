import requests
import argparse
import json
import yaml
import os

def get_config_path():
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".dddd-ocr")
    return os.path.join(config_dir, "config.yml")

def read_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and isinstance(config, dict):
                    return config.get('base_url'), config.get('proxy')
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    return None, None

def save_config(base_url, proxy=None):
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    config = {
        'base_url': base_url,
        'proxy': proxy
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"配置已保存到: {config_path}")
    except Exception as e:
        print(f"保存配置文件失败: {e}")

def get_default_server():
    base_url, proxy = read_config()
    if base_url:
        print(f"使用保存的服务地址: {base_url}")
        return base_url, proxy
    else:
        try:
            base_url = input("请输入ddddocr服务地址: ")
            if not base_url.strip():
                base_url = "http://localhost:8000"
                print(f"使用默认地址: {base_url}")
            proxy_input = input("请输入代理地址（可选，按回车跳过）: ")
            proxy = proxy_input.strip() if proxy_input.strip() else None
            save_config(base_url, proxy)
            return base_url, proxy
        except EOFError:
            return "http://localhost:8000", None

DEFAULT_SERVER, DEFAULT_PROXY = get_default_server()

def ocr(image_path, probability=False, charsets=None, png_fix=False, server=DEFAULT_SERVER, proxy=DEFAULT_PROXY):
    url = f"{server}/ocr"
    
    files = {}
    data = {
        "probability": str(probability),
        "png_fix": str(png_fix)
    }
    
    if charsets:
        data["charsets"] = charsets
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        with open(image_path, "rb") as f:
            files["file"] = f
            response = requests.post(url, files=files, data=data, proxies=proxies)
            return response.json()
    except FileNotFoundError:
        return {"code": 400, "message": f"File not found: {image_path}", "data": None}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}

def slide_match(target_path, background_path, simple_target=False, server=DEFAULT_SERVER, proxy=DEFAULT_PROXY):
    url = f"{server}/slide_match"
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        with open(target_path, "rb") as tf, open(background_path, "rb") as bf:
            files = {
                "target_file": tf,
                "background_file": bf
            }
            data = {
                "simple_target": str(simple_target)
            }
            response = requests.post(url, files=files, data=data, proxies=proxies)
            return response.json()
    except FileNotFoundError as e:
        return {"code": 400, "message": f"File not found: {e.filename}", "data": None}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}

def detection(image_path, server=DEFAULT_SERVER, proxy=DEFAULT_PROXY):
    url = f"{server}/detection"
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files, proxies=proxies)
            return response.json()
    except FileNotFoundError:
        return {"code": 400, "message": f"File not found: {image_path}", "data": None}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}

def main():
    parser = argparse.ArgumentParser(description="ddddocr-fastapi 客户端")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    ocr_parser = subparsers.add_parser("ocr", help="OCR识别")
    ocr_parser.add_argument("image_path", help="图片文件路径")
    ocr_parser.add_argument("--probability", action="store_true", help="返回识别概率")
    ocr_parser.add_argument("--charsets", help="指定字符集")
    ocr_parser.add_argument("--png_fix", action="store_true", help="进行PNG修复")
    ocr_parser.add_argument("--server", help=f"服务地址，默认: {DEFAULT_SERVER}")
    ocr_parser.add_argument("--proxy", help="代理地址")
    
    slide_parser = subparsers.add_parser("slide_match", help="滑动验证码匹配")
    slide_parser.add_argument("target_path", help="目标滑块图片路径")
    slide_parser.add_argument("background_path", help="背景图片路径")
    slide_parser.add_argument("--simple_target", action="store_true", help="使用简单目标模式")
    slide_parser.add_argument("--server", help=f"服务地址，默认: {DEFAULT_SERVER}")
    slide_parser.add_argument("--proxy", help="代理地址")
    
    det_parser = subparsers.add_parser("detection", help="目标检测")
    det_parser.add_argument("image_path", help="图片文件路径")
    det_parser.add_argument("--server", help=f"服务地址，默认: {DEFAULT_SERVER}")
    det_parser.add_argument("--proxy", help="代理地址")
    
    args = parser.parse_args()
    
    server = args.server if args.server else DEFAULT_SERVER
    proxy = args.proxy if args.proxy else DEFAULT_PROXY
    
    if args.command in ["ocr", "slide_match", "detection"]:
        if args.server or args.proxy:
            save_config(server, proxy)
    
    if args.command == "ocr":
        result = ocr(args.image_path, args.probability, args.charsets, args.png_fix, server, proxy)
    elif args.command == "slide_match":
        result = slide_match(args.target_path, args.background_path, args.simple_target, server, proxy)
    elif args.command == "detection":
        result = detection(args.image_path, server, proxy)
    else:
        parser.print_help()
        return
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()