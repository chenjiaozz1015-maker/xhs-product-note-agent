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
