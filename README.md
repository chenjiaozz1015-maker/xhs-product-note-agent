# 种草机
`xhs-product-note-agent`

上传商品图片、商品名称、商品类目和一句描述，自动生成小红书风格图片素材包与发布文案。

## 当前版本
种草机 v0.6-3 内容引擎记录版

## 在线试用
https://zhongcaoji.onrender.com/

## 当前能力
- 用户注册、登录、退出
- `trial / personal / business` 套餐配置与额度生效
- 生成成功后扣减额度并写入生成记录
- 首页显示剩余额度、下次重置时间、最近记录
- `/pricing` 套餐展示页
- `/me/records` 使用记录页
- 通过 `poster_engine_adapter.py` + `pillow` 生成 3 张图片
- 结果页支持下载、复制、编辑标题/正文/标签/评论引导
- 当前内容生成已支持规则引擎与 OpenAI-compatible 风格 LLM 最小接入

## v0.6-3 本轮增强
- `generation_records` 新增内容引擎记录字段：`requested_engine_type / content_engine_type / content_fallback_used / content_fallback_reason`
- 旧数据库会在应用启动时自动补齐缺失列，不需要手动迁移或重建数据库
- 生成成功后会把本次文案使用的内容引擎、是否发生 fallback、fallback 原因码写入生成记录
- `/me/records` 新增最近 30 条内容引擎摘要，可观察总条数、LLM 生成条数、规则引擎条数和自动回退条数
- 记录页每条记录会显示内容引擎来源，旧记录没有这些字段时也能安全展示
- 仍然只扣 1 次额度、只写 1 条生成记录，不影响图片生成、下载、复制和编辑流程
- Render 仍建议不要配置 `APP_VERSION`，版本号默认跟随代码版本

## 当前额度规则
- `trial` 默认 10 次 / 30 天
- `personal` 默认 100 次 / 30 天
- `business` 默认 500 次 / 30 天
- 周期从注册成功时间开始计算，不是自然月
- `quota_reset_at = 注册成功时间 + 30 天`
- 到期后读取额度时自动重置 `used_quota = 0`
- 当前不接真实支付，不做订单，不做后台升级生效

## 海报引擎说明
- 当前默认引擎：`pillow`
- 统一入口：`app/services/poster_engine_adapter.py`
- 可配置：`POSTER_ENGINE_TYPE=pillow`
- 预留：`external_placeholder`
- 当前不下载外部代码，不接真实外部海报引擎

## 内容引擎说明
- 当前默认引擎：`rule_based`
- 统一入口：`app/services/content_engine_adapter.py`
- 可配置：
  - `CONTENT_ENGINE_TYPE=rule_based`
  - `CONTENT_ENGINE_TYPE=llm_placeholder`
  - `CONTENT_ENGINE_TYPE=llm_openai_compatible`
- 当前真实可接入方式：`LLM_PROVIDER=openai_compatible`
- 这里的 `openai_compatible` 指“兼容 OpenAI 风格接口协议”，不限定 OpenAI 官方服务
- 后续可通过配置 `LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY` 接入国产模型平台，例如 DeepSeek、通义千问 Qwen、智谱 GLM、Kimi、豆包、腾讯混元等
- 当前实现没有写死官方域名、官方模型名，也不依赖 openai SDK
- 规则引擎保留为默认和兜底方案
- 当前如果 LLM 调用失败，会自动回退到规则文案，避免影响主流程

## 国产模型接入准备说明
- 当前推荐继续使用 `CONTENT_ENGINE_TYPE=rule_based` 作为线上默认
- 若要启用国产模型兼容接口，设置 `CONTENT_ENGINE_TYPE=llm_openai_compatible`
- 同时配置：
  - `LLM_PROVIDER=openai_compatible`
  - `LLM_BASE_URL`
  - `LLM_MODEL`
  - `LLM_API_KEY`
- 不要把真实密钥写入代码或提交到 Git
- 建议先运行：
```bash
python scripts/check_llm_config.py
```
- 配置完整不代表真实 API 一定可用，这一轮只做本地配置诊断，不做真实外网连通测试
- 若 LLM 失败，系统会自动 fallback 到 `rule_based`

## LLM 手动连通测试
先检查配置：
```bash
python scripts/check_llm_config.py
```

再手动 smoke check：
```bash
python scripts/smoke_check_llm.py
```

也可以传测试商品参数：
```bash
python scripts/smoke_check_llm.py --product-name "水牛奶蛋糕" --category "食品饮品" --description "适合早餐和下午茶，口感松软，适合家里囤一点" --content-type "真实测评" --style "温柔日常"
```

说明：
- `check_llm_config.py`：只读配置检查，不请求外网
- `smoke_check_llm.py`：手动连通测试，会请求一次模型接口
- `SUCCESS` 表示模型返回结构可用
- `FAILED` 表示请求或解析失败
- `SKIPPED` 表示配置不完整，未发请求
- smoke check 通过后，仍建议先本地观察，再考虑把 `CONTENT_ENGINE_TYPE` 切换到 `llm_openai_compatible`
- 不要把真实 `API Key` 写入代码或提交到 Git
- Render / 云平台通过环境变量配置即可
- `APP_VERSION` 建议不要在 Render 单独配置，默认直接使用 `app/config.py` 中的代码版本
- 只有确实需要临时覆盖版本展示时，才额外配置 `APP_VERSION`

## 文案引擎对比脚本
默认运行：
```bash
python scripts/compare_content_engines.py
```

指定商品：
```bash
python scripts/compare_content_engines.py --product-name "保温杯" --category "家居日用" --description "通勤带着方便，容量刚好"
python scripts/compare_content_engines.py --product-name "护手霜" --category "美妆护肤" --description "秋冬随身带，不黏腻，适合通勤补涂"
```

使用前建议先运行：
```bash
python scripts/check_llm_config.py
python scripts/smoke_check_llm.py
```

说明：
- `compare_content_engines.py` 会先生成一份 `rule_based` 文案
- 如果 LLM 配置完整，会再请求一次模型接口生成 `llm_openai_compatible` 文案
- 如果 LLM 配置不完整，会显示 `SKIPPED`，同时保留 `rule_based` 结果
- 如果 LLM 请求失败，会显示 `FAILED`，同时保留 `rule_based` 结果
- 它不走用户生成流程，不扣额度，不写记录，不生成图片，不修改数据库
- 默认只在终端打印结果；如需保存，可配合 `--output` 输出 JSON
- 不要提交 `.env` 或真实 `API Key`

## 小样本文案批量评测
默认运行：
```bash
python scripts/batch_evaluate_content.py
```

保存 Markdown：
```bash
python scripts/batch_evaluate_content.py --format markdown --output content_eval.md
```

保存 JSON：
```bash
python scripts/batch_evaluate_content.py --format json --output content_eval.json
```

可选只看某一侧：
```bash
python scripts/batch_evaluate_content.py --only rule_based
python scripts/batch_evaluate_content.py --only llm
```

说明：
- 这个脚本用于人工评估文案质量
- 它会用内置小样本批量生成 `rule_based` 结果
- 当 LLM 配置完整时，会额外请求模型接口生成 `llm_openai_compatible` 结果
- 当 LLM 配置不完整时，所有样例都会显示 `SKIPPED`，并且不会请求外网
- 单个样例 LLM 失败不会影响其他样例继续执行
- 它不走用户生成流程，不扣额度，不写记录，不生成图片，不修改数据库
- 运行前建议先执行：
```bash
python scripts/check_llm_config.py
python scripts/smoke_check_llm.py
```
- 不要提交 `.env`、真实 `API Key`、`content_eval.md`、`content_eval.json`


## 内容引擎记录观察
- 成功生成后，`generation_records` 会记录：
  - `requested_engine_type`：本次请求想使用的内容引擎
  - `content_engine_type`：本次实际落地使用的内容引擎
  - `content_fallback_used`：是否发生自动回退
  - `content_fallback_reason`：回退原因码，例如 `llm_timeout`
- `/me/records` 页面会显示最近 30 条记录的内容引擎摘要
- 旧记录如果没有这些字段或值为空，会显示“旧记录未标注”
- 这里只记录安全的原因码，不展示完整异常、密钥或外部服务敏感信息
## 如何安全启用 LLM
线上默认保持：
```bash
CONTENT_ENGINE_TYPE=rule_based
```

启用前建议依次运行：
```bash
python scripts/check_llm_config.py
python scripts/smoke_check_llm.py
python scripts/compare_content_engines.py
python scripts/batch_evaluate_content.py
```

确认效果稳定后，再把环境变量改为：
```bash
CONTENT_ENGINE_TYPE=llm_openai_compatible
```

说明：
- 正式 `POST /generate` 流程现在已经支持在配置完整时尝试 LLM
- 如果 LLM 不可用、超时、返回非法 JSON 或 schema 不兼容，会自动回退到 `rule_based`
- 用户不应该看到报错页
- 结果页只会轻量显示“规则引擎 / LLM 生成 / 已自动回退”
- 回退后仍然只扣 1 次额度、只写 1 条生成记录

## LLM 灰度启用流程
默认保持：
```bash
CONTENT_ENGINE_TYPE=rule_based
```

准备启用前，建议顺序执行：
```bash
python scripts/preflight_llm_rollout.py
python scripts/check_llm_config.py
python scripts/smoke_check_llm.py
python scripts/compare_content_engines.py
python scripts/batch_evaluate_content.py
```

结论可接受后，再去 Render 把：
```bash
CONTENT_ENGINE_TYPE=llm_openai_compatible
```

如果上线后发现问题，立即改回：
```bash
CONTENT_ENGINE_TYPE=rule_based
```

更完整的操作步骤见：
```text
docs/llm_rollout_runbook.md
```

## LLM 最小接入配置
```bash
CONTENT_ENGINE_TYPE=llm_openai_compatible
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-openai-compatible-host/v1
LLM_MODEL=your-model-name
LLM_TIMEOUT_SECONDS=15
LLM_MAX_RETRIES=1
```

说明：
- `LLM_BASE_URL` 可以填到 `/v1`，系统会自动补成 `/chat/completions`
- `openai_compatible` 表示兼容 OpenAI 风格接口的模型服务，不限定 OpenAI 官方服务
- 后续可以把 `LLM_BASE_URL / LLM_MODEL / LLM_API_KEY` 配成国产模型平台提供的兼容接口
- 当前不提交任何真实密钥
- 若 `LLM_BASE_URL`、`LLM_MODEL` 或 `LLM_API_KEY` 为空，会直接 fallback 到 `rule_based`
- 若返回超时、非 200、非 JSON、字段缺失或结构不兼容，也会自动退回 `rule_based`
- 当前不会在页面暴露密钥等敏感信息

## 中心化运营脚本
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

切回试用账号：
```bash
python scripts/manage_user_plan.py set-plan --email user@example.com --plan trial
```

查看最近用户：
```bash
python scripts/manage_user_plan.py list --limit 20
```

说明：
- 脚本操作当前服务器上的 `data/zhongcaoji.db`
- 当前只支持 `trial / personal / business`
- 修改 plan 后会复用服务层同步 `monthly_quota`
- `used_quota` 保留，不清空历史使用

## 本地启动
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
```text
http://127.0.0.1:8000/
```

## 测试
```bash
py -m pytest -q
```

如果 Windows 临时目录权限有问题，可以使用：
```bash
py -m pytest -q --basetemp .tmp/pytest
```

## /health 版本说明
`/health` 返回的 `version` 默认读取 `app/config.py` 里的代码版本，当前默认值为 `v0.6-3`。
`APP_VERSION` 只作为可选覆盖项。

部署建议：
- Render 默认不要配置 `APP_VERSION`
- 版本升级时直接随代码发布即可
- 只有在极少数需要临时覆盖展示版本时，才手动增加 `APP_VERSION`

如果 Render 线上 `/health` 仍显示旧版本，优先检查 Render Environment 里是否配置过 `APP_VERSION`；如果配过，建议删除该环境变量后重新部署，让版本号回到代码默认值。

## 版本记录
- v0.6-3：`generation_records` 新增内容引擎使用记录字段；旧数据库自动补齐缺失列；成功生成后记录 requested / actual / fallback 元信息；`/me/records` 新增最近 30 条内容引擎摘要与每条记录的来源显示；旧记录空字段安全兼容；仍然只扣 1 次额度、只写 1 条生成记录；Render 仍建议不要配置 `APP_VERSION`。
- v0.6-2：新增 `docs/llm_rollout_runbook.md`；新增 `scripts/preflight_llm_rollout.py`；明确 LLM 灰度启用前检查流程、Render 环境变量启用方式、启用后观察项和快速回退到 `rule_based` 的方式；默认仍为 `rule_based`；不请求外网，不扣额度，不写记录，不生成图片，不修改数据库；不提交真实 API Key。
- v0.6-1：正式生成流程支持通过 `CONTENT_ENGINE_TYPE` 可控启用 `llm_openai_compatible`；默认仍然是 `rule_based`；LLM 配置不完整或请求失败时自动 fallback 到 `rule_based`；`ContentGenerateResult` 增加 requested / actual / fallback 元信息；结果页可轻量显示内容引擎来源；不重复扣额度，不重复写生成记录，不影响图片生成，不暴露 API Key；Render 不需要配置 `APP_VERSION`，版本号跟随代码默认值。
- v0.5-6：新增 `scripts/batch_evaluate_content.py`；支持内置小样本批量对比 `rule_based` 与 `llm_openai_compatible`；支持终端输出、Markdown 报告和 JSON 报告；LLM 配置不完整时整体 `SKIPPED` 且不请求外网；单个样例 LLM 失败不影响其他样例；不扣额度、不写生成记录、不生成图片、不修改数据库；线上默认仍建议使用 `CONTENT_ENGINE_TYPE=rule_based`；Render 不需要配置 `APP_VERSION`，版本号跟随代码默认值。
- v0.5-5：新增 `scripts/compare_content_engines.py`；支持同一商品输入下对比 `rule_based` 与 `llm_openai_compatible` 文案；LLM 配置不完整时自动 `SKIPPED`；LLM 失败时不影响 `rule_based` 结果；对比脚本不扣额度、不写生成记录、不生成图片、不修改数据库；线上默认仍建议使用 `CONTENT_ENGINE_TYPE=rule_based`；Render 不再需要配置 `APP_VERSION`，版本号跟随代码默认值。
- v0.5-4：新增 `scripts/smoke_check_llm.py`；支持人工手动测试国产 OpenAI-compatible 模型接口连通性；smoke check 只生成文案测试结果，不扣额度、不写生成记录、不生成图片；不影响用户主流程；API Key 只做 masked 展示；线上默认仍建议使用 `rule_based`。
- v0.5-3：增强 LLM 配置校验；新增 `scripts/check_llm_config.py`；优化国产模型 OpenAI-compatible prompt；增强 LLM JSON 清洗和结构校验；在配置缺失、超时、非法 JSON、schema 不完整等情况下继续 fallback 到 `rule_based`；`/health` 增加 LLM 配置状态摘要；不提交真实密钥，不默认启用 LLM。
- v0.5-2：新增 `llm_content_service.py`；`CONTENT_ENGINE_TYPE` 新增 `llm_openai_compatible`；增加 OpenAI-compatible 风格 LLM 所需环境变量；通过 `content_engine_adapter.py` 统一接入规则文案与 LLM 文案；这里的 `openai_compatible` 指兼容 OpenAI 风格接口协议，而不是绑定 OpenAI 官方服务；后续可通过 `LLM_BASE_URL / LLM_MODEL / LLM_API_KEY` 接入国产模型平台；在密钥缺失、URL 无效、超时、非 JSON、字段不完整等情况下自动 fallback 到 `rule_based`；不影响图片生成、账号、额度、套餐、生成记录与运营脚本。
- v0.5-1：新增 `content_engine_adapter.py`；新增 `CONTENT_ENGINE_TYPE` 配置；当前默认 `rule_based`；预留 `llm_placeholder` 大模型文案引擎占位；当前不接真实 OpenAI / DeepSeek / 通义千问 API；当前规则文案仍由 `content_generator.py + category_profile.py` 提供；未来可通过 adapter 接入大模型，失败时 fallback 到 `rule_based`；不影响图片生成、账号、额度、套餐、生成记录和运营脚本。
- v0.4-3：新增或增强商品细分类目识别；食品饮品细分为烘焙糕点、饮品冲泡、零食小吃、代餐轻食；美妆护肤细分为护肤、彩妆、护手霜/身体护理、随身补涂；家居日用细分为杯壶水杯、收纳整理、清洁用品、桌面/通勤好物；标题、正文、标签和图片卖点统一根据细分类目调整；继续使用规则引擎，不接大模型。
- v0.4-2：增强内置 Pillow 图片模板质量，强化封面图、卖点图、清单总结图三类图片结构，增强五种风格差异，优化商品图占比、标题层级、标签和轻量装饰。
- v0.4-1：增强 `poster_engine_adapter.py`，新增 `POSTER_ENGINE_TYPE` 配置，统一图片生成引擎入口，预留 `external_placeholder`。


