<!-- source: https://opencode.ai/docs/zh-cn/github -->

[跳转到内容](09-GitHub.md#_top)

# GitHub

在 GitHub Issue 和 Pull Request 中使用 OpenCode。

OpenCode 可以与你的 GitHub 工作流集成。在评论中提及 `/opencode` 或 `/oc`，OpenCode 就会在你的 GitHub Actions 运行器中执行任务。

* * *

## [功能特性](09-GitHub.md#%E5%8A%9F%E8%83%BD%E7%89%B9%E6%80%A7)

- **问题分类**：让 OpenCode 调查某个 Issue 并为你做出解释。
- **修复与实现**：让 OpenCode 修复 Issue 或实现某个功能。它会在新分支中工作，并提交包含所有变更的 PR。
- **安全可靠**：OpenCode 在你自己的 GitHub 运行器中运行。

* * *

## [安装](09-GitHub.md#%E5%AE%89%E8%A3%85)

在一个位于 GitHub 仓库中的项目里运行以下命令：

```
opencode github install
```

该命令会引导你完成 GitHub App 的安装、工作流的创建以及密钥的配置。

* * *

### [手动设置](09-GitHub.md#%E6%89%8B%E5%8A%A8%E8%AE%BE%E7%BD%AE)

你也可以手动进行设置。

1. **安装 GitHub App**

前往 [**github.com/apps/opencode-agent**](https://github.com/apps/opencode-agent)，确保已在目标仓库中安装该应用。

2. **添加工作流**

将以下工作流文件添加到仓库的 `.github/workflows/opencode.yml` 中。请确保在 `env` 中设置合适的 `model` 及所需的 API 密钥。



```
name: opencode




on:

     issue_comment:

       types: [created]

     pull_request_review_comment:

       types: [created]




jobs:

     opencode:

       if: |

         contains(github.event.comment.body, '/oc') ||

         contains(github.event.comment.body, '/opencode')

       runs-on: ubuntu-latest

       permissions:

         id-token: write

       steps:

       - name: Checkout repository

         uses: actions/checkout@v6

         with:

           fetch-depth: 1

           persist-credentials: false

       - name: Run OpenCode

        uses: anomalyco/opencode/github@latest

        env:

          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

        with:

          model: anthropic/claude-sonnet-4-20250514

          # share: true

          # github_token: xxxx
```

3. **将 API 密钥存储到 Secrets 中**

在你的组织或项目的 **Settings** 中，展开左侧的 **Secrets and variables**，然后选择 **Actions**，添加所需的 API 密钥。


* * *

## [配置](09-GitHub.md#%E9%85%8D%E7%BD%AE)

- `model`：OpenCode 使用的模型，格式为 `provider/model`。此项为 **必填**。

- `agent`：要使用的代理，必须是主代理。如果未找到，则回退到配置中的 `default_agent`，若仍未找到则使用 `"build"`。

- `share`：是否共享 OpenCode 会话。对于公开仓库，默认为 **true**。

- `prompt`：可选的自定义提示词，用于覆盖默认行为。可通过此项自定义 OpenCode 处理请求的方式。

- `token`：可选的 GitHub 访问 Token，用于执行创建评论、提交变更和创建 Pull Request 等操作。默认情况下，OpenCode 使用 OpenCode GitHub App 的安装访问 Token，因此提交、评论和 Pull Request 会显示为来自该应用。

你也可以使用 GitHub Action 运行器内置的 [`GITHUB_TOKEN`](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)，而无需安装 OpenCode GitHub App。只需确保在工作流中授予所需的权限：



```
permissions:

    id-token: write

    contents: write

    pull-requests: write

    issues: write
```













如果你愿意，也可以使用 [个人访问令牌](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)（PAT）。


* * *

## [支持的事件](09-GitHub.md#%E6%94%AF%E6%8C%81%E7%9A%84%E4%BA%8B%E4%BB%B6)

OpenCode 可以由以下 GitHub 事件触发：

| 事件类型 | 触发方式 | 详情 |
| --- | --- | --- |
| `issue_comment` | 在 Issue 或 PR 上发表评论 | 在评论中提及 `/opencode` 或 `/oc`。OpenCode 会读取上下文，并可创建分支、提交 PR 或回复。 |
| `pull_request_review_comment` | 在 PR 中对特定代码行发表评论 | 在代码审查时提及 `/opencode` 或 `/oc`。OpenCode 会接收文件路径、行号和 diff 上下文。 |
| `issues` | Issue 被创建或编辑 | 在 Issue 创建或修改时自动触发 OpenCode。需要提供 `prompt` 输入。 |
| `pull_request` | PR 被创建或更新 | 在 PR 被打开、同步或重新打开时自动触发 OpenCode。适用于自动化审查场景。 |
| `schedule` | 基于 Cron 的定时任务 | 按计划运行 OpenCode。需要提供 `prompt` 输入。输出会写入日志和 PR（没有 Issue 可供评论）。 |
| `workflow_dispatch` | 从 GitHub UI 手动触发 | 通过 Actions 选项卡按需触发 OpenCode。需要提供 `prompt` 输入。输出会写入日志和 PR。 |

### [定时任务示例](09-GitHub.md#%E5%AE%9A%E6%97%B6%E4%BB%BB%E5%8A%A1%E7%A4%BA%E4%BE%8B)

按计划运行 OpenCode 以执行自动化任务：

```
name: Scheduled OpenCode Task

on:

schedule:

    - cron: "0 9 * * 1" # Every Monday at 9am UTC

jobs:

opencode:

    runs-on: ubuntu-latest

    permissions:

      id-token: write

      contents: write

      pull-requests: write

      issues: write

    steps:

      - name: Checkout repository

        uses: actions/checkout@v6

        with:

          persist-credentials: false

      - name: Run OpenCode

        uses: anomalyco/opencode/github@latest

        env:

          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

        with:

          model: anthropic/claude-sonnet-4-20250514

          prompt: |

            Review the codebase for any TODO comments and create a summary.

            If you find issues worth addressing, open an issue to track them.
```

对于定时事件，`prompt` 输入为 **必填**，因为没有评论可供提取指令。定时工作流在运行时没有用户上下文来进行权限检查，因此如果你希望 OpenCode 创建分支或 PR，工作流必须授予 `contents: write` 和 `pull-requests: write` 权限。

* * *

### [Pull Request 示例](09-GitHub.md#pull-request-%E7%A4%BA%E4%BE%8B)

在 PR 被创建或更新时自动进行审查：

```
name: opencode-review

on:

pull_request:

    types: [opened, synchronize, reopened, ready_for_review]

jobs:

review:

    runs-on: ubuntu-latest

    permissions:

      id-token: write

      contents: read

      pull-requests: read

      issues: read

    steps:

      - uses: actions/checkout@v6

        with:

          persist-credentials: false

      - uses: anomalyco/opencode/github@latest

        env:

          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

        with:

          model: anthropic/claude-sonnet-4-20250514

          use_github_token: true

          prompt: |

            Review this pull request:

            - Check for code quality issues

            - Look for potential bugs

            - Suggest improvements
```

对于 `pull_request` 事件，如果未提供 `prompt`，OpenCode 将默认对该 Pull Request 进行审查。

* * *

### [Issue 分类示例](09-GitHub.md#issue-%E5%88%86%E7%B1%BB%E7%A4%BA%E4%BE%8B)

自动分类新建的 Issue。以下示例会过滤掉注册不满 30 天的账户以减少垃圾信息：

```
name: Issue Triage

on:

issues:

    types: [opened]

jobs:

triage:

    runs-on: ubuntu-latest

    permissions:

      id-token: write

      contents: write

      pull-requests: write

      issues: write

    steps:

      - name: Check account age

        id: check

        uses: actions/github-script@v7

        with:

          script: |

            const user = await github.rest.users.getByUsername({

              username: context.payload.issue.user.login

            });

            const created = new Date(user.data.created_at);

            const days = (Date.now() - created) / (1000 * 60 * 60 * 24);

            return days >= 30;

          result-encoding: string

      - uses: actions/checkout@v6

        if: steps.check.outputs.result == 'true'

        with:

          persist-credentials: false

      - uses: anomalyco/opencode/github@latest

        if: steps.check.outputs.result == 'true'

        env:

          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

        with:

          model: anthropic/claude-sonnet-4-20250514

          prompt: |

            Review this issue. If there's a clear fix or relevant docs:

            - Provide documentation links

            - Add error handling guidance for code examples

            Otherwise, do not comment.
```

对于 `issues` 事件，`prompt` 输入为 **必填**，因为没有评论可供提取指令。

* * *

## [自定义提示词](09-GitHub.md#%E8%87%AA%E5%AE%9A%E4%B9%89%E6%8F%90%E7%A4%BA%E8%AF%8D)

覆盖默认提示词，以便为你的工作流自定义 OpenCode 的行为。

```
- uses: anomalyco/opencode/github@latest

with:

    model: anthropic/claude-sonnet-4-5

    prompt: |

      Review this pull request:

      - Check for code quality issues

      - Look for potential bugs

      - Suggest improvements
```

这对于在项目中实施特定的审查标准、编码规范或关注重点非常有用。

* * *

## [示例](09-GitHub.md#%E7%A4%BA%E4%BE%8B)

以下是在 GitHub 中使用 OpenCode 的一些示例。

- **解释 Issue**

在 GitHub Issue 中添加以下评论：



```
/opencode explain this issue
```













OpenCode 会阅读整个讨论串（包括所有评论），并回复一份清晰的解释。

- **修复 Issue**

在 GitHub Issue 中输入：



```
/opencode fix this
```













OpenCode 会创建一个新分支，实现变更，并提交一个包含所有修改的 PR。

- **审查 PR 并进行修改**

在 GitHub PR 上留下以下评论：



```
Delete the attachment from S3 when the note is removed /oc
```













OpenCode 会实现所请求的变更并将其提交到同一个 PR 中。

- **审查特定代码行**

在 PR 的 “Files” 选项卡中直接对代码行留下评论。OpenCode 会自动检测文件、行号和 diff 上下文，从而提供精准的响应。



```
[Comment on specific lines in Files tab]

/oc add error handling here
```













当你对特定代码行发表评论时，OpenCode 会接收到：


  - 正在审查的具体文件
  - 特定的代码行
  - 周围的 diff 上下文
  - 行号信息

这样你就可以提出更有针对性的请求，而无需手动指定文件路径或行号。