# 🔌 MCP Tools

Model Context Protocol工具服务器，支持自定义工具注册和MCP协议通信。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/MCP-Protocol-green" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

## ✨ 特性

- 🔧 工具注册和管理
- 📦 资源管理
- 📝 提示模板
- 🌐 HTTP服务器
- 📊 请求统计

## 🚀 快速开始

```bash
python server.py          # 测试模式
python server.py --http   # HTTP服务器模式
```

## 📖 使用

```python
from server import MCPServer, create_default_server

# 创建服务器
server = create_default_server()

# 注册自定义工具
server.register_function(
    "search",
    "Search the web",
    lambda q: f"Results for: {q}",
    {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
)

# 处理请求
response = server.handle_request({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {"name": "search", "arguments": {"query": "Python"}}
})
```

## 🔌 MCP协议支持

| 方法 | 说明 |
|------|------|
| `initialize` | 初始化连接 |
| `tools/list` | 列出所有工具 |
| `tools/call` | 调用工具 |
| `resources/list` | 列出资源 |
| `resources/read` | 读取资源 |
| `prompts/list` | 列出提示 |
| `prompts/get` | 获取提示 |

## 📁 项目结构

```
mcp-tools/
├── server.py      # MCP服务器核心
└── README.md
```

## 📄 许可证

MIT License
