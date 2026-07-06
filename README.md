# 种草机
`xhs-product-note-agent`

上传商品图片、商品名称、商品类目和一句描述，自动生成小红书风格图片素材包与发布文案。

## 当前版本
种草机 v0.4-3 类目词库增强版

## 在线试用
https://zhongcaoji.onrender.com/

## 当前能力
- 用户注册、登录、退出
- trial / personal / business 套餐配置与额度生效
- 生成成功后扣减额度并写入生成记录
- 首页显示剩余额度、下次重置时间、最近记录
- `/pricing` 套餐展示页
- `/me/records` 使用记录页
- 通过 `poster_engine_adapter.py` + `pillow` 生成 3 张图片
- 结果页支持下载、复制、编辑标题/正文/标签/评论引导

## v0.4-3 本轮增强
- 新增商品细分类目识别逻辑，集中在 `app/services/category_profile.py`
- 食品饮品细分为：`bakery`、`drink`、`snack`、`light_meal`
- 美妆护肤细分为：`skincare`、`makeup`、`hand_body_care`、`portable_care`
- 家居日用细分为：`cup_bottle`、`storage`、`cleaning`、`desktop_commute`
- 标题、正文、标签、评论引导、图片卖点统一复用细分类目词库
- 继续使用规则引擎，不接大模型，不接外部 GitHub 图片引擎
- 不影响账号、额度、套餐、生成记录和运营脚本链路

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
- 当前 v0.4-3 不下载外部代码，不接真实外部海报引擎

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

## /health 版本说明
`/health` 返回的 `version` 优先读取 `APP_VERSION` 环境变量，代码默认值为 `v0.4-3`。
如果 Render 线上 `/health` 仍显示旧版本，请检查 Render Environment 里的 `APP_VERSION`，改为 `v0.4-3` 或删除该环境变量后重新部署。

## 版本记录
- v0.4-3：新增或增强商品细分类目识别；食品饮品细分为烘焙糕点、饮品冲泡、零食小吃、代餐轻食；美妆护肤细分为护肤、彩妆、护手霜/身体护理、随身补涂；家居日用细分为杯壶水杯、收纳整理、清洁用品、桌面/通勤好物；标题、正文、标签和图片卖点统一根据细分类目调整；继续使用规则引擎，不接大模型。
- v0.4-2：增强内置 Pillow 图片模板质量，强化封面图、卖点图、清单总结图三类图片结构，增强五种风格差异，优化商品图占比、标题层级、标签和轻量装饰。
- v0.4-1：增强 `poster_engine_adapter.py`，新增 `POSTER_ENGINE_TYPE` 配置，统一图片生成引擎入口，预留 `external_placeholder`。
