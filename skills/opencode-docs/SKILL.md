---
name: opencode-docs
description: 当用户想在 OpenCode (opencode.ai) 中文文档里查找/定位信息（如“配置/提供商/网络/企业版/故障排除/Windows/CLI/IDE/插件/MCP/LSP/SDK/skills”）
---

# OpenCode 文档 (zh-cn) 镜像 + 定位器

## 概述

此 skill 是 `https://opencode.ai/docs/zh-cn/**` 的**本地镜像文档**：

- `SKILL.md` 作为**索引页**。
- 实际文档存放在 `references/` 目录下，遵循原始 URL 路径结构。

默认行为：**仅整理/定位**（返回相关本地文档路径，可选附带简短片段）。除非用户明确要求，否则**不**生成最终解释。

## 路径

- 技能根目录：`skills/opencode-docs/`
- 本地镜像根目录：`skills/opencode-docs/references/`

## 文档索引

从这里开始：
- `references/01-简介.md`

自动生成的顶层索引（运行更新管道可刷新）：
<!-- BEGIN AUTO-GENERATED INDEX -->
## 快速开始
- [简介](references/01-简介.md)
- [配置](references/02-配置.md)
- [提供商](references/03-提供商.md)
- [网络](references/04-网络.md)
- [企业版](references/05-企业版.md)
- [故障排除](references/06-故障排除.md)
- [Windows (WSL)](references/07-Windows-(WSL).md)

## 使用
- [TUI](references/使用/01-TUI.md)
- [CLI](references/使用/02-CLI.md)
- [IDE](references/使用/03-IDE.md)
- [快捷键](references/使用/04-快捷键.md)
- [分享](references/使用/05-分享.md)
- [主题](references/使用/06-主题.md)

## 配置
- [模型](references/配置/01-模型.md)
- [权限](references/配置/02-权限.md)
- [规则](references/配置/03-规则.md)
- [格式化工具](references/配置/04-格式化工具.md)
- [工具](references/配置/05-工具.md)
- [自定义工具](references/配置/06-自定义工具.md)
- [服务器](references/配置/07-服务器.md)
- [Web](references/配置/08-Web.md)
- [GitHub](references/配置/09-GitHub.md)
- [GitLab](references/配置/10-GitLab.md)

## 开发
- [代理](references/开发/01-代理.md)
- [代理技能](references/开发/02-代理技能.md)
- [插件](references/开发/03-插件.md)
- [MCP 服务器](references/开发/04-MCP-服务器.md)
- [LSP 服务器](references/开发/05-LSP-服务器.md)
- [SDK](references/开发/06-SDK.md)
- [Go](references/开发/07-Go.md)
- [ACP 支持](references/开发/08-ACP-支持.md)
- [Zen](references/开发/09-Zen.md)
- [生态系统](references/开发/10-生态系统.md)
- [命令](references/开发/11-命令.md)
<!-- END AUTO-GENERATED INDEX -->
## 更新本地镜像

### 前置条件

- 网络可访问
- 环境变量 `FIRECRAWL_API_KEY` 已设置

### 一键更新

```bash
cd /Users/majianhang/Code/Company/Skill-Hub

# 设置 SKIP_DOWNLOAD=1 可复用已有的 .firecrawl 输出（不消耗额外额度）
bash scripts/skills/opencode-docs/update.sh
```

## 为问题定位相关文档

### 处理流程

1. 从用户查询中提取 2–6 个关键词（中文和/或英文）。
2. 使用 `rg` 在 `skills/opencode-docs/references/` 下搜索。
3. 返回 **5–10** 个最相关的 `.md` 文件路径。
4. 可选为每个文件附带 1 个简短片段（1–2 行），但保持输出简洁。
5. 除非明确要求，否则不直接回答问题本身。

### 命令

```bash
cd /Users/majianhang/Code/Company/Skill-Hub

rg -n "关键词1|keyword2" "skills/opencode-docs/references"
```

### 输出格式

始终按以下格式返回结果：

```text
最匹配的结果：
- skills/opencode-docs/references/<path>.md: <一句话原因/片段>
...
```
