# 种草机
`xhs-product-note-agent`

上传商品图片、商品名称、商品类目和一句描述，自动生成小红书风格图片素材包与发布文案。

## 当前版本
种草机 v0.5-5 LLM 文案对比版

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

## v0.5-5 本轮增强
- 新增 `scripts/compare_content_engines.py`
- 支持同一商品输入下对比 `rule_based` 与 `llm_openai_compatible` 文案
- LLM 配置不完整时自动 `SKIPPED`
- LLM 失败时不影响 `rule_based` 结果
- 对比脚本不扣额度、不写生成记录、不生成图片、不修改数据库
- 线上默认仍建议使用 `CONTENT_ENGINE_TYPE=rule_based`
- Render 不再需要配置 `APP_VERSION`，版本号跟随代码默认值

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
`/health` 返回的 `version` 默认读取 `app/config.py` 里的代码版本，当前默认值为 `v0.5-5`。
`APP_VERSION` 只作为可选覆盖项。

部署建议：
- Render 默认不要配置 `APP_VERSION`
- 版本升级时直接随代码发布即可
- 只有在极少数需要临时覆盖展示版本时，才手动增加 `APP_VERSION`

如果 Render 线上 `/health` 仍显示旧版本，优先检查 Render Environment 里是否配置过 `APP_VERSION`；如果配过，建议删除该环境变量后重新部署，让版本号回到代码默认值。

## 版本记录
- v0.5-5：新增 `scripts/compare_content_engines.py`；支持同一商品输入下对比 `rule_based` 与 `llm_openai_compatible` 文案；LLM 配置不完整时自动 `SKIPPED`；LLM 失败时不影响 `rule_based` 结果；对比脚本不扣额度、不写生成记录、不生成图片、不修改数据库；线上默认仍建议使用 `CONTENT_ENGINE_TYPE=rule_based`；Render 不再需要配置 `APP_VERSION`，版本号跟随代码默认值。
- v0.5-4：新增 `scripts/smoke_check_llm.py`；支持人工手动测试国产 OpenAI-compatible 模型接口连通性；smoke check 只生成文案测试结果，不扣额度、不写生成记录、不生成图片；不影响用户主流程；API Key 只做 masked 展示；线上默认仍建议使用 `rule_based`。
- v0.5-3：增强 LLM 配置校验；新增 `scripts/check_llm_config.py`；优化国产模型 OpenAI-compatible prompt；增强 LLM JSON 清洗和结构校验；在配置缺失、超时、非法 JSON、schema 不完整等情况下继续 fallback 到 `rule_based`；`/health` 增加 LLM 配置状态摘要；不提交真实密钥，不默认启用 LLM。
- v0.5-2：新增 `llm_content_service.py`；`CONTENT_ENGINE_TYPE` 新增 `llm_openai_compatible`；增加 OpenAI-compatible 风格 LLM 所需环境变量；通过 `content_engine_adapter.py` 统一接入规则文案与 LLM 文案；这里的 `openai_compatible` 指兼容 OpenAI 风格接口协议，而不是绑定 OpenAI 官方服务；后续可通过 `LLM_BASE_URL / LLM_MODEL / LLM_API_KEY` 接入国产模型平台；在密钥缺失、URL 无效、超时、非 JSON、字段不完整等情况下自动 fallback 到 `rule_based`；不影响图片生成、账号、额度、套餐、生成记录与运营脚本。
- v0.5-1：新增 `content_engine_adapter.py`；新增 `CONTENT_ENGINE_TYPE` 配置；当前默认 `rule_based`；预留 `llm_placeholder` 大模型文案引擎占位；当前不接真实 OpenAI / DeepSeek / 通义千问 API；当前规则文案仍由 `content_generator.py + category_profile.py` 提供；未来可通过 adapter 接入大模型，失败时 fallback 到 `rule_based`；不影响图片生成、账号、额度、套餐、生成记录和运营脚本。
- v0.4-3：新增或增强商品细分类目识别；食品饮品细分为烘焙糕点、饮品冲泡、零食小吃、代餐轻食；美妆护肤细分为护肤、彩妆、护手霜/身体护理、随身补涂；家居日用细分为杯壶水杯、收纳整理、清洁用品、桌面/通勤好物；标题、正文、标签和图片卖点统一根据细分类目调整；继续使用规则引擎，不接大模型。
- v0.4-2：增强内置 Pillow 图片模板质量，强化封面图、卖点图、清单总结图三类图片结构，增强五种风格差异，优化商品图占比、标题层级、标签和轻量装饰。
- v0.4-1：增强 `poster_engine_adapter.py`，新增 `POSTER_ENGINE_TYPE` 配置，统一图片生成引擎入口，预留 `external_placeholder`。
