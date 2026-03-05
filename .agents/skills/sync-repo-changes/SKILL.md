---
name: sync-repo-changes
description: 当用户提出“把改动同步到仓库”“帮我提交并推送”“把当前修改发起 PR”“同步到 GitHub”等请求，或需要将当前仓库改动提交、推送并自动创建 PR 时，应使用此技能。
---

# 一键同步仓库改动（分支 + PR）

## 使用时机

当用户希望把当前仓库改动同步到 GitHub 并创建 PR 时，执行本技能。

适用请求示例：
- 把改动同步到仓库
- 帮我提交并推送
- 把当前修改发起 PR
- 同步到 GitHub

## 一键同步输入约定

未明确指定参数时，使用以下默认值：

- 目标基线分支：`main`
- 提交范围：仓库全部已修改内容（`git add -A`）
- 推送策略：创建新分支后推送（不直推 `main`）
- PR 审阅人：不自动指定
- 提交文案与 PR 文案：基于变更自动生成，生成后先确认再执行

当用户明确提供参数时，仅覆盖对应字段。

## 执行前检查

按顺序执行以下检查。任一步失败即停止，并输出修复步骤。

1. 校验当前目录位于 Git 仓库：

```bash
git rev-parse --is-inside-work-tree
```

2. 校验 `origin` 远端存在：

```bash
git remote get-url origin
```

3. 校验 `gh` 已安装：

```bash
gh --version
```

若 `gh` 缺失，立即停止，并输出安装与登录步骤（不继续后续流程）：

```bash
# macOS
brew install gh

# Windows (winget)
winget install --id GitHub.cli

# Ubuntu/Debian
sudo apt install gh

# 登录 GitHub
gh auth login
```

## 同步主流程

严格按以下命令序执行，不跳步，不改序。

1. 生成分支名：`pm-sync/YYYYMMDD-HHmmss`

```bash
branch_name="pm-sync/$(date +%Y%m%d-%H%M%S)"
```

2. 创建并切换分支：

```bash
git checkout -b "$branch_name"
```

若分支名冲突，追加时间戳后缀重试一次；重试失败则停止并提示用户确认新分支名。

3. 暂存全部改动：

```bash
git add -A
```

4. 检查是否有可提交内容：

```bash
git diff --cached --name-only
```

若结果为空，停止流程并输出“无可提交内容”。

5. 自动生成中文提交标题并确认：
- 先读取暂存文件列表，生成候选标题（示例格式：`同步仓库改动：更新技能与配置`）。
- 先向用户展示候选标题并请求确认。
- 用户确认后，执行提交；若用户拒绝，使用用户提供的新标题继续。

6. 提交改动：

```bash
git commit -m "<已确认的中文提交标题>"
```

7. 推送分支到远端：

```bash
git push -u origin "$branch_name"
```

推送失败时立即停止，不执行 `pull`、`rebase`、`force push`。

8. 自动生成中文 PR 标题与正文并确认：
- 标题示例：`同步仓库改动：新增同步技能并更新插件配置`
- 正文至少包含：变更摘要、影响范围、验证结果
- 先确认文案，再执行建 PR 命令

9. 创建 PR（默认指向 `main`）：

```bash
gh pr create --base main --head "$branch_name" --title "<已确认的PR标题>" --body "<已确认的PR正文>"
```

创建失败时立即停止，并给出下一步修复命令（如 `gh auth login`、检查仓库写权限后重试）。

## 失败处理

执行失败时统一遵循以下规则：

1. 立即停止，不继续后续步骤。
2. 清晰报告失败命令、错误原因、建议修复命令。
3. 保留当前已完成结果（如已创建分支、已提交 commit），不自动回滚。
4. 禁止执行高风险命令：`git pull --rebase`、`git push --force`、`git reset --hard`。

## 输出模板

流程结束后，按以下模板输出结果：

```markdown
## 同步结果

- 分支名：`<branch_name>`
- Commit：`<short_sha>`
- PR 链接：<pr_url 或 "创建失败">
- 执行状态：`成功` / `失败`

## 变更摘要
- <要点 1>
- <要点 2>

## 下一步建议
1. <建议 1>
2. <建议 2>
```

成功时至少给出 PR 链接；失败时至少给出可直接执行的修复命令。
