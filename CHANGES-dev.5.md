# CHG-004 · IndexTTS 本机配音（1.0.0-dev.5）

产品目标仍为 v1.0。对应原 PRD F05–F09、F21–F31、F38–F42 的偏好/音频/任务/剪辑导出链路；docs/v1.0 保持冻结。本文件与本开发版本共同记录需求、页面和技术规格增量。

## 需求与页面

- 用户选择本机部署 IndexTTS，音频服务独立于 DeepSeek 文字、Seedream 图片；OpenAI 配音保留为可选项，不静默回退。
- 模型连接页新增配音服务商（IndexTTS 本机 / OpenAI）、本机服务地址、启动与检测按钮、2–30秒参考声音上传及当前声音版本。更换参考声音仅影响后续生成，不覆盖已有配音资产。
- 本机配音不记作云端 API 费用，仍消耗 GPU、电力和存储；保留原 OpenAI 每段预留策略用于切回云端。图片及文字预算继续执行原授权，不因改配音扩大上限。

## 应用接口

- PUT /api/v1/connection 增加 ttsProvider=openai|index_tts、indexTtsUrl，旧配置缺省仍使用 OpenAI。
- GET /api/v1/bootstrap 增加 ttsProvider、indexTtsUrl、indexTtsVoice 的公开信息，不返回密钥、音频内容或本机私有路径。
- GET /api/v1/index-tts/health：后端检测已保存的本机桥接服务，返回 available、model、referenceReady。
- POST /api/v1/index-tts/start：按既有会话、CSRF、幂等约束启动本机脚本，后台隐藏窗口；PID及命令行检查避免重复启动。模型加载完成前不宣称 ready。
- POST /api/v1/voice-reference：受会话/CSRF保护的 multipart 单文件上传，最大10MB，ffprobe验证2–30秒，FFmpeg归一化为24kHz单声道PCM WAV，保存在忽略的runtime/voices内，使用不可变ID。

## 本机桥接契约（拾史自定义，不冒充 IndexTTS 官方 HTTP API）

- 桥接代码 scripts/index_tts_bridge.py，默认仅绑定127.0.0.1:9880；应用仅允许HTTP loopback地址，不允许远程域名、URL凭证、重定向或任意路径。
- GET /health 返回 service=shishi-index-tts、ready、model、referenceReady。
- POST /v1/audio/speech 输入 input（最多3000字）、reference_audio（可选base64 WAV）、duration_factor（0.5–2.0）；返回 audio/wav。无自定义参考声音时使用官方演示参考文件。
- 桥接服务使用官方 Python IndexTTS2.5.infer 接口，普通话ZH；关闭首次部署不需要的CUDA自定义编译、DeepSpeed、Qwen文本情绪模块。串行推理，文本/参考声音摘要/参数/模型版本构成缓存键；拒绝浏览器跨站Origin调用，HTTP访问日志不记录请求正文或参考音频；上游推理器会在本机stdout日志输出归一化文本，日志不进入Git。
- 应用合成前做服务预检；离线时直接阻塞，不生成未知请求。实际请求中断时保留unknown，禁止盲目重试。成功WAV经ffprobe验证时长后存为audio资产并记录本机provider_calls；缓存返回同一资产。文件进入现有分镜试听、剪辑、字幕、MP4/SRT/ZIP链路。

## 部署与依赖

- 独立运行目录 D:/AI-Runtime/shishi-indextts，权重和缓存不进入WPS代码同步目录或Git。
- 上游官方源码固定提交 d9e41aac89fd00b3d71497fddb287b7f24613712。下载推理所需代码、许可证、锁文件，排除演示媒体和旧codec二进制；保留source-manifest.json。
- 主模型IndexTeam/IndexTTS-2.5及官方依赖的W2V-BERT、CAMPPlus、BigVGAN，使用发布方文件校验信息验证完整性。下载脚本支持分段续传，示例音色来自官方演示仓库，不使用未经提供的用户人声。
- 本机有RTX4090 Laptop 16GB。为避免重复下载CUDA包，使用venv-reuse隔离覆盖层只读复用digital-human环境的Python3.10.19/PyTorch2.6.0+cu124，保留NumPy1.26；补充实际推理需要的关键依赖，版本固定于 scripts/index-tts-overlay-requirements.txt，其余只读复用原环境。此为本机兼容路径，与官方推荐的PyTorch2.8/cu128环境不同，须以实际推理验证为准，且依赖原环境仍存在。未改动原AI环境。
- start-index-tts.ps1负责隐藏窗口启动、日志及PID。后续迁移机器需重新建立环境，不应复制已安装虚拟环境后假定可移植。

## 验证状态

已通过46项Node全量测试、3项Python桥接服务模拟测试，以及类型检查/前端构建。设置页1280/1440/1920宽度、参考声音上传归一化、服务检测和真实Seedream首图显示检查通过。核心及辅助模型权重已完成下载与发布方摘要校验，CUDA可用。实际IndexTTS2.5首段旁白合成成功：WAV时长10.49542秒，首次请求18.219秒，保存到首分镜，音频资产91fa73e0-6e6a-4a14-aba2-60a20b15bf9a。此为单段链路验证，听感与读音仍由用户验收。参考声音为官方演示voice_01，非用户个人音色。此次本机调用没有新增云端API费用或预算占用；任务保持暂停。

Seedream首张真实生图已成功，保存为首镜头图片并暂停任务，未生成其余图片或云端配音。画面中的马纹未准确呈现衔杯细节，只作为接口和显示链路验证；文物形制与纹样仍需实物参考图及人工审阅。

官方依据：
- https://github.com/index-tts/index-tts （安装、模型及Python调用）
- https://huggingface.co/IndexTeam/IndexTTS-2.5 （核心模型）
- https://modelscope.cn/models/IndexTeam/IndexTTS-2.5 （官方列出的国内模型源）
- https://github.com/index-tts/index-tts/blob/main/indextts/infer_v2_5.py （推理初始化及参数）

运行兼容修复：隔离层补齐descript-audiotools及依赖，Python3.10使用IPython8.37.0；桥接进程为GPT2InferenceModel显式混入GenerationMixin，适配Transformers4.52.1。固定版本见overlay requirements，不修改上游源文件或原有AI环境。

最终回归：46项Node测试及3项Python桥接测试通过，类型检查和构建通过；桌面10页回归无运行错误，冻结设计检查通过（42需求/57文件）。真实音频在分镜「旁白与声音」页签已验证元数据、播放推进及暂停。证据qa/index-tts-real-audio.json、qa/index-tts.json、qa/screens/index-tts-real-shot.png保留本机，不提交用户素材。
