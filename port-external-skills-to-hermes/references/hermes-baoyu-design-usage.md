# Hermes 桌面 GUI 环境下使用 baoyu-design 的注意事项

> 记录自实际会话经验。适用于 Windows 10 + Hermes 桌面 GUI 环境。

## 环境限制

### 1. 浏览器工具不可用
- `browser_navigate` / `browser_vision` 等工具会报错：`Chrome not found`
- 无法通过浏览器工具预览设计成果
- **替代方案**：告诉用户直接双击 HTML 文件用系统浏览器打开

### 2. HTTP 服务器启动受阻
- `terminal` 工具禁止 shell 后台进程（`&` 或 `bg=true`）
- `python -m http.server` 的 `background=true` 模式进程会立即退出（exit code 49）
- 无法启动本地 HTTP 服务器用于 `gen-pptx` 导出
- **替代方案**：
  - 浏览器直接打开 `file://` 路径（deck-stage.js 支持 file 协议）
  - 打印为 PDF（Ctrl+P，横向，启用背景图形）
  - 在另一台机器上启动服务器后运行 gen-pptx

### 3. `execute_code` 的隔离性
- `execute_code` 运行在临时沙箱目录
- 文件写入不会持久化到宿主文件系统
- **规则**：持久化文件必须用 `write_file` 或 `terminal` 工具

## 推荐工作流程

### 设计阶段
1. 读取 `system-prompt.md` 和对应 harness 的参考文档
2. 向用户提出澄清问题（用普通消息，非 `clarify` 工具）
3. 用 `write_file` 创建项目目录和 HTML 文件
4. 告诉用户文件路径，让他们用浏览器直接打开查看

### 导出阶段（PPTX）
1. 首选：浏览器打印 → 另存为 PDF（保留所有样式）
2. 次选：截图 + 插入 PowerPoint 背景
3. 最后：如果用户有另一台可启动 HTTP 服务器的机器，提供 gen-pptx 命令

## 文件交付路径

Windows 默认路径：
```
C:\Users\<username>\designs\<project-name>\
```

## 网络下载技巧

GitHub raw 访问不稳定时：
1. 首选：`curl -L <repo>/zipball/main -o repo.zip`（ZIP 归档）
2. 次选：GitHub API 递归树获取文件列表
3. 避免：逐个下载 raw.githubusercontent.com 文件（容易 SSL 中断）
