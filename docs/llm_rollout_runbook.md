# LLM 灰度启用 Runbook

## 当前默认状态
- 线上默认推荐：
  - `CONTENT_ENGINE_TYPE=rule_based`
  - `POSTER_ENGINE_TYPE=pillow`
- `APP_VERSION` 不需要在 Render 单独配置，版本号跟随 `app/config.py` 里的代码默认值

## 启用 LLM 前必须确认
按顺序执行：

1. `python scripts/check_llm_config.py`
   - 只检查配置，不请求外网
2. `python scripts/smoke_check_llm.py`
   - 手动请求一次模型接口，验证连通性
3. `python scripts/compare_content_engines.py`
   - 单商品对比 `rule_based` 和 `LLM` 文案
4. `python scripts/batch_evaluate_content.py`
   - 多样例批量对比 `rule_based` 和 `LLM` 文案

## Render 环境变量配置
启用前需要配置：

- `CONTENT_ENGINE_TYPE=llm_openai_compatible`
- `LLM_PROVIDER=openai_compatible`
- `LLM_API_KEY=真实密钥`
- `LLM_BASE_URL=模型平台兼容接口地址`
- `LLM_MODEL=模型名称`
- `LLM_TIMEOUT_SECONDS=15`
- `LLM_MAX_RETRIES=1`
- `POSTER_ENGINE_TYPE=pillow`

注意：
- 不要配置 `APP_VERSION`
- 不要把真实密钥写进代码、README、`.env.example` 或提交到 Git

## 启用后观察项
至少观察以下项目：

- `/health` 中 `content_engine_type` 是否为 `llm_openai_compatible`
- `/health` 中 `llm_config_ready` 是否为 `true`
- 结果页内容引擎来源是否显示 `LLM 生成`
- 是否出现 `规则引擎（LLM 不可用，已自动回退）`
- 生成是否仍然只扣 1 次额度
- 生成记录是否仍然只写 1 条
- 图片是否仍然生成 3 张
- 页面是否没有 500 错误
- 文案是否有类目跑偏
- 文案是否有夸大功效、医疗、减肥、保证效果等风险表述

## 建议验收样例
建议至少检查这 8 个样例：

- 水牛奶蛋糕
- 挂耳咖啡
- 护手霜
- 口红
- 保温杯
- 收纳盒
- 厨房清洁湿巾
- 坚果零食

每个样例观察：
- 标题自然度
- 类目贴合度
- 正文真实感
- 标签可用性
- 是否跑偏
- 是否出现夸大表达
- 是否比 `rule_based` 更好

## 快速回退方式
如果发现问题，在 Render 把：

- `CONTENT_ENGINE_TYPE=llm_openai_compatible`

改回：

- `CONTENT_ENGINE_TYPE=rule_based`

然后重新部署，或等待环境变量生效。

回退后检查：

1. `/health` 中 `content_engine_type` 是否回到 `rule_based`
2. 重新生成 1 次商品，确认结果页显示规则引擎
3. 确认页面仍能正常生成图片和文案

## 不建议启用 LLM 的情况
- `smoke_check_llm.py` 不成功
- `batch_evaluate_content.py` 中多个样例跑偏
- LLM 经常 timeout
- fallback 频率高
- 文案出现夸大功效或类目串词
- 模型接口不稳定
- 费用不可控
- API Key 权限或额度不清楚

## 灰度建议
- 不要一开始给所有真实客户使用
- 先用内部账号测试
- 每天少量样例观察
- 确认稳定后再考虑保持 `llm_openai_compatible`
- 如果客户反馈不好，立刻切回 `rule_based`
