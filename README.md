# 📦 pub-resource

公共资源仓库，存放各类配置文件、开发工具资源和收藏记录。

## 📑 索引

所有文件的详细索引见 [index.md](index.md)。

## 目录结构

```
pub-resource/
├── algorithm/           # 算法刷题笔记
├── claude/              # Claude Code 资源
│   ├── ccr/             #   Claude Code Router 多 provider 配置
│   ├── hook/            #   Git Commit 消息格式校验 hook
│   └── statusline/      #   终端状态栏美化
├── clash/               # Clash 代理配置
│   ├── override/        #   JS/YAML 覆写脚本与配置
│   └── ruleset/         #   自定义规则集
├── hermes/              # Hermes Agent 资源
│   ├── hooks/           #   Gateway 事件钩子
│   └── install-hooks.sh #   Hook 一键安装脚本
├── network/             # 网络代理配置指南
├── 人物/                 # B站人物识别记录
│   └── bilibili/
└── 舞蹈/                 # K-pop 翻跳/路演视频收藏
```

## 快速使用

### 安装 Hermes Hook

```bash
# 一键安装所有 hooks
bash <(curl -sL https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh)

# 安装指定 hook
bash <(curl -sL https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh) -- online-notify
```

### 查看可用 hooks

```bash
bash <(curl -sL https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh) -- -l
```

## 分类说明

| 分类 | 说明 | 路径 |
|------|------|------|
| 🔢 算法 | LeetCode 刷题笔记 | `algorithm/` |
| 🤖 Claude | Claude Code Router、Hook、状态栏 | `claude/` |
| 🌐 Clash | Clash 覆写配置与自定义规则集 | `clash/` |
| 🔧 Hermes | Hermes Agent Gateway Hooks 及安装工具 | `hermes/` |
| 🕸️ Network | Sing-box 代理配置指南 | `network/` |
| 👤 人物 | B站人物识别记录 | `人物/` |
| 💃 舞蹈 | K-pop 翻跳/路演视频收藏 | `舞蹈/` |
