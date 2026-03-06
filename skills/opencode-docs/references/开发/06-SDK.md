<!-- source: https://opencode.ai/docs/zh-cn/sdk -->

[跳转到内容](06-SDK.md#_top)

# SDK

opencode 服务器的类型安全 JS 客户端。

opencode JS/TS SDK 提供了一个类型安全的客户端，用于与服务器进行交互。
你可以用它来构建集成方案，并以编程方式控制 opencode。

[了解更多](https://opencode.ai/docs/server) 关于服务器的工作原理。如需示例，请查看社区构建的 [项目](https://opencode.ai/docs/ecosystem#projects)。

* * *

## [安装](06-SDK.md#%E5%AE%89%E8%A3%85)

从 npm 安装 SDK：

```
npm install @opencode-ai/sdk
```

* * *

## [创建客户端](06-SDK.md#%E5%88%9B%E5%BB%BA%E5%AE%A2%E6%88%B7%E7%AB%AF)

创建一个 opencode 实例：

```
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()
```

这会同时启动服务器和客户端。

#### [选项](06-SDK.md#%E9%80%89%E9%A1%B9)

| 选项 | 类型 | 描述 | 默认值 |
| --- | --- | --- | --- |
| `hostname` | `string` | 服务器主机名 | `127.0.0.1` |
| `port` | `number` | 服务器端口 | `4096` |
| `signal` | `AbortSignal` | 用于取消操作的中止信号 | `undefined` |
| `timeout` | `number` | 服务器启动超时时间（毫秒） | `5000` |
| `config` | `Config` | 配置对象 | `{}` |

* * *

## [配置](06-SDK.md#%E9%85%8D%E7%BD%AE)

你可以传入一个配置对象来自定义行为。实例仍然会读取你的 `opencode.json`，但你可以通过内联方式覆盖或添加配置：

```
import { createOpencode } from "@opencode-ai/sdk"

const opencode = await createOpencode({

  hostname: "127.0.0.1",

  port: 4096,

  config: {

    model: "anthropic/claude-3-5-sonnet-20241022",

  },

})

console.log(`Server running at ${opencode.server.url}`)

opencode.server.close()
```

## [仅客户端模式](06-SDK.md#%E4%BB%85%E5%AE%A2%E6%88%B7%E7%AB%AF%E6%A8%A1%E5%BC%8F)

如果你已经有一个正在运行的 opencode 实例，可以创建一个客户端实例来连接它：

```
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({

  baseUrl: "http://localhost:4096",

})
```

#### [选项](06-SDK.md#%E9%80%89%E9%A1%B9-1)

| 选项 | 类型 | 描述 | 默认值 |
| --- | --- | --- | --- |
| `baseUrl` | `string` | 服务器 URL | `http://localhost:4096` |
| `fetch` | `function` | 自定义 fetch 实现 | `globalThis.fetch` |
| `parseAs` | `string` | 响应解析方式 | `auto` |
| `responseStyle` | `string` | 返回风格：`data` 或 `fields` | `fields` |
| `throwOnError` | `boolean` | 抛出错误而非返回错误 | `false` |

* * *

## [类型](06-SDK.md#%E7%B1%BB%E5%9E%8B)

SDK 包含所有 API 类型的 TypeScript 定义。你可以直接导入它们：

```
import type { Session, Message, Part } from "@opencode-ai/sdk"
```

所有类型均根据服务器的 OpenAPI 规范生成，可在 [类型文件](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) 中查看。

* * *

## [错误处理](06-SDK.md#%E9%94%99%E8%AF%AF%E5%A4%84%E7%90%86)

SDK 可能会抛出错误，你可以捕获并处理这些错误：

```
try {

  await client.session.get({ path: { id: "invalid-id" } })

} catch (error) {

  console.error("Failed to get session:", (error as Error).message)

}
```

* * *

## [结构化输出](06-SDK.md#%E7%BB%93%E6%9E%84%E5%8C%96%E8%BE%93%E5%87%BA)

你可以通过指定带有 JSON Schema 的 `format` 来请求模型返回结构化的 JSON 输出。模型会使用 `StructuredOutput` 工具返回符合你 Schema 的经过验证的 JSON。

### [基本用法](06-SDK.md#%E5%9F%BA%E6%9C%AC%E7%94%A8%E6%B3%95)

```
const result = await client.session.prompt({

  path: { id: sessionId },

  body: {

    parts: [{ type: "text", text: "Research Anthropic and provide company info" }],

    format: {

      type: "json_schema",

      schema: {

        type: "object",

        properties: {

          company: { type: "string", description: "Company name" },

          founded: { type: "number", description: "Year founded" },

          products: {

            type: "array",

            items: { type: "string" },

            description: "Main products",

          },

        },

        required: ["company", "founded"],

      },

    },

  },

})

// Access the structured output

console.log(result.data.info.structured_output)

// { company: "Anthropic", founded: 2021, products: ["Claude", "Claude API"] }
```

### [输出格式类型](06-SDK.md#%E8%BE%93%E5%87%BA%E6%A0%BC%E5%BC%8F%E7%B1%BB%E5%9E%8B)

| 类型 | 描述 |
| --- | --- |
| `text` | 默认值。标准文本响应（无结构化输出） |
| `json_schema` | 返回符合所提供 Schema 的经过验证的 JSON |

### [JSON Schema 格式](06-SDK.md#json-schema-%E6%A0%BC%E5%BC%8F)

使用 `type: 'json_schema'` 时，需提供以下字段：

| 字段 | 类型 | 描述 |
| --- | --- | --- |
| `type` | `'json_schema'` | 必填。指定 JSON Schema 模式 |
| `schema` | `object` | 必填。定义输出结构的 JSON Schema 对象 |
| `retryCount` | `number` | 可选。验证重试次数（默认值：2） |

### [错误处理](06-SDK.md#%E9%94%99%E8%AF%AF%E5%A4%84%E7%90%86-1)

如果模型在所有重试后仍无法生成有效的结构化输出，响应中会包含 `StructuredOutputError`：

```
if (result.data.info.error?.name === "StructuredOutputError") {

  console.error("Failed to produce structured output:", result.data.info.error.message)

  console.error("Attempts:", result.data.info.error.retries)

}
```

### [最佳实践](06-SDK.md#%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5)

1. **在 Schema 属性中提供清晰的描述**，帮助模型理解需要提取的数据
2. **使用 `required`** 指定哪些字段必须存在
3. **保持 Schema 简洁** — 复杂的嵌套 Schema 可能会让模型更难正确填充
4. **设置合适的 `retryCount`** — 对于复杂 Schema 可增加重试次数，对于简单 Schema 可减少

* * *

## [API](06-SDK.md#api)

SDK 通过类型安全的客户端暴露所有服务器 API。

* * *

### [Global](06-SDK.md#global)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `global.health()` | 检查服务器健康状态和版本 | `{ healthy: true, version: string }` |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B)

```
const health = await client.global.health()

console.log(health.data.version)
```

* * *

### [App](06-SDK.md#app)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `app.log()` | 写入一条日志 | `boolean` |
| `app.agents()` | 列出所有可用的代理 | [`Agent[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-1)

```
// Write a log entry

await client.app.log({

  body: {

    service: "my-app",

    level: "info",

    message: "Operation completed",

  },

})

// List available agents

const agents = await client.app.agents()
```

* * *

### [Project](06-SDK.md#project)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `project.list()` | 列出所有项目 | [`Project[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `project.current()` | 获取当前项目 | [`Project`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-2)

```
// List all projects

const projects = await client.project.list()

// Get current project

const currentProject = await client.project.current()
```

* * *

### [Path](06-SDK.md#path)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `path.get()` | 获取当前路径 | [`Path`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-3)

```
// Get current path information

const pathInfo = await client.path.get()
```

* * *

### [Config](06-SDK.md#config)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `config.get()` | 获取配置信息 | [`Config`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `config.providers()` | 列出提供商和默认模型 | `{ providers:` [`Provider[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)`, default: { [key: string]: string } }` |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-4)

```
const config = await client.config.get()

const { providers, default: defaults } = await client.config.providers()
```

* * *

### [Sessions](06-SDK.md#sessions)

| 方法 | 描述 | 备注 |
| --- | --- | --- |
| `session.list()` | 列出会话 | 返回 [`Session[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.get({ path })` | 获取会话 | 返回 [`Session`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.children({ path })` | 列出子会话 | 返回 [`Session[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.create({ body })` | 创建会话 | 返回 [`Session`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.delete({ path })` | 删除会话 | 返回 `boolean` |
| `session.update({ path, body })` | 更新会话属性 | 返回 [`Session`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.init({ path, body })` | 分析应用并创建 `AGENTS.md` | 返回 `boolean` |
| `session.abort({ path })` | 中止正在运行的会话 | 返回 `boolean` |
| `session.share({ path })` | 分享会话 | 返回 [`Session`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.unshare({ path })` | 取消分享会话 | 返回 [`Session`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.summarize({ path, body })` | 总结会话 | 返回 `boolean` |
| `session.messages({ path })` | 列出会话中的消息 | 返回 `{ info:` [`Message`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)`, parts:` [`Part[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)`}[]` |
| `session.message({ path })` | 获取消息详情 | 返回 `{ info:` [`Message`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)`, parts:` [`Part[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)`}` |
| `session.prompt({ path, body })` | 发送提示词消息 | `body.noReply: true` 返回 UserMessage（仅注入上下文）。默认返回带有 AI 响应的 [`AssistantMessage`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)。支持通过 `body.outputFormat` 使用 [结构化输出](06-SDK.md#%E7%BB%93%E6%9E%84%E5%8C%96%E8%BE%93%E5%87%BA) |
| `session.command({ path, body })` | 向会话发送命令 | 返回 `{ info:` [`AssistantMessage`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)`, parts:` [`Part[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts)`}` |
| `session.shell({ path, body })` | 执行 shell 命令 | 返回 [`AssistantMessage`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.revert({ path, body })` | 撤回消息 | 返回 [`Session`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `session.unrevert({ path })` | 恢复已撤回的消息 | 返回 [`Session`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `postSessionByIdPermissionsByPermissionId({ path, body })` | 响应权限请求 | 返回 `boolean` |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-5)

```
// Create and manage sessions

const session = await client.session.create({

  body: { title: "My session" },

})

const sessions = await client.session.list()

// Send a prompt message

const result = await client.session.prompt({

  path: { id: session.id },

  body: {

    model: { providerID: "anthropic", modelID: "claude-3-5-sonnet-20241022" },

    parts: [{ type: "text", text: "Hello!" }],

  },

})

// Inject context without triggering AI response (useful for plugins)

await client.session.prompt({

  path: { id: session.id },

  body: {

    noReply: true,

    parts: [{ type: "text", text: "You are a helpful assistant." }],

  },

})
```

* * *

### [Files](06-SDK.md#files)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `find.text({ query })` | 搜索文件中的文本 | 包含 `path`、`lines`、`line_number`、`absolute_offset`、`submatches` 的匹配对象数组 |
| `find.files({ query })` | 按名称查找文件和目录 | `string[]`（路径） |
| `find.symbols({ query })` | 查找工作区符号 | [`Symbol[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |
| `file.read({ query })` | 读取文件 | `{ type: "raw" | "patch", content: string }` |
| `file.status({ query? })` | 获取已跟踪文件的状态 | [`File[]`](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/types.gen.ts) |

`find.files` 支持以下可选查询字段：

- `type`：`"file"` 或 `"directory"`
- `directory`：覆盖搜索的项目根目录
- `limit`：最大结果数（1–200）

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-6)

```
// Search and read files

const textResults = await client.find.text({

  query: { pattern: "function.*opencode" },

})

const files = await client.find.files({

  query: { query: "*.ts", type: "file" },

})

const directories = await client.find.files({

  query: { query: "packages", type: "directory", limit: 20 },

})

const content = await client.file.read({

  query: { path: "src/index.ts" },

})
```

* * *

### [TUI](06-SDK.md#tui)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `tui.appendPrompt({ body })` | 向提示词追加文本 | `boolean` |
| `tui.openHelp()` | 打开帮助对话框 | `boolean` |
| `tui.openSessions()` | 打开会话选择器 | `boolean` |
| `tui.openThemes()` | 打开主题选择器 | `boolean` |
| `tui.openModels()` | 打开模型选择器 | `boolean` |
| `tui.submitPrompt()` | 提交当前提示词 | `boolean` |
| `tui.clearPrompt()` | 清除提示词 | `boolean` |
| `tui.executeCommand({ body })` | 执行命令 | `boolean` |
| `tui.showToast({ body })` | 显示 Toast 通知 | `boolean` |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-7)

```
// Control TUI interface

await client.tui.appendPrompt({

  body: { text: "Add this to prompt" },

})

await client.tui.showToast({

  body: { message: "Task completed", variant: "success" },

})
```

* * *

### [Auth](06-SDK.md#auth)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `auth.set({ ... })` | 设置认证凭据 | `boolean` |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-8)

```
await client.auth.set({

  path: { id: "anthropic" },

  body: { type: "api", key: "your-api-key" },

})
```

* * *

### [Events](06-SDK.md#events)

| 方法 | 描述 | 响应 |
| --- | --- | --- |
| `event.subscribe()` | 服务器发送的事件流 | 服务器发送的事件流 |

* * *

#### [示例](06-SDK.md#%E7%A4%BA%E4%BE%8B-9)

```
// Listen to real-time events

const events = await client.event.subscribe()

for await (const event of events.stream) {

  console.log("Event:", event.type, event.properties)

}
```