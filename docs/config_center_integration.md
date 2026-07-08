# Config Center Integration

## 当前已完成
- 已完成 `projectCode=zhongcaoji` 的 config-center bootstrap
- bootstrap 接口：
  - `POST http://39.106.61.160:28081/internal/config-center/v1/projects/bootstrap`
- 当前 bootstrap 约定：
  - `projectCode=zhongcaoji`
  - `runtime=python`
  - `localWorkspaceRoot=D:\projects\xhs-product-note-agent`
- `inviteCode` 只通过环境变量 `CONFIG_CENTER_INVITE_CODE` 传入

## 供应商已明确的运行时规则
- 不要人工要求提供 runtimeConfigToken 文件
- 如果 token 文件缺失，需要重新按新版 bootstrap 流程执行
- `inviteCode` 只用于首次 bootstrap，不能用于运行时拉配置
- bootstrap 成功后，脚本应自动写入 `.config-center/test.runtime-token.json`
- 运行时 token 文件路径：
  - `.config-center/test.runtime-token.json`
- 运行时读取接口：
  - `GET http://39.106.61.160:28081/internal/config-center/v1/projects/zhongcaoji/runtime-config?env=test`
- Header：
  - `X-Project-Config-Token: <runtimeConfigToken>`
- `runtime-config` 返回的是基础项目配置，不是完整能力配置
- 支付中台、文件中台等能力后续走 `middle-platform-access-requests`
- 自建支付、OSS、MQ、短信等完整能力后续走 `resource-requests`

## 安全原则
- 不提交 `inviteCode`
- 不提交 `runtimeConfigToken`
- 不提交 `.env`
- 不提交 `.config-center/test.runtime-token.json`
- 不把真实密钥写进 `README`、`.env.example`、测试文件或日志
- `bootstrap` 是初始化动作，不建议重复执行
- 真实密钥只放本地环境变量或部署平台环境变量

## 当前 runtime-config 接入边界
- 当前已接入 runtime-config 读取能力
- 当前只做“安全读取、诊断、测试”
- 当前不把 config-center 配置直接切进正式 LLM 配置来源
- 当前线上仍使用 Render 环境变量和本地环境变量作为配置来源
- 当前不修改 `CONTENT_ENGINE_TYPE`
- 当前不改正式生成流程

## 重新获取 runtime token 的方式
如果 `check_config_center_runtime.py` 提示 `runtime_token_file_missing`，重新执行：

```bash
python scripts/bootstrap_config_center.py --yes
```

如果需要覆盖已有 token：

```bash
python scripts/bootstrap_config_center.py --yes --overwrite-token
```

## 当前仍缺少的后续接口信息
后续如果要把 `LLM_API_KEY / LLM_BASE_URL / LLM_MODEL` 从 config-center 读取，需要补充以下接口信息：

- 配置读取接口的完整返回结构
- 配置写入接口
- 项目配置查询接口
- 鉴权方式
- 错误码
- 是否支持按环境区分，例如 `local / staging / production`
- 是否支持敏感字段脱敏

## 后续计划
- 未来可以从 config-center 读取 LLM 配置
- 可以选择“本地环境变量优先，config-center 作为补充”
- 也可以选择“config-center 优先，本地环境变量兜底”
- `/health` 只显示安全摘要，不暴露真实密钥
- LLM 启用前仍走 `preflight / smoke / compare / batch` 流程
