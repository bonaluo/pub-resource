# ccr (Claude Code Router) 配置指南

## 功能一：ccr code/preset 自动 bypass 权限

### 问题
`~/.bashrc` 中已有的 `alias claude='claude --dangerously-skip-permissions'` 只对原生 `claude` 命令生效，`ccr code` 和 `ccr <preset>` 不受 alias 影响，每次都需要手动加权限参数。

### 解决方案
在 `~/.bashrc` 中添加 bash 函数，拦截所有 ccr 调用：
- `ccr code` + preset 名（如 `ccr deepseek`、`ccr kimi`）→ 自动追加 `--dangerously-skip-permissions`
- `ccr start/stop/restart/model/preset/...` 等管理子命令 → 原样透传，不加 bypass

```bash
ccr() {
  local nocode=(start stop restart status statusline model preset install activate ui -v -h version help)
  local bypass=true
  for c in "${nocode[@]}"; do
    [[ "$1" = "$c" ]] && bypass=false && break
  done
  if $bypass; then
    command ccr "$1" --dangerously-skip-permissions "${@:2}"
  else
    command ccr "$@"
  fi
}
```

### 关键点
- 用黑名单而非白名单：未知子命令（包括用户自定义 preset 名）默认 bypass，ccr 自身会校验无效命令
- `command ccr` 防止递归调用自身

---

## 功能二：多 Provider/Preset 快速切换

### 目标
通过 preset 机制在不同 provider 和模型之间切换，例如：
- `ccr deepseek "prompt"` → deepseek-v4-pro
- `ccr kimi "prompt"` → kimi-k2.6

### 步骤

#### 1. 导出当前配置为 preset
```bash
ccr preset export deepseek --description "DeepSeek V4 Pro" --author "xfy" --tags "deepseek"
```
此命令会将 `~/.claude-code-router/config.json` 导出到 `~/.claude-code-router/presets/deepseek/manifest.json`。

#### 2. 创建第二个 preset（手动方式）
复制 deepseek preset 的 manifest.json，修改关键字段：
- `name` → 新 preset 名
- `Providers` → 只保留需要的 provider 和模型
- `Router` → 所有路由指向目标模型

**注意**：手动创建的 manifest 必须写入**真实 API key**，不能使用 `${CONFIG_API_KEY}` 占位符。`ccr preset export` 导出时会 sanitize 敏感字段，但 ccr 加载手动 preset 时不会反向解析占位符。

#### 3. ccai preset 的 Providers 建议只包含目标模型
Claude Code 的 `/model` 命令会列出所有已注册 provider 的全部模型。如果在 preset 的 Providers 中保留了其他模型（如 deepseek），/model 列表中会出现无关模型，容易造成混淆。建议每个 preset 的 Providers 只包含该 preset 实际需要的模型。

### 踩坑记录

1. **api_key 占位符问题**
   `ccr preset export` 会将 api_key 替换为 `${CONFIG_API_KEY}`，ccr 加载 export 出的 preset 时会自动从 config.json 注入真实值。但手动创建的 preset 不会触发此逻辑，必须写入明文 API key。

2. **新增/修改 preset 后需要重启**
   `ccr restart` — ccr server 启动时注册所有 preset 的命名空间路由（`/preset/<name>`），不重启不会生效。

3. **Preset Router 格式为 `provider,model`**
   Router 的值格式是 `provider名,模型名`，如 `newapi,nvidia:kimi-k2.6`。provider 名必须与 Providers 数组中某个 provider 的 `name` 字段匹配。

### 文件结构
```
~/.claude-code-router/
├── config.json                    # 主配置（default preset 的配置）
├── presets/
│   ├── deepseek/
│   │   └── manifest.json          # deepseek preset
│   └── kimi/
│       └── manifest.json          # kimi preset
```
