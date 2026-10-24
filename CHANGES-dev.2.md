# CHG-001 · DeepSeek 接入（1.0.0-dev.2）

用户授权：2026-10-24，文字与识读改接 DeepSeek API。产品目标仍为 v1.0；冻结的 docs/v1.0 PRD 与技术规格保持不变，此文件记录实现增量，供下一版设计同步。

- 对应 F10–F20：独立文字服务商选择，DeepSeek Responses 适配，默认 deepseek-flash；系统指令从 developer 映射为 system，结构化输出、引用检查和来源校对保持。
- 对应 F21–F31：图片与配音继续使用 OpenAI，不将 DeepSeek 密钥发往 OpenAI；供应商固定官方地址，不提供任意地址。调用表增量增加 provider/model 字段，可追踪费用归属；保留幂等、未知保护和预算授权。
- 页面：模型连接增加 DeepSeek 密钥、模型、服务分工与能力提示；顶部显示当前文字服务商。旧密钥和作品数据兼容，空密钥保持已有值，密钥不返回前端。
- PDF：含正文 PDF 本地提取不受影响；扫描 PDF 的文件输入在 DeepSeek 下于预留和请求前明确拦截，提示转 JPG/PNG 或粘贴正文。照片识读只允许当前已核实支持视觉的 deepseek-flash。
- 迁移：默认仍保留旧用户 OpenAI 选择，由应用设置明确切换；本次用户已授权切换，运行时设置切为 DeepSeek，等待用户自行填写密钥。不自动恢复或重发已有任务。

官方依据（2026-10-24）：
- https://api-docs.deepseek.com/guides/responses_api/ （地址、结构化格式、角色及 PDF 文件输入限制）
- https://api-docs.deepseek.com/guides/vision/ （deepseek-flash 图片识读）
- https://api-docs.deepseek.com/quick_start/pricing/ （当前模型名与计费）

验证证据完成后记录于 IMPLEMENTATION.md。真实付费调用与账户权限需用户试用验收。
