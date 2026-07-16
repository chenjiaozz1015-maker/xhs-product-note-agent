# LLM 灰度上线准备与观察清单

## 当前默认状态

- 线上默认保持 `CONTENT_ENGINE_TYPE=rule_based`。
- 图片引擎保持 `POSTER_ENGINE_TYPE=pillow`。
- LLM 只用于本地验证和人工评估，不自动切换线上。
- Render 不建议配置 `APP_VERSION`，版本号跟随 `app/config.py` 的代码默认值。

## 灰度前本地必须通过

在项目根目录依次执行：

```bash
python scripts/check_llm_config.py
python scripts/local_llm_rollout_check.py --skip-batch
python scripts/local_llm_rollout_check.py
python scripts/llm_gray_rollout_ready.py
```

必须确认：

- `Config check: READY`
- `Smoke check: SUCCESS`
- 单品对比结果可读
- 批量评测没有明显类目串词
- `LLM_API_KEY` 不出现在日志、页面、报告或 Git 中
- `CONTENT_ENGINE_TYPE` 仍为 `rule_based`，直到人工批准

## 人工切换步骤

本节只记录步骤，不在代码中执行。

在 Render 环境变量中设置：

```bash
CONTENT_ENGINE_TYPE=llm_openai_compatible
```

其他配置保持：

```bash
POSTER_ENGINE_TYPE=pillow
```

注意：

- 不要配置 `APP_VERSION`。
- 不要把 `LLM_API_KEY` 放进 Git、README、`.env.example` 或测试文件。
- 线上如果需要 `LLM_API_KEY`，必须通过 Render Secret / 环境变量，或后续受控配置同步机制。

## 快速回退

如果质量、稳定性、fallback 或成本异常，把 Render 环境变量从：

```bash
CONTENT_ENGINE_TYPE=llm_openai_compatible
```

改回：

```bash
CONTENT_ENGINE_TYPE=rule_based
```

然后重新部署。

## 上线后观察项

- `/health` 中的 `content_engine_type`
- `/me/records` 中的 `content_engine_type`、`fallback_used`、`fallback_reason`
- `python scripts/engine_usage_report.py` 的统计结果
- fallback 原因和 fallback 频率
- 用户是否可接受生成质量
- 是否有类目串词
- 是否有空结果
- 是否有请求失败
- 是否有成本异常

## 不建议启用 LLM 的情况

- `LLM_API_KEY` 未配置
- `local_llm_rollout_check.py` 未通过
- fallback 频率高
- 内容质量明显不稳定
- 输出过长或格式不稳定
- 密钥管理方式未确认
- 没有回退人值守
