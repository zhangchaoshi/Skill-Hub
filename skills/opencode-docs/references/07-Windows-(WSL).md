<!-- source: https://opencode.ai/docs/zh-cn/windows-wsl -->

[跳转到内容](07-Windows-(WSL).md#_top)

# Windows (WSL)

通过 WSL 在 Windows 上运行 OpenCode 以获得最佳体验。

虽然 OpenCode 可以直接在 Windows 上运行，但我们推荐使用 [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) 以获得最佳体验。WSL 提供了一个 Linux 环境，能够与 OpenCode 的各项功能无缝配合。

* * *

## [安装配置](07-Windows-(WSL).md#%E5%AE%89%E8%A3%85%E9%85%8D%E7%BD%AE)

1. **安装 WSL**

如果尚未安装，请参照 Microsoft 官方指南 [安装 WSL](https://learn.microsoft.com/en-us/windows/wsl/install)。

2. **在 WSL 中安装 OpenCode**

WSL 设置完成后，打开 WSL 终端，使用任一 [安装方式](https://opencode.ai/docs/) 安装 OpenCode。



```
curl -fsSL https://opencode.ai/install | bash
```

3. **从 WSL 中使用 OpenCode**

导航到你的项目目录（通过 `/mnt/c/`、`/mnt/d/` 等路径访问 Windows 文件），然后运行 OpenCode。



```
cd /mnt/c/Users/YourName/project

opencode
```


* * *

## [桌面应用 \+ WSL 服务器](07-Windows-(WSL).md#%E6%A1%8C%E9%9D%A2%E5%BA%94%E7%94%A8--wsl-%E6%9C%8D%E5%8A%A1%E5%99%A8)

如果你希望使用 OpenCode 桌面应用，同时在 WSL 中运行服务器：

1. **在 WSL 中启动服务器**，添加 `--hostname 0.0.0.0` 以允许外部连接：



```
opencode serve --hostname 0.0.0.0 --port 4096
```

2. **在桌面应用中连接到**`http://localhost:4096`


```
OPENCODE_SERVER_PASSWORD=your-password opencode serve --hostname 0.0.0.0
```

* * *

## [Web 客户端 + WSL](07-Windows-(WSL).md#web-%E5%AE%A2%E6%88%B7%E7%AB%AF--wsl)

要在 Windows 上获得最佳的 Web 体验：

1. **在 WSL 终端中运行 `opencode web`**，而非在 PowerShell 中运行：



```
opencode web --hostname 0.0.0.0
```

2. **在 Windows 浏览器中访问**`http://localhost:<port>`（OpenCode 会输出该 URL）


从 WSL 中运行 `opencode web` 可确保正确的文件系统访问和终端集成，同时仍可通过 Windows 浏览器进行访问。

* * *

## [访问 Windows 文件](07-Windows-(WSL).md#%E8%AE%BF%E9%97%AE-windows-%E6%96%87%E4%BB%B6)

WSL 可以通过 `/mnt/` 目录访问你的所有 Windows 文件：

- `C:` 盘 → `/mnt/c/`
- `D:` 盘 → `/mnt/d/`
- 其他盘符以此类推…

示例：

```
cd /mnt/c/Users/YourName/Documents/project

opencode
```

* * *

## [使用技巧](07-Windows-(WSL).md#%E4%BD%BF%E7%94%A8%E6%8A%80%E5%B7%A7)

- 对于存储在 Windows 驱动器上的项目，在 WSL 中运行 OpenCode 即可无缝访问文件
- 搭配 VS Code 的 [WSL 扩展](https://code.visualstudio.com/docs/remote/wsl) 使用 OpenCode，打造一体化的开发工作流
- OpenCode 的配置和会话数据存储在 WSL 环境中的 `~/.local/share/opencode/`