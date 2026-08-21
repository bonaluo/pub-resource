# 📑 索引

仓库全部资源索引，按目录分类列出。

## 🔢 algorithm/ - 算法

- [算法.md](algorithm/算法.md) - LeetCode 刷题笔记（数组/双指针/链表等）

## 🤖 claude/ - Claude Code 资源

### ccr（Claude Code Router）

- [ccr/README.md](claude/ccr/README.md) - Claude Code Router 多 provider 切换与 bypass 权限配置指南

### hook

- [git-commit-validation/README.md](claude/hook/git-commit-validation/README.md) - Git Commit 消息格式校验 Hook（Conventional Commits 规范）

### statusline

- [windows/statusline.py](claude/statusline/windows/statusline.py) - Claude Code Windows 终端状态栏脚本

## 🌐 clash/ - Clash 配置

### override

- [js/19de45b7097.js](clash/override/js/19de45b7097.js) - JavaScript 覆写脚本（节点处理/分组重命名）
- [yaml/19de48f30be.yaml](clash/override/yaml/19de48f30be.yaml) - YAML 覆写配置

### ruleset

- [nojp.json](clash/ruleset/nojp.json) - 非日本分流域名规则集

## 🔧 hermes/ - Hermes Agent 资源

- [README.md](hermes/README.md) - Hermes 资源说明文档
- [install-hooks.sh](hermes/install-hooks.sh) - Gateway Hook 一键安装脚本

### hooks/

- [online-notify/](hermes/hooks/online-notify/) - Gateway 启动时向所有消息通道发送上线通知
  - [HOOK.yaml](hermes/hooks/online-notify/HOOK.yaml)
  - [handler.py](hermes/hooks/online-notify/handler.py)

## 🕸️ network/ - 网络代理

- [sing-box-guide.md](network/sing-box-guide.md) - Sing-box 代理配置完全指南（订阅转换/DNS 分流/WebUI/systemd 自启动）

## 👤 人物/ - 人物识别记录

### bilibili/

- [草原大雄狮/README.md](人物/bilibili/草原大雄狮/README.md) - 草原大雄狮
- [小马儿66/README.md](人物/bilibili/小马儿66/README.md) - 小马儿66
- [Ginana/README.md](人物/bilibili/Ginana/README.md) - Ginana（已识别）
- [魚寶_Yubo/README.md](人物/bilibili/魚寶_Yubo/README.md) - 魚寶_Yubo（已识别，B站路演随舞拍摄者）

## 💃 舞蹈/ - 翻跳视频收藏

- [RUDE/README.md](舞蹈/RUDE/README.md) - RUDE（翻跳/路演视频记录）
- [Kiss&Tell/README.md](舞蹈/Kiss&Tell/README.md) - Kiss&Tell（翻跳/路演视频记录）
- [一分一秒/README.md](舞蹈/一分一秒/README.md) - 一分一秒（翻跳/路演视频记录）
- [WhoIsShe/README.md](舞蹈/WhoIsShe/README.md) - Who Is She（翻跳/路演视频记录）

---

## 快速访问

### 一键安装 Hermes Hook

```bash
# 安装所有 hooks 到 ~/.hermes/hooks/
curl -sL https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh | bash

# 安装指定 hook
curl -sL https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh | bash -s -- online-notify

# 安装到自定义路径
curl -sL https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh | bash -s -- -d /custom/path

# 查看可用 hooks
curl -sL https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh | bash -s -- -l
```