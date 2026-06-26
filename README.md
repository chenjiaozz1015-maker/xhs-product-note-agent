# 种草机

`xhs-product-note-agent`

上传商品照片、商品名称、商品类目和一句描述，自动生成小红书风格图片素材包和发布文案。

## 当前版本
种草机 v0.1-8 本地 MVP

## 适合谁
- 普通小红书好物分享用户
- 小商家
- 初级内容创作者
- 宝妈 / 探店 / 测评类账号
- 想快速把商品照片变成可发布图文的人

## 当前已实现
- 上传商品图片
- 商品图片预览
- 填写商品名称
- 选择商品类目
- 填写一句商品描述
- 选择内容类型和风格
- 根据商品类目生成更相关的标题、正文、标签、评论引导
- 生成 3 张小红书风格图片
  - 封面图
  - 卖点 / 体验图
  - 总结推荐图
- 点击大图预览
- 下载单张图片
- 下载全部图片
- 复制标题、正文、标签、评论引导、全部发布文案
- 中文字体渲染修复
- 基础错误提示
- 生成按钮 loading / disabled
- 移动端适配

## 当前未实现
- AI 大模型文案
- 图片识别
- 自动识别商品类目
- 登录
- 支付
- 数据库
- 后端 ZIP 打包
- 自动发布小红书
- 视频生成
- 商品库
- 多模板系统

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

## 目录结构
```text
app/
  routes/        页面和生成接口
  services/      文案生成、笔记组织、图片合成
  templates/     HTML 模板
  static/        CSS、JS、上传和生成图片目录
tests/           测试
third_party/     后续预留外部海报引擎
README.md
requirements.txt
```

## 运行文件说明
运行时上传图片和生成图片会写入：

- `app/static/uploads/`
- `app/static/generated/`

这些运行文件已通过 `.gitignore` 排除，目录中的 `.gitkeep` 可保留进入 Git。

## 健康检查
```text
GET /health
```

示例返回：

```json
{
  "status": "ok",
  "app": "zhongcaoji",
  "version": "v0.1-8",
  "uploads_dir_exists": true,
  "generated_dir_exists": true,
  "static_dir_exists": true,
  "css_file_exists": true,
  "js_file_exists": true,
  "font_file_exists": true,
  "font_path": "/usr/share/fonts/..."
}
```

## 线上部署中文字体
Pillow 生成图片时需要可用的中文字体，否则中文可能显示成方块。

字体查找顺序：

1. 优先使用项目内 `app/static/fonts/` 中的字体
2. 其次使用 Linux 系统已安装的 CJK 字体
3. 最后使用 Windows 本地开发环境字体

如果 Render 环境没有中文字体，可以将开源授权字体放到 `app/static/fonts/`。推荐字体：

- Noto Sans SC
- Noto Sans CJK
- Source Han Sans SC

不要提交未经授权的商业字体。

Render 当前如果 `/health` 返回 `font_file_exists=false`、`font_path=null`，请手动下载开源授权字体 `Noto Sans SC Regular`，优先放到：

```text
app/static/fonts/NotoSansSC-Regular.ttf
```

也支持：

```text
app/static/fonts/NotoSansSC-Regular.otf
```

不要把 zip 包或解压目录直接提交到 `app/static/fonts/`。

放置后确认：

```bash
git status --short
py -m pytest -q
```

然后提交并重新部署。部署后 `/health` 中应显示：

```json
{
  "font_file_exists": true,
  "font_path": "/opt/render/project/src/app/static/fonts/NotoSansSC-Regular.ttf"
}
```

## 后续部署建议
当前项目适合部署到 Render、Railway、腾讯云轻量服务器等平台。

- 线上环境需要可写的 `app/static/uploads/` 和 `app/static/generated/` 目录
- 当前没有登录和数据库，适合小范围试用
- 免费平台可能会清理本地生成文件
- 后续正式版应考虑对象存储或云存储

## 试用注意事项
- 当前是本地 MVP，不代表最终产品
- 生成图片基于模板排版，商品图保持原样不重绘
- 文案基于规则模板，不是大模型生成
- 类目需要用户手动选择
- 暂不自动发布小红书
- 建议先用于小范围内部试用

## 版本记录
- v0.1：本地 MVP，上传图片并生成图文
- v0.1-1：上传预览、lightbox、复制反馈、图片模板优化
- v0.1-2：结果页发布素材包、下载全部图片、文案卡片
- v0.1-3：视觉收口、中文字体渲染修复
- v0.1-4：试用版收口、商品名称 / 类目、类目化内容生成、错误提示
- v0.1-5：上线前整理、部署准备、健康检查与环境说明
- v0.1-6：Render 线上静态资源加载修复，健康检查增加静态文件状态
- v0.1-7：Render 线上生成图片中文字体修复，健康检查增加字体诊断
- v0.1-8：补充项目内开源中文字体接入说明，准备 Render 字体文件放置路径
