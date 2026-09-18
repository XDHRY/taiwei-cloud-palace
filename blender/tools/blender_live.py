# -*- coding: utf-8 -*-
"""Blender Live 交互客户端。

通过本地 TCP Socket（localhost:9876）与 Blender 内运行的 MCP 插件通信。
支持：
- 查询场景/对象信息
- 查询当前用户在 Blender 视口中鼠标点选/选中的对象（active_object / selected_objects）
- 对选中的组件执行精确移动、缩放、旋转、更换材质、调整着色器参数
- 在 Blender 主线程执行任意 Python 代码并返回实时结果
"""
import socket
import json
import sys
import argparse

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
BUFFER_SIZE = 8192
TIMEOUT = 240.0

def send_blender_command(command_type, params=None, host=DEFAULT_HOST, port=DEFAULT_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    try:
        sock.connect((host, port))
    except Exception as e:
        return {"status": "error", "message": f"Cannot connect to Blender on {host}:{port}: {e}"}

    payload = {
        "type": command_type,
        "params": params or {}
    }
    
    try:
        sock.sendall(json.dumps(payload).encode("utf-8"))
        chunks = []
        while True:
            chunk = sock.recv(BUFFER_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
            data = b"".join(chunks)
            try:
                res = json.loads(data.decode("utf-8"))
                return res
            except json.JSONDecodeError:
                continue
        if chunks:
            return json.loads(b"".join(chunks).decode("utf-8"))
        return {"status": "error", "message": "Empty response from Blender"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        sock.close()

def execute_code(code_str, host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_blender_command("execute_code", {"code": code_str}, host, port)

def get_selected_object(host=DEFAULT_HOST, port=DEFAULT_PORT):
    code = """
import bpy, json
obj = bpy.context.active_object
sel = [o.name for o in bpy.context.selected_objects]
if not obj:
    print(json.dumps({'has_active': False, 'selected': sel}))
else:
    bb = [list(c) for c in obj.bound_box]
    mats = [m.name for m in obj.data.materials] if hasattr(obj.data, 'materials') else []
    print(json.dumps({
        'has_active': True,
        'name': obj.name,
        'type': obj.type,
        'location': [round(c, 4) for c in obj.location],
        'rotation_euler': [round(c, 4) for c in obj.rotation_euler],
        'scale': [round(c, 4) for c in obj.scale],
        'dimensions': [round(c, 4) for c in obj.dimensions],
        'materials': mats,
        'selected_all': sel
    }))
"""
    return execute_code(code, host, port)

def modify_selected(loc=None, rot=None, scale=None, material=None, host=DEFAULT_HOST, port=DEFAULT_PORT):
    stmts = ["import bpy, json", "obj = bpy.context.active_object", "if not obj: raise Exception('No active object selected in Blender!')"]
    if loc is not None:
        stmts.append(f"obj.location = ({loc[0]}, {loc[1]}, {loc[2]})")
    if rot is not None:
        stmts.append(f"obj.rotation_euler = ({rot[0]}, {rot[1]}, {rot[2]})")
    if scale is not None:
        stmts.append(f"obj.scale = ({scale[0]}, {scale[1]}, {scale[2]})")
    if material is not None:
        stmts.append(f"mat = bpy.data.materials.get('{material}')")
        stmts.append("if mat and hasattr(obj.data, 'materials'):")
        stmts.append("    if len(obj.data.materials) > 0: obj.data.materials[0] = mat")
        stmts.append("    else: obj.data.materials.append(mat)")
    stmts.append("print(json.dumps({'modified': obj.name, 'new_location': list(obj.location), 'new_scale': list(obj.scale)}))")
    return execute_code("\n".join(stmts), host, port)

def main():
    parser = argparse.ArgumentParser(description="Blender Live CLI Bridge")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--selected", action="store_true", help="Get currently selected/active object info")
    parser.add_argument("--exec", type=str, help="Execute python code in Blender")
    parser.add_argument("--move", nargs=3, type=float, metavar=("X", "Y", "Z"), help="Move active object to (X, Y, Z)")
    parser.add_argument("--set-mat", type=str, help="Set material of active object")

    args = parser.parse_args()

    if args.selected:
        res = get_selected_object(args.host, args.port)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.exec:
        res = execute_code(args.exec, args.host, args.port)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.move:
        res = modify_selected(loc=args.move, host=args.host, port=args.port)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.set_mat:
        res = modify_selected(material=args.set_mat, host=args.host, port=args.port)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        res = send_blender_command("get_scene_info", host=args.host, port=args.port)
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
