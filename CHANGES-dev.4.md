# CHG-003 · Seedream 独立图片服务（1.0.0-dev.4）

产品目标 v1.0；冻结的 docs/v1.0 PRD、技术规格及架构保持原样。本文件同步记录本开发版本在 F21–F31 的需求、页面及技术增量。

## 用户问题与目标

现有图片请求返回模型 gpt-image-2.5 不存在，因此分镜图片为空。用户要求使用 Seedream 生图 API。保留已批准剧本、六个分镜和提示词，不重复生成文字；图片服务独立于 DeepSeek 文字和 OpenAI 配音。

## 页面与配置契约

- 模型连接新增图片服务商（OpenAI / Seedream）、火山方舟 API Key、Seedream 模型 ID、方舟密钥入口及服务分工。
- PUT /api/v1/connection 新增 imageProvider、seedreamModel、arkKey。既有 imageModel 仍保存 OpenAI 图片模型，旧客户端/旧配置兼容；新增字段缺省时保留现有图片服务配置。
- GET bootstrap 返回 imageProvider、当前有效 imageModel、openaiImageModel、seedreamModel、seedreamConfigured，不返回任何服务的密钥。
- 环境变量 ARK_API_KEY、SEEDREAM_MODEL；默认模型 doubao-seedream-5-0-lite-260128，最终以用户方舟账号已开通的模型/接入点为准。初版针对 5.0 lite / 4.5 / 4.0 的单图参数接入。
- 三家密钥分开保存在用户目录的本机秘密文件；留空保存保留旧值，Seedream 密钥不发送给 OpenAI 或 DeepSeek。

## 图片技术规格

- 官方固定地址 POST https://ark.cn-beijing.volces.com/api/v3/images/generations，Bearer Ark API Key。
- JSON 字段 model、prompt、size=1440x2560、response_format=b64_json、sequential_image_generation=disabled、stream=false、watermark=true。一次请求只生成一张9:16图片，不启用组图、联网搜索、图层拆分或视频生成。
- 若项目有器物 reference 资产，选最近一张，以 data:image/...;base64 形式传入 image；图生图与文生图使用同一接口。书页 source 资产不自动当作器物参考图。
- 返回 base64 图片经 sharp 校验转 PNG，存为本机 image 资产，origin=seedream，记录模型及水印状态；沿用现有缩略图、分镜页、剪辑和导出流程。
- 图片调用阶段使用 Seedream/模型专属请求标识，不复用旧 OpenAI 失败请求。相同 Seedream 调用结果未知时仍拦截重复提交；切换服务不清除旧预留、不自动扩大总预算。
- 当前失败作品保留 22 元预算占用与 2 元待核实预留，30 元上限剩余 6 元可用于后续预留；这些数额属于应用保守预留策略，不是服务商实际账单。本次仅保存 Seedream 选择，未恢复任务。

## 验证与边界

类型检查、39 项测试和前端构建通过。新增 8 项模拟测试覆盖文生图/参考图、官方地址与 Ark 密钥、PNG 保存、缺少密钥不回退、未知保护、旧失败预留保留、三服务密钥独立及预算拦截。所有模拟测试使用临时数据和虚构密钥。

独立浏览器验证设置页选择/切换/留空保存和秘密字段不返回；1280/1440/1920 无横向溢出、无运行时错误；10 页回归通过，原样片仍可读取。证据：本机 qa/seedream.json、qa/screens/seedream-settings.png、qa/browser.json。

真实 Seedream 生图尚未验收，需要用户在应用填写方舟密钥并开通可用模型。未新增任何付费请求，也未修改现有失败账目。配音仍为 OpenAI，其账户额度需独立配置。

官方出处（2026-10-24）：
- https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-api （地址、参考图 base64、单图模式、返回格式、尺寸和水印）
- https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-4-0-5-0 （模型示例与密钥入口）
- https://ark.volcengine.com/region:cn-beijing/apikey （密钥配置入口）
