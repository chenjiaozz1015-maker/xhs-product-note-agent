# 种草机运营脚本说明

## 使用前提醒
- 请在项目根目录运行脚本
- 不要提交 `.env`
- 不要提交 `data/zhongcaoji.db`
- 不要把真实 API Key、真实 inviteCode 或真实 runtimeConfigToken 写进代码、README 或 `.env.example`
- 不要把真实用户密码写进代码、README 或测试文件
- 线上默认建议保持 `CONTENT_ENGINE_TYPE=rule_based`
- 只有 `smoke_check_llm.py`、`compare_content_engines.py`、`batch_evaluate_content.py` 会在 LLM 配置完整时请求模型接口
- `bootstrap_config_center.py` 只有在传 `--yes` 且 `CONFIG_CENTER_INVITE_CODE` 存在时才会请求内部 config-center 接口
- `check_config_center_runtime.py` 会请求 config-center 的 runtime-config 接口
- 其他脚本默认只读或只做本地数据库操作

## 脚本清单

| 脚本 | 用途 | 是否请求外网 | 是否修改数据库 | 常用命令 | 适用场景 |
| --- | --- | --- | --- | --- | --- |
| `manage_user_plan.py` | 查看用户、手动开通或切换套餐 | 否 | `set-plan` 会修改；`show/list` 不修改 | `python scripts/manage_user_plan.py show --email user@example.com` | 运营查看用户状态、手动开通套餐 |
| `check_llm_config.py` | 检查 LLM 配置是否完整 | 否 | 否 | `python scripts/check_llm_config.py` | 启用 LLM 前先看配置是否齐全 |
| `preflight_llm_rollout.py` | LLM 灰度启用前只读预检 | 否 | 否 | `python scripts/preflight_llm_rollout.py` | 启用前走一遍预检清单 |
| `llm_gray_rollout_ready.py` | LLM 灰度上线前只读准备检查 | 否 | 否 | `python scripts/llm_gray_rollout_ready.py` | 判断是否进入人工灰度决策 |
| `smoke_check_llm.py` | 手动请求一次 LLM，验证真实连通性 | 是，配置完整时会请求一次 | 否 | `python scripts/smoke_check_llm.py` | 手工验证模型接口能否返回可用结果 |
| `compare_content_engines.py` | 单个商品对比 `rule_based` 和 LLM 文案 | 是，配置完整时会请求一次 | 否 | `python scripts/compare_content_engines.py` | 看单个样例的规则文案和 LLM 文案差异 |
| `batch_evaluate_content.py` | 多个样例批量评测 `rule_based` 和 LLM 文案 | 是，配置完整时会请求模型接口 | 否 | `python scripts/batch_evaluate_content.py --format markdown --output content_eval.md` | 做小样本批量质量对比 |
| `engine_usage_report.py` | 查看 `generation_records` 的内容引擎使用统计 | 否 | 否，只读 | `python scripts/engine_usage_report.py --limit 50` | LLM 启用后观察实际命中和 fallback |
| `bootstrap_config_center.py` | 调用内部 config-center bootstrap 接口初始化项目配置 | 只有 `--yes` 且 inviteCode 存在时会请求 | 否 | `python scripts/bootstrap_config_center.py --dry-run` | 首次初始化配置中心项目 |
| `check_config_center_runtime.py` | 检查 runtime token 文件并请求一次 runtime-config | 是，会请求 config-center | 否 | `python scripts/check_config_center_runtime.py` | 手动验证配置中心运行时读取是否正常 |
| `reset_user_password.py` | 运营侧重置用户登录密码 | 否 | 是，只修改指定用户密码哈希 | `python scripts/reset_user_password.py --email user@example.com --password "NewPassword123"` | 测试用户忘记密码时手动重置 |
| `list_ops_tools.py` | 打印运营脚本入口和常用命令索引 | 否 | 否 | `python scripts/list_ops_tools.py` | 快速查“该用哪个脚本” |

## 配置中心初始化
设置环境变量后运行：

```bash
python scripts/bootstrap_config_center.py --dry-run
python scripts/bootstrap_config_center.py --yes
```

说明：
- 只有传 `--yes` 且 `CONFIG_CENTER_INVITE_CODE` 存在时，才会请求内部 config-center 接口
- 成功后会尝试写入 `.config-center/test.runtime-token.json`
- `--overwrite-token` 可覆盖已有 token 文件
- 不会修改数据库
- 不会扣额度
- 不会写 `generation_records`
- 不会生成图片
- 不要提交真实 inviteCode
- 不要提交 token 文件
- `bootstrap` 是初始化动作，不建议重复执行

## 配置中心 runtime-config 读取
手动检查：

```bash
python scripts/check_config_center_runtime.py
```

说明：
- 这个脚本会读取 `.config-center/test.runtime-token.json`
- 它会请求一次 config-center 的 runtime-config 接口
- 它不会修改数据库
- 它不会扣额度
- 它不会写 `generation_records`
- 它不会生成图片
- 它不会修改 `CONTENT_ENGINE_TYPE`
- 它只打印 `config keys`，不会打印完整 `runtimeConfigToken` 或完整敏感配置值

## 运营重置用户密码
常用命令：

```bash
python scripts/reset_user_password.py --email user@example.com --password "NewPassword123"
```

说明：
- 这个脚本只修改指定用户的密码哈希
- 它不会修改套餐
- 它不会修改额度
- 它不会修改 `generation_records`
- 它不会显示明文密码
- 仅限运营人员使用

## 常见操作流程

### 1. 查看用户和开通套餐
查看用户：

```bash
python scripts/manage_user_plan.py show --email user@example.com
```

开通个人月卡：

```bash
python scripts/manage_user_plan.py set-plan --email user@example.com --plan personal
```

开通商家月卡：

```bash
python scripts/manage_user_plan.py set-plan --email user@example.com --plan business
```

查看最近用户：

```bash
python scripts/manage_user_plan.py list --limit 20
```

### 2. LLM 启用前检查
建议顺序：

```bash
python scripts/preflight_llm_rollout.py
python scripts/check_llm_config.py
python scripts/smoke_check_llm.py
python scripts/compare_content_engines.py
python scripts/batch_evaluate_content.py
python scripts/llm_gray_rollout_ready.py
```

### 2.1 LLM 灰度上线准备检查

用途：LLM 灰度上线前只读准备检查。

- 是否请求外网：否
- 是否修改数据库：否
- 是否扣额度：否
- 是否写记录：否
- 是否生成图片：否

常用命令：

```bash
python scripts/llm_gray_rollout_ready.py
python scripts/llm_gray_rollout_ready.py --json
python scripts/llm_gray_rollout_ready.py --json --output llm_gray_rollout_ready.json
```

### 3. LLM 启用后观察
查看最近记录：

```bash
python scripts/engine_usage_report.py
python scripts/engine_usage_report.py --limit 100
python scripts/engine_usage_report.py --format json
```

如果 fallback 比例明显偏高，建议把 Render 环境变量改回：

```bash
CONTENT_ENGINE_TYPE=rule_based
```

### 4. 生成评测报告
输出 Markdown 报告：

```bash
python scripts/batch_evaluate_content.py --format markdown --output content_eval.md
```

输出 JSON 报告：

```bash
python scripts/batch_evaluate_content.py --format json --output content_eval.json
```

说明：
- `content_eval.md`
- `content_eval.json`

这类评测产物不要提交到 Git。

## 内置运行时配置管理

这些脚本只管理项目本地 SQLite 的 `app_settings` 表，不请求外网，也暂不改变正式生成配置来源：

```bash
python scripts/settings_set.py --key LLM_MODEL --value "qwen-plus"
python scripts/settings_set.py --key LLM_API_KEY_REF --value "secret://project/env/providers/llm/provider/api-key"
python scripts/settings_get.py --key LLM_MODEL
python scripts/settings_get.py --key LLM_API_KEY
python scripts/settings_get.py --key LLM_API_KEY --reveal
python scripts/settings_list.py
```

- `settings_set.py`：写入或更新 `app_settings`，secret key 默认脱敏保存和输出。
- `settings_get.py`：读取单个配置，secret 默认脱敏，只有 `--reveal` 才显示明文到终端。
- `settings_list.py`：列出全部配置，secret 默认脱敏。
- 自动识别包含 `API_KEY`、`TOKEN`、`SECRET`、`PASSWORD`、`PRIVATE_KEY` 的 key 为 secret；可用 `--plain` 明确覆盖。
- 不要把真实 API Key 写入 README、`.env.example` 或 Git。当前 `app_settings` 不直接控制正式 LLM 流程。

## LLM 配置来源

LLM 相关配置读取顺序为：环境变量 > `app_settings` > 代码默认值。可通过以下命令写入本地配置：

```bash
python scripts/settings_set.py --key LLM_MODEL --value "qwen-plus"
python scripts/settings_set.py --key LLM_BASE_URL --value "https://your-compatible-api.example/v1"
不要使用 `settings_set.py` 写入 `LLM_API_KEY` 明文；API Key 应由受保护环境变量或 secret-material 提供。
python scripts/check_llm_config.py
```

检查脚本和 preflight 会显示每个配置的来源以及 `configured / missing` 状态，不会显示完整 secret。正式线上仍建议在 Render 保持 `CONTENT_ENGINE_TYPE=rule_based`，本轮不会自动启用 LLM。

## 本地 LLM 灰度验证

```bash
python scripts/local_llm_rollout_check.py
python scripts/local_llm_rollout_check.py --skip-smoke
python scripts/local_llm_rollout_check.py --skip-compare
python scripts/local_llm_rollout_check.py --skip-batch
python scripts/local_llm_rollout_check.py --format json --output local_llm_rollout_report.json
```

该脚本只读本地 `app_settings`。配置不完整时不会请求 LLM；配置完整且未跳过时才会执行 smoke、单品对比和批量评测。它不修改 `CONTENT_ENGINE_TYPE`，不扣额度、不写 `generation_records`、不生成图片、不请求 config-center。报告文件已加入 `.gitignore`，不要提交真实密钥。

## Config-center secret-material

用途：使用 runtime token 手动拉取 config-center 的 secret-material env 内容到本地文件。

- 是否请求外网：是，仅手动执行且非 `--dry-run` 时请求。
- 是否修改数据库：否。
- 是否写文件：是，默认写入 `.config-center/test.secret-material.env`。
- 是否打印 secret：否。

```bash
python scripts/fetch_config_center_secret_material.py --dry-run
python scripts/fetch_config_center_secret_material.py
python scripts/fetch_config_center_secret_material.py --overwrite
```

runtime token 缺失、文件已存在且未指定 `--overwrite`、或接口返回无法识别的内容时，脚本不会写文件。secret-material 文件已加入 `.gitignore`，不要提交。
