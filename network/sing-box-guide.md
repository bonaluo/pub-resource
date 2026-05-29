# Sing-box 代理配置完全指南

> 从零开始部署 sing-box 代理，含 Clash 订阅转换、DNS 分流、WebUI 面板、systemd 自启动。

## 目录

- [1. 安装](#1-安装)
- [2. Clash 订阅转换](#2-clash-订阅转换)
- [3. 最小可用配置](#3-最小可用配置)
- [4. DNS 配置](#4-dns-配置)
- [5. 路由规则](#5-路由规则)
- [6. Clash API + WebUI 面板](#6-clash-api--webui-面板)
- [7. systemd 自启动](#7-systemd-自启动)
- [8. Docker 容器走代理](#8-docker-容器走代理)
- [9. 常见问题](#9-常见问题)

---

## 1. 安装

### 官方脚本（推荐）

```bash
curl -fsSL https://sing-box.app/install.sh | sh
```

网络慢时加代理：

```bash
export https_proxy=http://<your-proxy> http_proxy=http://<your-proxy>
curl -fsSL https://sing-box.app/install.sh | sh
```

### APT 仓库（Debian/Ubuntu）

```bash
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://sing-box.app/gpg.key -o /etc/apt/keyrings/sagernet.asc
sudo chmod a+r /etc/apt/keyrings/sagernet.asc
echo 'Types: deb
URIs: https://deb.sagernet.org/
Suites: *
Components: *
Enabled: yes
Signed-By: /etc/apt/keyrings/sagernet.asc' | sudo tee /etc/apt/sources.list.d/sagernet.sources
sudo apt-get update && sudo apt-get install sing-box
```

验证安装：

```bash
sing-box version
```

---

## 2. Clash 订阅转换

Clash 订阅通常是一个 base64 编码的文本，每行一个节点链接（`vmess://`、`ss://` 等）。

### 2.1 获取并解码

```bash
curl -sL "https://your-subscription-url?token=YOUR_TOKEN" | base64 -d
```

输出示例：

```
vmess://eyJ2IjoiMiIsInBzIjoi5paw5Yqg5Z2hLTAxIiwiYWRkIjoiZXhhbXBsZS5wcm94eS5jb20iLCJwb3J0IjoiM
TI5MDEiLCJpZCI6Inh4eHh4eHh4LXh4eHgteHh4eC14eHh4LXh4eHh4eHh4eHh4eCIsImFpZCI6IjAiLCJuZXQiOiJ3c
yIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiJcLyIsInRscyI6IiJ9
```

### 2.2 解析 vmess 节点

每行去掉 `vmess://` 前缀，base64 解码即得 JSON：

```json
{
  "v": "2",
  "ps": "新加坡-01",
  "add": "example.proxy.com",
  "port": "12901",
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "aid": "0",
  "net": "ws",
  "type": "none",
  "host": "baidu.com",
  "path": "/",
  "tls": ""
}
```

### 2.3 转换为 sing-box outbound

```json
{
  "type": "vmess",
  "tag": "新加坡-01",
  "server": "example.proxy.com",
  "server_port": 12901,
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "security": "auto",
  "alter_id": 0,
  "domain_resolver": "dns-local",
  "transport": {
    "type": "ws",
    "path": "/",
    "headers": {"Host": "baidu.com"}
  }
}
```

### 2.4 注意事项

- 订阅的前几行可能是**订阅信息**（流量、到期时间等），不是真实节点，需要过滤掉
- 同一订阅下所有节点可能共用同一个服务器和 UUID——这是正常的（前端路由调度）

---

## 3. 最小可用配置

```json
{
  "log": {"level": "info"},
  "inbounds": [
    {
      "type": "mixed",
      "tag": "mixed-in",
      "listen": "0.0.0.0",
      "listen_port": 2080
    }
  ],
  "outbounds": [
    {
      "type": "vmess",
      "tag": "新加坡-01",
      "server": "example.proxy.com",
      "server_port": 12901,
      "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "security": "auto",
      "alter_id": 0,
      "domain_resolver": "dns-local",
      "transport": {
        "type": "ws",
        "path": "/",
        "headers": {"Host": "baidu.com"}
      }
    },
    {
      "type": "selector",
      "tag": "proxy",
      "outbounds": ["新加坡-01", "direct"],
      "default": "新加坡-01"
    },
    {
      "type": "direct",
      "tag": "direct",
      "domain_resolver": "dns-local"
    }
  ],
  "dns": {
    "servers": [
      {"tag": "dns-remote", "type": "https", "server": "1.1.1.1", "detour": "proxy"},
      {"tag": "dns-local",  "type": "local",  "detour": "direct"}
    ],
    "rules": [
      {"rule_set": "geosite-cn", "server": "dns-local"},
      {"rule_set": "geosite-geolocation-!cn", "server": "dns-remote"}
    ]
  },
  "route": {
    "default_domain_resolver": "dns-local",
    "rule_set": [
      {"type": "remote", "tag": "geosite-cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/cn.srs"},
      {"type": "remote", "tag": "geosite-geolocation-!cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/geolocation-!cn.srs"},
      {"type": "remote", "tag": "geoip-cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/cn.srs"}
    ],
    "rules": [
      {"rule_set": "geosite-cn", "outbound": "direct"},
      {"rule_set": "geoip-cn", "outbound": "direct"}
    ],
    "final": "proxy"
  }
}
```

### 关键字段说明

| 字段 | 说明 |
|------|------|
| `inbounds[0].listen` | `0.0.0.0` 允许局域网访问；`127.0.0.1` 仅本机 |
| `outbounds[].domain_resolver` | **必须设置**，指向本地 DNS 解析服务器域名 |
| `route.default_domain_resolver` | **必须设置**（1.12+），全局默认 DNS 解析器 |

---

## 4. DNS 配置

### 4.1 1.12+ 新格式（重要）

sing-box 1.12.0 废弃了旧的 DNS server 格式，必须使用新格式：

| 旧格式（已废弃） | 新格式（当前） |
|---|---|
| `{"address": "local"}` | `{"type": "local"}` |
| `{"address": "tcp://1.1.1.1"}` | `{"type": "tcp", "server": "1.1.1.1"}` |
| `{"address": "https://1.1.1.1/dns-query"}` | `{"type": "https", "server": "1.1.1.1"}` |

### 4.2 推荐 DNS 分流配置

```json
"dns": {
  "servers": [
    {"tag": "dns-remote", "type": "https", "server": "1.1.1.1", "detour": "proxy"},
    {"tag": "dns-local",  "type": "local",  "detour": "direct"}
  ],
  "rules": [
    {"rule_set": "geosite-cn", "server": "dns-local"},
    {"rule_set": "geosite-geolocation-!cn", "server": "dns-remote"}
  ]
}
```

- `dns-remote`：国外域名走代理 DNS（Cloudflare）
- `dns-local`：国内域名走本地 DNS（阿里/腾讯自动）

---

## 5. 路由规则

```json
"route": {
  "default_domain_resolver": "dns-local",
  "rule_set": [
    {"type": "remote", "tag": "geosite-cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/cn.srs"},
    {"type": "remote", "tag": "geoip-cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/cn.srs"},
    {"type": "remote", "tag": "geosite-geolocation-!cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/geolocation-!cn.srs"}
  ],
  "rules": [
    {"rule_set": "geosite-cn", "outbound": "direct"},
    {"rule_set": "geoip-cn", "outbound": "direct"}
  ],
  "final": "proxy"
}
```

规则优先级：从上到下匹配，`final` 为兜底规则。

---

## 6. Clash API + WebUI 面板

### 6.1 启用 Clash API

```json
"experimental": {
  "clash_api": {
    "external_controller": "0.0.0.0:9090",
    "external_ui": "/home/user/.hermes/sing-box-ui"
  }
}
```

### 6.2 部署 YACD 面板

```bash
# 下载 YACD 静态文件
UI_DIR=~/.hermes/sing-box-ui
curl -sL -o /tmp/yacd.tar.gz \
  "https://gh-proxy.com/https://github.com/MetaCubeX/Yacd-meta/archive/refs/heads/gh-pages.tar.gz"
tar xzf /tmp/yacd.tar.gz -C /tmp/
mv /tmp/Yacd-meta-gh-pages "$UI_DIR"
```

访问：`http://<你的IP>:9090/ui`

---

## 7. systemd 自启动

### 7.1 创建服务文件

`~/.config/systemd/user/sing-box.service`：

```ini
[Unit]
Description=sing-box proxy service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c /home/user/sing-box-config.json
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### 7.2 启用

```bash
systemctl --user daemon-reload
systemctl --user enable --now sing-box
```

### 7.3 日常管理

```bash
systemctl --user status sing-box    # 查看状态
systemctl --user restart sing-box   # 重启
systemctl --user stop sing-box      # 停止
journalctl --user -u sing-box -f    # 实时日志
```

### 7.4 工作流

```bash
# 每次修改配置后
sing-box check -c /path/to/config.json    # 1. 先验证
systemctl --user restart sing-box          # 2. 再重启

# 验证代理可用
curl -x http://127.0.0.1:2080 https://httpbin.org/ip
curl -x http://127.0.0.1:2080 -o /dev/null -w "HTTP %{http_code}\n" https://www.google.com
```

---

## 8. Docker 容器走代理

### 8.1 前提

- sing-box 入站监听 `0.0.0.0`（非 `127.0.0.1`）
- 容器通过 Docker 网桥网关访问宿主机

### 8.2 查找网关 IP

```bash
docker inspect <容器名> --format '{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}'
# 通常返回类似 172.19.0.1
```

### 8.3 配置容器代理

以 SearXNG 为例，修改 `settings.yml`：

```yaml
outgoing:
  proxies:
    all://:
      - http://172.19.0.1:2080
```

重启容器：

```bash
docker restart <容器名>
```

### 8.4 验证

```bash
journalctl --user -u sing-box -f | grep inbound
```

应能看到来自容器 IP（如 `172.19.0.2`）的入站连接。

---

## 9. 常见问题

### Q1: `legacy DNS servers is deprecated`

**原因**：使用了旧 DNS 格式。

**解决**：将 `"address": "local"` 改为 `"type": "local"`，`"address": "https://..."` 改为 `"type": "https", "server": "..."`。

### Q2: `missing route.default_domain_resolver`

**原因**：1.12+ 必须设置 domain_resolver。

**解决**：添加 `"route": {"default_domain_resolver": "dns-local"}`。

### Q3: `detour to an empty direct outbound makes no sense`

**原因**：vmess 节点解析域名时形成 DNS 死循环。

**解决**：每个 vmess 出站加 `"domain_resolver": "dns-local"`，direct 出站也加同样设置。

### Q4: `unknown outbound type: dns-out`

**原因**：`dns-out` 不是有效的 outbound 类型。

**解决**：删除该 outbound，DNS 路由由 `dns.rules` 处理。

### Q5: curl localhost 返回 502

**原因**：环境变量 `http_proxy` 劫持了 localhost 请求。

**解决**：使用 `curl --noproxy '*' http://localhost:...`。

### Q6: Docker 容器无法连接代理

**原因**：容器用 `127.0.0.1` 无法访问宿主机。

**解决**：使用 Docker 网桥网关 IP（如 `172.19.0.1`）替代。

### Q7: 配置检查通过但启动失败

**原因**：rule_set 远程下载失败（DNS 死循环导致）。

**解决**：确保所有 vmess/direct 出站都设置了 `"domain_resolver": "dns-local"`。

---

## 附录：完整配置模板

一个可直接使用的完整配置模板，替换 `<...>` 占位符即可：

```json
{
  "log": {"level": "info"},
  "inbounds": [
    {
      "type": "mixed",
      "tag": "mixed-in",
      "listen": "0.0.0.0",
      "listen_port": 2080
    }
  ],
  "outbounds": [
    {
      "type": "vmess",
      "tag": "<节点名称>",
      "server": "<服务器地址>",
      "server_port": <端口>,
      "uuid": "<UUID>",
      "security": "auto",
      "alter_id": 0,
      "domain_resolver": "dns-local",
      "transport": {
        "type": "<ws|tcp|grpc>",
        "path": "<路径>",
        "headers": {"Host": "<host>"}
      }
    },
    {
      "type": "selector",
      "tag": "proxy",
      "outbounds": ["<节点名称>", "direct"],
      "default": "<节点名称>"
    },
    {
      "type": "direct",
      "tag": "direct",
      "domain_resolver": "dns-local"
    }
  ],
  "dns": {
    "servers": [
      {"tag": "dns-remote", "type": "https", "server": "1.1.1.1", "detour": "proxy"},
      {"tag": "dns-local",  "type": "local",  "detour": "direct"}
    ],
    "rules": [
      {"rule_set": "geosite-cn", "server": "dns-local"},
      {"rule_set": "geosite-geolocation-!cn", "server": "dns-remote"}
    ]
  },
  "route": {
    "default_domain_resolver": "dns-local",
    "rule_set": [
      {"type": "remote", "tag": "geosite-cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/cn.srs"},
      {"type": "remote", "tag": "geosite-geolocation-!cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/geolocation-!cn.srs"},
      {"type": "remote", "tag": "geoip-cn", "format": "binary", "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/cn.srs"}
    ],
    "rules": [
      {"rule_set": "geosite-cn", "outbound": "direct"},
      {"rule_set": "geoip-cn", "outbound": "direct"}
    ],
    "final": "proxy"
  },
  "experimental": {
    "clash_api": {
      "external_controller": "0.0.0.0:9090",
      "external_ui": "/path/to/yacd-ui"
    }
  }
}
```
