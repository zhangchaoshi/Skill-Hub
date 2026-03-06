<!-- source: https://opencode.ai/docs/zh-cn/tui -->

[跳转到内容](01-TUI.md#_top)

# TUI

使用 OpenCode 终端用户界面。

OpenCode 提供了一个交互式终端界面（TUI），用于配合 LLM 处理您的项目。

运行 OpenCode 即可启动当前目录的 TUI。

```
opencode
```

或者您可以为指定的工作目录启动它。

```
opencode /path/to/project
```

进入 TUI 后，您可以输入消息进行提示。

```
Give me a quick summary of the codebase.
```

* * *

## [文件引用](01-TUI.md#%E6%96%87%E4%BB%B6%E5%BC%95%E7%94%A8)

您可以使用 `@` 在消息中引用文件。这会在当前工作目录中进行模糊文件搜索。

```
How is auth handled in @packages/functions/src/api/index.ts?
```

文件的内容会自动添加到对话中。

* * *

## [Bash 命令](01-TUI.md#bash-%E5%91%BD%E4%BB%A4)

以 `!` 开头的消息会作为 shell 命令执行。

```
!ls -la
```

命令的输出会作为工具结果添加到对话中。

* * *

## [命令](01-TUI.md#%E5%91%BD%E4%BB%A4)

使用 OpenCode TUI 时，您可以输入 `/` 后跟命令名称来快速执行操作。例如：

```
/help
```

大多数命令还支持以 `ctrl+x` 作为前导键的快捷键，其中 `ctrl+x` 是默认前导键。 [了解更多](https://opencode.ai/docs/keybinds)。

以下是所有可用的斜杠命令：

* * *

### [connect](01-TUI.md#connect)

将提供商添加到 OpenCode。允许您从可用的提供商中选择并添加其 API 密钥。

```
/connect
```

* * *

### [compact](01-TUI.md#compact)

压缩当前会话。 _别名_：`/summarize`

```
/compact
```

**快捷键：**`ctrl+x c`

* * *

### [details](01-TUI.md#details)

切换工具执行详情的显示。

```
/details
```

**快捷键：**`ctrl+x d`

* * *

### [editor](01-TUI.md#editor)

打开外部编辑器来编写消息。使用 `EDITOR` 环境变量中设置的编辑器。 [了解更多](01-TUI.md#editor-setup)。

```
/editor
```

**快捷键：**`ctrl+x e`

* * *

### [exit](01-TUI.md#exit)

退出 OpenCode。 _别名_：`/quit`、`/q`

```
/exit
```

**快捷键：**`ctrl+x q`

* * *

### [export](01-TUI.md#export)

将当前对话导出为 Markdown 并在默认编辑器中打开。使用 `EDITOR` 环境变量中设置的编辑器。 [了解更多](01-TUI.md#editor-setup)。

```
/export
```

**快捷键：**`ctrl+x x`

* * *

### [help](01-TUI.md#help)

显示帮助对话框。

```
/help
```

**快捷键：**`ctrl+x h`

* * *

### [init](01-TUI.md#init)

创建或更新 `AGENTS.md` 文件。 [了解更多](https://opencode.ai/docs/rules)。

```
/init
```

**快捷键：**`ctrl+x i`

* * *

### [models](01-TUI.md#models)

列出可用模型。

```
/models
```

**快捷键：**`ctrl+x m`

* * *

### [new](01-TUI.md#new)

开始新的会话。 _别名_：`/clear`

```
/new
```

**快捷键：**`ctrl+x n`

* * *

### [redo](01-TUI.md#redo)

重做之前撤销的消息。仅在使用 `/undo` 后可用。

在内部，这使用 Git 来管理文件更改。因此您的项目 **需要是一个 Git 仓库**。

```
/redo
```

**快捷键：**`ctrl+x r`

* * *

### [sessions](01-TUI.md#sessions)

列出会话并在会话之间切换。 _别名_：`/resume`、`/continue`

```
/sessions
```

**快捷键：**`ctrl+x l`

* * *

分享当前会话。 [了解更多](https://opencode.ai/docs/share)。

```
/share
```

**快捷键：**`ctrl+x s`

* * *

### [themes](01-TUI.md#themes)

列出可用主题。

```
/themes
```

**快捷键：**`ctrl+x t`

* * *

### [thinking](01-TUI.md#thinking)

切换对话中思考/推理块的可见性。启用后，您可以看到支持扩展思考的模型的推理过程。

```
/thinking
```

* * *

### [undo](01-TUI.md#undo)

撤销对话中的最后一条消息。移除最近的用户消息、所有后续响应以及所有文件更改。

在内部，这使用 Git 来管理文件更改。因此您的项目 **需要是一个 Git 仓库**。

```
/undo
```

**快捷键：**`ctrl+x u`

* * *

### [unshare](01-TUI.md#unshare)

取消分享当前会话。 [了解更多](https://opencode.ai/docs/share#un-sharing)。

```
/unshare
```

* * *

## [编辑器设置](01-TUI.md#%E7%BC%96%E8%BE%91%E5%99%A8%E8%AE%BE%E7%BD%AE)

`/editor` 和 `/export` 命令都使用 `EDITOR` 环境变量中指定的编辑器。

- [Linux/macOS](01-TUI.md#tab-panel-116)
- [Windows (CMD)](01-TUI.md#tab-panel-117)
- [Windows (PowerShell)](01-TUI.md#tab-panel-118)

```
# Example for nano or vim

export EDITOR=nano

export EDITOR=vim

# For GUI editors, VS Code, Cursor, VSCodium, Windsurf, Zed, etc.

# include --wait

export EDITOR="code --wait"
```

要使其永久生效，请将其添加到您的 shell 配置文件中；
`~/.bashrc`、`~/.zshrc` 等。

```
set EDITOR=notepad

# For GUI editors, VS Code, Cursor, VSCodium, Windsurf, Zed, etc.

# include --wait

set EDITOR=code --wait
```

要使其永久生效，请使用 **系统属性** \> **环境变量**。

```
$env:EDITOR = "notepad"

# For GUI editors, VS Code, Cursor, VSCodium, Windsurf, Zed, etc.

# include --wait

$env:EDITOR = "code --wait"
```

要使其永久生效，请将其添加到您的 PowerShell 配置文件中。

常用的编辑器选项包括：

- `code` \- Visual Studio Code
- `cursor` \- Cursor
- `windsurf` \- Windsurf
- `nvim` \- Neovim 编辑器
- `vim` \- Vim 编辑器
- `nano` \- Nano 编辑器
- `notepad` \- Notepad（Windows 记事本）
- `subl` \- Sublime Text

某些编辑器需要命令行参数才能以阻塞模式运行。`--wait` 标志使编辑器进程阻塞直到关闭。

* * *

## [配置](01-TUI.md#%E9%85%8D%E7%BD%AE)

您可以通过 OpenCode 配置文件自定义 TUI 行为。

```
{

  "$schema": "https://opencode.ai/config.json",

  "tui": {

    "scroll_speed": 3,

    "scroll_acceleration": {

      "enabled": true

    }

  }

}
```

### [选项](01-TUI.md#%E9%80%89%E9%A1%B9)

- `scroll_acceleration` \- 启用 macOS 风格的滚动加速，实现平滑、自然的滚动体验。启用后，快速滚动时速度会增加，慢速移动时保持精确。 **此设置优先于 `scroll_speed`，启用时会覆盖它。**
- `scroll_speed` \- 控制使用滚动命令时 TUI 的滚动速度（最小值：`1`）。默认为 `3`。 **注意：如果 `scroll_acceleration.enabled` 设置为 `true`，则此设置会被忽略。**

* * *

## [自定义](01-TUI.md#%E8%87%AA%E5%AE%9A%E4%B9%89)

您可以使用命令面板（`ctrl+x h` 或 `/help`）自定义 TUI 视图的各个方面。这些设置在重启后仍会保留。

* * *

#### [用户名显示](01-TUI.md#%E7%94%A8%E6%88%B7%E5%90%8D%E6%98%BE%E7%A4%BA)

切换您的用户名是否显示在聊天消息中。通过以下方式访问：

- 命令面板：搜索 “username” 或 “hide username”
- 该设置会自动保存，并在各个 TUI 会话中保持记忆