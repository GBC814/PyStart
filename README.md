# PyStart

PyStart 是一个专为初学者打造的 Python 代码编辑器，基于 PyQt6 和 Fluent Design 风格构建。

## 功能特性

- **现代 UI**: 使用 PyQt-Fluent-Widgets 构建的简洁美观的界面。
- **类 Thonny 布局**: 文件资源管理器（左侧）、代码编辑器（中间）、终端（底部）。
- **集成 Python**: 支持便携式 Python 运行环境集成。
- **解释器管理**: 轻松切换 Python 解释器或下载新的解释器。

## 安装说明

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用程序:
   ```bash
   python src/main.py
   ```

## 目录结构

- `src/`: 源代码
  - `ui/`: 用户界面组件
  - `core/`: 核心逻辑（解释器管理等）
  - `locale/`: 多语言翻译文件
- `assets/`: 图标和资源文件
- `runtime/`: 在此放置便携式 Python 发行版（例如 `python.exe`）

## 配置说明

设置存储在 `config.json` 文件中。您可以通过应用程序中的“设置”菜单更改解释器路径。
