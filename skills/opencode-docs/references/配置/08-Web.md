<!-- source: https://opencode.ai/docs/zh-cn/web -->

[跳转到内容](08-Web.md#_top)

# Web

在浏览器中使用 OpenCode。

OpenCode 可以作为 Web 应用在浏览器中运行，无需终端即可获得同样强大的 AI 编码体验。

![OpenCode Web - New Session](../assets/docs/_astro/web-homepage-new-session.BB1mEdgo_Z1AT1v3.webp)

## [快速开始](08-Web.md#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B)

运行以下命令启动 Web 界面：

```
opencode web
```

这会在 `127.0.0.1` 上启动一个本地服务器，使用随机可用端口，并自动在默认浏览器中打开 OpenCode。

* * *

## [配置](08-Web.md#%E9%85%8D%E7%BD%AE)

你可以通过命令行标志或 [配置文件](https://opencode.ai/docs/config) 来配置 Web 服务器。

### [端口](08-Web.md#%E7%AB%AF%E5%8F%A3)

默认情况下，OpenCode 会选择一个可用端口。你也可以指定端口：

```
opencode web --port 4096
```

### [主机名](08-Web.md#%E4%B8%BB%E6%9C%BA%E5%90%8D)

默认情况下，服务器绑定到 `127.0.0.1`（仅限本地访问）。要使 OpenCode 在网络中可访问：

```
opencode web --hostname 0.0.0.0
```

使用 `0.0.0.0` 时，OpenCode 会同时显示本地地址和网络地址：

```
  Local access:       http://localhost:4096

  Network access:     http://192.168.1.100:4096
```

### [mDNS 发现](08-Web.md#mdns-%E5%8F%91%E7%8E%B0)

启用 mDNS 可以让你的服务器在本地网络中被自动发现：

```
opencode web --mdns
```

这会自动将主机名设置为 `0.0.0.0`，并将服务器广播为 `opencode.local`。

你可以自定义 mDNS 域名，以便在同一网络中运行多个实例：

```
opencode web --mdns --mdns-domain myproject.local
```

### [CORS](08-Web.md#cors)

要为 CORS 添加额外的允许域名（适用于自定义前端）：

```
opencode web --cors https://example.com
```

### [身份验证](08-Web.md#%E8%BA%AB%E4%BB%BD%E9%AA%8C%E8%AF%81)

要保护服务器访问，可以通过 `OPENCODE_SERVER_PASSWORD` 环境变量设置密码：

```
OPENCODE_SERVER_PASSWORD=secret opencode web
```

用户名默认为 `opencode`，可以通过 `OPENCODE_SERVER_USERNAME` 进行更改。

* * *

## [使用 Web 界面](08-Web.md#%E4%BD%BF%E7%94%A8-web-%E7%95%8C%E9%9D%A2)

启动后，Web 界面提供对 OpenCode 会话的访问。

### [会话](08-Web.md#%E4%BC%9A%E8%AF%9D)

在主页上查看和管理你的会话。你可以查看活跃的会话，也可以创建新的会话。

![OpenCode Web - Active Session](../assets/docs/_astro/web-homepage-active-session.BbK4Ph6e_Z1O7nO1.webp)

### [服务器状态](08-Web.md#%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%8A%B6%E6%80%81)

点击”See Servers”可以查看已连接的服务器及其状态。

![OpenCode Web - See Servers](../assets/docs/_astro/web-homepage-see-servers.BpCOef2l_ZB0rJd.webp)

* * *

## [连接终端](08-Web.md#%E8%BF%9E%E6%8E%A5%E7%BB%88%E7%AB%AF)

你可以将终端 TUI 连接到正在运行的 Web 服务器：

```
# 启动 Web 服务器

opencode web --port 4096

# 在另一个终端中连接 TUI

opencode attach http://localhost:4096
```

这样你就可以同时使用 Web 界面和终端，共享相同的会话和状态。

* * *

## [配置文件](08-Web.md#%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6)

你也可以在 `opencode.json` 配置文件中设置服务器选项：

```
{

  "server": {

    "port": 4096,

    "hostname": "0.0.0.0",

    "mdns": true,

    "cors": ["https://example.com"]

  }

}
```

命令行标志的优先级高于配置文件中的设置。