"""
MCP Tools - Model Context Protocol 工具服务器
支持自定义工具注册和MCP协议通信
"""

import json
import os
import sys
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    input_schema: Dict = field(default_factory=dict)
    func: Optional[Callable] = None

    def to_mcp_format(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class MCPServer:
    """
    MCP工具服务器
    支持：工具注册、请求处理、资源管理
    """

    def __init__(self, name: str = "mcp-tools", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, Any] = {}
        self.prompts: Dict[str, Dict] = {}
        self.request_count = 0

    def register_tool(self, tool: MCPTool):
        """注册工具"""
        self.tools[tool.name] = tool

    def register_function(self, name: str, description: str, func: Callable, input_schema: Dict = None):
        """注册函数为工具"""
        tool = MCPTool(
            name=name,
            description=description,
            func=func,
            input_schema=input_schema or {"type": "object", "properties": {}}
        )
        self.register_tool(tool)

    def register_resource(self, uri: str, name: str, description: str, content: Any):
        """注册资源"""
        self.resources[uri] = {
            "uri": uri,
            "name": name,
            "description": description,
            "content": content
        }

    def register_prompt(self, name: str, description: str, template: str, arguments: List[Dict] = None):
        """注册提示模板"""
        self.prompts[name] = {
            "name": name,
            "description": description,
            "template": template,
            "arguments": arguments or []
        }

    def handle_request(self, request: Dict) -> Dict:
        """处理MCP请求"""
        self.request_count += 1
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
        }

        handler = handlers.get(method)
        if handler:
            try:
                result = handler(params)
                return {"jsonrpc": "2.0", "id": request_id, "result": result}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -1, "message": str(e)}}
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

    def _handle_initialize(self, params: Dict) -> Dict:
        """处理初始化请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }

    def _handle_tools_list(self, params: Dict) -> Dict:
        """列出所有工具"""
        return {
            "tools": [tool.to_mcp_format() for tool in self.tools.values()]
        }

    def _handle_tools_call(self, params: Dict) -> Dict:
        """调用工具"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        if not tool.func:
            raise ValueError(f"Tool not implemented: {tool_name}")

        result = tool.func(**arguments)

        return {
            "content": [
                {"type": "text", "text": str(result)}
            ]
        }

    def _handle_resources_list(self, params: Dict) -> Dict:
        """列出所有资源"""
        return {
            "resources": [
                {"uri": r["uri"], "name": r["name"], "description": r["description"]}
                for r in self.resources.values()
            ]
        }

    def _handle_resources_read(self, params: Dict) -> Dict:
        """读取资源"""
        uri = params.get("uri", "")
        resource = self.resources.get(uri)
        if not resource:
            raise ValueError(f"Resource not found: {uri}")

        return {
            "contents": [
                {"uri": uri, "text": str(resource["content"])}
            ]
        }

    def _handle_prompts_list(self, params: Dict) -> Dict:
        """列出所有提示"""
        return {
            "prompts": [
                {"name": p["name"], "description": p["description"], "arguments": p["arguments"]}
                for p in self.prompts.values()
            ]
        }

    def _handle_prompts_get(self, params: Dict) -> Dict:
        """获取提示"""
        name = params.get("name", "")
        prompt = self.prompts.get(name)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")

        arguments = params.get("arguments", {})
        template = prompt["template"]
        for key, value in arguments.items():
            template = template.replace(f"{{{key}}}", str(value))

        return {
            "messages": [
                {"role": "user", "content": {"type": "text", "text": template}}
            ]
        }

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "name": self.name,
            "version": self.version,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "prompts_count": len(self.prompts),
            "request_count": self.request_count
        }


# 内置工具示例
def get_current_time() -> str:
    return datetime.now().isoformat()

def calculate(expression: str) -> str:
    try:
        allowed = set('0123456789+-*/.() ')
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "Invalid expression"
    except Exception as e:
        return f"Error: {e}"

def json_format(text: str) -> str:
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"


def create_default_server(**kwargs) -> MCPServer:
    """创建带有默认工具的MCP服务器"""
    server = MCPServer(**kwargs)

    # 注册内置工具
    server.register_function(
        "get_time",
        "Get current datetime",
        get_current_time,
        {"type": "object", "properties": {}}
    )

    server.register_function(
        "calculate",
        "Calculate math expression",
        calculate,
        {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression"}
            },
            "required": ["expression"]
        }
    )

    server.register_function(
        "json_format",
        "Format JSON string",
        json_format,
        {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "JSON string"}
            },
            "required": ["text"]
        }
    )

    # 注册资源
    server.register_resource(
        "info://server",
        "Server Info",
        "MCP server information",
        {"name": server.name, "version": server.version}
    )

    # 注册提示
    server.register_prompt(
        "code_review",
        "Review code for issues",
        "Please review the following code:\n\n{code}",
        [{"name": "code", "description": "Code to review", "required": True}]
    )

    return server


# HTTP服务器
def run_http_server(server: MCPServer, host: str = "0.0.0.0", port: int = 3000):
    """运行HTTP服务器"""
    try:
        from flask import Flask, request, jsonify
        app = Flask(__name__)

        @app.route("/mcp", methods=["POST"])
        def handle_mcp():
            req = request.json
            response = server.handle_request(req)
            return jsonify(response)

        @app.route("/health", methods=["GET"])
        def health():
            return jsonify(server.get_stats())

        print(f"MCP Server running on http://{host}:{port}")
        app.run(host=host, port=port)

    except ImportError:
        print("Flask not installed. Install with: pip install flask")


if __name__ == "__main__":
    server = create_default_server()

    print("MCP Tools Server")
    print(f"Stats: {server.get_stats()}")
    print()

    # 测试请求
    test_requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_time", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "calculate", "arguments": {"expression": "2+3*4"}}},
    ]

    for req in test_requests:
        print(f"Request: {req['method']}")
        response = server.handle_request(req)
        print(f"Response: {json.dumps(response.get('result', response.get('error')), indent=2)}")
        print()

    # 启动HTTP服务器
    if "--http" in sys.argv:
        run_http_server(server)
