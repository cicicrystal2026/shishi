# CHG-005 · 本机旁白情绪控制 · 1.0.0-dev.6

产品目标仍为v1.0；此为F05–F09偏好及F27–F31配音素材的实现增量，冻结docs/v1.0保持不变。

用户反馈首段声音过于激动。原桥接不设置情绪向量，会沿用参考声音情绪；此次把讲解风格从参考音色中独立控制。

- 模型连接页新增「讲解风格」：平稳讲解（默认）/跟随参考声音。保存不触发生成，只影响后续配音。旧配置无字段时默认平稳讲解；不修改已有音频。
- connection增加indexTtsStyle=calm|reference；严格校验并公开返回，无密钥变化。OpenAI配音路径保持原逻辑。
- 本机请求增加speech_style；平稳讲解使用官方emo_vector顺序[happy,angry,sad,afraid,disgusted,melancholic,surprised,calm]，设置[0,0,0,0,0,0,0,0.8]，emo_alpha=1、use_random=False。duration_factor=1.1，目标时长略增，不是保证实际时长精确增加10%。跟随参考声音不设置情绪向量，duration_factor=1。
- 这是模型情绪引导，不能保证完全消除参考声音的韵律影响；听感仍需用户验收。未加载QwenEmotion，不使用文本情绪解析。
- 应用请求键、桥接缓存同时纳入风格及参数版本，避免新风格误用旧音频；输出资产记录speechStyle和durationFactor。服务health声明支持的speechStyles；旧桥接需重启，缺少能力时阻塞，不静默忽略风格。
- 保留原始首段音频，重新合成只限首段本机测试，不恢复其余云端图片或配音。不修改预算，不清除旧预留。

验证：47项Node测试、4项Python桥接测试通过，包含风格透传/保存、无效值拦截、缓存隔离、平静情绪向量与既有调用保护。真实新旁白及浏览器验收结果另记于IMPLEMENTATION.md。

依据：官方固定源码indextts/infer_v2_5.py（本机已读取），以及 https://github.com/index-tts/index-tts 。

真实首段本机测试完成：新音频c63a4ac8-a084-47a7-9984-25031a15f868，9.264762秒，请求12.118秒，speechStyle=calm、durationFactor=1.1；首分镜已引用新音频。原音频91fa73e0-6e6a-4a14-aba2-60a20b15bf9a完整保留。两次独立推理内容时长存在采样差异，不能把duration_factor当作跨次合成的时长保证。预算占用24元、待核实预留2元保持不变，任务仍paused。新音频浏览器加载/播放/暂停通过，设置页默认calm及三个桌面宽度通过，十页回归无运行错误，类型检查/构建/冻结基线检查通过。听感是否足够平稳仍待用户试听。
