import requests
import argparse
import json

DEFAULT_SERVER = "http://localhost:8000"

def ocr(image_path, probability=False, charsets=None, png_fix=False, server=DEFAULT_SERVER):
    url = f"{server}/ocr"
    
    files = {}
    data = {
        "probability": str(probability),
        "png_fix": str(png_fix)
    }
    
    if charsets:
        data["charsets"] = charsets
    
    try:
        with open(image_path, "rb") as f:
            files["file"] = f
            response = requests.post(url, files=files, data=data)
            return response.json()
    except FileNotFoundError:
        return {"code": 400, "message": f"File not found: {image_path}", "data": None}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}

def slide_match(target_path, background_path, simple_target=False, server=DEFAULT_SERVER):
    url = f"{server}/slide_match"
    
    try:
        with open(target_path, "rb") as tf, open(background_path, "rb") as bf:
            files = {
                "target_file": tf,
                "background_file": bf
            }
            data = {
                "simple_target": str(simple_target)
            }
            response = requests.post(url, files=files, data=data)
            return response.json()
    except FileNotFoundError as e:
        return {"code": 400, "message": f"File not found: {e.filename}", "data": None}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}

def detection(image_path, server=DEFAULT_SERVER):
    url = f"{server}/detection"
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files)
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
    ocr_parser.add_argument("--server", default=DEFAULT_SERVER, help="服务地址")
    
    slide_parser = subparsers.add_parser("slide_match", help="滑动验证码匹配")
    slide_parser.add_argument("target_path", help="目标滑块图片路径")
    slide_parser.add_argument("background_path", help="背景图片路径")
    slide_parser.add_argument("--simple_target", action="store_true", help="使用简单目标模式")
    slide_parser.add_argument("--server", default=DEFAULT_SERVER, help="服务地址")
    
    det_parser = subparsers.add_parser("detection", help="目标检测")
    det_parser.add_argument("image_path", help="图片文件路径")
    det_parser.add_argument("--server", default=DEFAULT_SERVER, help="服务地址")
    
    args = parser.parse_args()
    
    if args.command == "ocr":
        result = ocr(args.image_path, args.probability, args.charsets, args.png_fix, args.server)
    elif args.command == "slide_match":
        result = slide_match(args.target_path, args.background_path, args.simple_target, args.server)
    elif args.command == "detection":
        result = detection(args.image_path, args.server)
    else:
        parser.print_help()
        return
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()