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

## 安全原则
- 不提交 `inviteCode`
- 不提交 `.env`
- 不把真实密钥写进 `README`、`.env.example`、测试文件或日志
- `bootstrap` 是初始化动作，不建议重复执行
- 真实密钥只放本地环境变量或部署平台环境变量

## 当前仍缺少的后续接口信息
后续如果要把 `LLM_API_KEY / LLM_BASE_URL / LLM_MODEL` 从 config-center 读取，需要补充以下接口信息：

- 配置读取接口
- 配置写入接口
- 项目配置查询接口
- 鉴权方式
- 返回结构
- 错误码
- 是否支持按环境区分，例如 `local / staging / production`
- 是否支持敏感字段脱敏

## 后续计划
- 未来可以从 config-center 读取 LLM 配置
- 可以选择“本地环境变量优先，config-center 作为补充”
- 也可以选择“config-center 优先，本地环境变量兜底”
- `/health` 只显示 `configured / missing`，不暴露真实密钥
- LLM 启用前仍走 `preflight / smoke / compare / batch` 流程

## 当前结论
- 目前只完成了 bootstrap 接入
- 当前缺少配置读取接口，因此本轮不实现真实配置拉取
- 当前线上仍使用 Render 环境变量和本地环境变量作为配置来源
