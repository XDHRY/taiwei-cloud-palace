# taiwei_mcp.py — 素与太微云宫 Blender(G19, 端口9876) 的直连客户端
# 用法: python taiwei_mcp.py <script.py>   —— 脚本在 Blender 内执行, stdout 原样返回
#       python taiwei_mcp.py list          —— 列出 MCP 工具
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

VENV_EXE = r'E:/UserData/xdrhh/.openclaw/workspace/tools/.blender-mcp-venv/Scripts/mcp-for-blender.exe'

async def main():
    env = dict(os.environ, DISABLE_TELEMETRY='true', BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876')
    params = StdioServerParameters(command=VENV_EXE, env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=600)) as session:
            await session.initialize()
            if sys.argv[1] == 'list':
                result = await session.list_tools()
                print(json.dumps([t.name for t in result.tools], ensure_ascii=False))
                return
            code = Path(sys.argv[1]).read_text(encoding='utf-8-sig')
            result = await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': '太微云宫审美与逻辑审计(只读排查,不保存blend)'})
            for part in result.content:
                if part.type == 'text':
                    print(part.text)
            if result.isError:
                raise RuntimeError('MCP tool returned an error')

asyncio.run(main())
