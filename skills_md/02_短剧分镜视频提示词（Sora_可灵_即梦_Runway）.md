# 02 短剧分镜视频提示词（Sora / 可灵 / 即梦 / Runway）

> **风格归零：郭帆视觉体系 x AI视频生成**
> 本提示词可直接用于 Sora / 可灵 / 即梦 / Runway Gen-3 / Pika 等视频生成AI。
> 核心锚点：电影级质感、人物视觉统一、9:16竖屏构图、克制运镜、写实纹理。

---

## 一、系统级设定模板

```
风格锚定：郭帆电影美学 x 短剧竖屏
视觉基准：
- 画面质感对标《流浪地球》系列——真实纹理、自然光影、物理正确
- 拒绝"影视飓风"式过度打光和过度调色——光线要有来源，阴影要有层次
- 人物不是滤镜产物——皮肤有毛孔，衣服有褶皱，环境有灰尘

画幅：9:16 竖屏（1080x1920）
帧率：24fps（电影感）
输出要求：8K超清，胶片颗粒保留，禁止AI平滑磨皮
```

---

## 二、人物视觉统一性规则（四要素）

AI视频生成的最大问题是人物形象漂移。必须用以下四要素锁定人物外观。

### 2.1 四要素定义

| 要素 | 说明 | 提示词写法示例 |
|------|------|---------------|
| 发型 | 精确到长度/颜色/刘海/发型纹理 | "long black straight hair, center part, reaching mid-back" |
| 肤色 | 精确到明度/冷暖/质感 | "fair skin with warm undertone, visible pores, natural texture" |
| 配饰 | 标志性配饰必须每镜出现 | "wearing a thin silver necklace with a small crescent pendant" |
| 穿搭 | 每场戏锁定1套服装，不换装 | "wearing a cream-colored cashmere coat, dark blue jeans, white sneakers" |

### 2.2 人物统一性提示词模板

当AI生成的视频中人物需要在多个镜头间保持一致时，在每段提示词前统一加上：

```
[CHARACTER: 林晚]
hairstyle: long black straight hair, center part, reaching waist
skin: fair, warm undertone, natural pore texture
accessory: silver ring on right index finger
outfit: oversized grey wool coat, black turtleneck, dark denim
```

---

## 三、三套色调模板

按题材绑定色彩方案，任何镜头都要在对应的色彩框架内生成。

### 模板 A：甜宠暖金柔光

| 维度 | 规格 |
|------|------|
| 色温 | 暖色（5500K-6200K） |
| 主色调 | 金色/暖橙/奶白 |
| 阴影 | 柔和暖灰，不出现冷色阴影 |
| 光质 | 柔光箱质感——散射光，无硬阴影 |
| 对比度 | 低对比度（soft contrast） |
| 饱和度 | 中等偏高 |
| 提示词后缀 | `-- warm golden hour lighting, soft glow, gentle skin diffusion, cream and peach color palette, romantic atmosphere` |

**示例镜头提示词：**

```
[CHARACTER: 林晚]
9:16 vertical shot. medium close-up. warm golden hour sunlight streaming through sheer curtains. girl sitting on a wooden windowsill, looking down at a book, a faint smile at the corner of her mouth. soft air particles floating in light. cream and peach color palette. film grain. 8K.
```

### 模板 B：豪门冷白青橙

| 维度 | 规格 |
|------|------|
| 色温 | 冷色偏青（4200K-4800K） |
| 主色调 | 冷白/青灰/局部橙色点缀 |
| 阴影 | 冷蓝灰，深邃 |
| 光质 | 硬光+柔光结合——窗口光为主，局部打亮 |
| 对比度 | 中高对比度 |
| 饱和度 | 低饱和度，保留橙色（如肤色/灯光） |
| 提示词后缀 | `-- cool white and teal color palette, orange-teal contrast, hard window light, deep cool shadows, cinematic teal tones, restrained saturation` |

**示例镜头提示词：**

```
[CHARACTER: 沈墨言]
9:16 vertical shot. close-up from slightly low angle. man in a charcoal suit sitting in a modernist office. cold window light from the right side, hard shadows across half his face. minimal color palette: teal-grey walls, warm orange desk lamp. he's not looking at the camera. film grain. realistic skin texture. 8K.
```

### 模板 C：悬疑蓝紫冷霓虹

| 维度 | 规格 |
|------|------|
| 色温 | 冷色（3800K-4500K） |
| 主色调 | 深蓝/紫调/冷白/霓虹绿点缀 |
| 阴影 | 全黑或深紫，几乎无细节 |
| 光质 | 点光源/霓虹灯管/街灯光——强指向性 |
| 对比度 | 高对比度（low-key lighting） |
| 饱和度 | 中等，局部高饱和（霓虹灯光） |
| 提示词后缀 | `-- blue-purple neon palette, cold cyan and deep violet, hard point light sources, low-key lighting, high contrast, dark shadows crushing to black, noir atmosphere` |

**示例镜头提示词：**

```
[CHARACTER: 陈屿]
9:16 vertical shot. extreme close-up on eyes. only lighting is from a flickering blue neon sign outside the window. half the face in cyan light, half in complete darkness. no expression. slow blink. cold atmosphere. blue-purple color palette. 8K film grain.
```

---

## 四、9:16竖屏构图规则

### 4.1 人脸定位

| 景别 | 人脸在画面中的位置 | 说明 |
|------|-------------------|------|
| 特写 | 画面上1/3区域（眉毛到下巴居画面中央偏上） | 眼睛在画面水平中线偏上1/4处 |
| 近景 | 画面上1/3区域（胸部以上） | 头顶留白不超过画面5% |
| 中景 | 画面上1/2到2/3区域（膝盖或腰部以上） | 人物居中，头部在画面上1/3 |

### 4.2 主体居中规则

- 单人镜头：人物面部垂直中轴对齐画面垂直中轴，或略偏一侧（留出视线方向的空白）。
- 双人对话：使用过肩镜头（OTS），前景肩膀占画面左侧1/4，对焦在说话人物面部。
- 环境镜头：主体在画面中央区域，但要在画面中加入纵深元素（前景/背景层次）。

### 4.3 背景虚化规则

| 景别 | 背景虚化程度 | 说明 |
|------|-------------|------|
| 特写 | 强虚化（浅景深） | 背景几乎不可辨，仅保留色块和光斑 |
| 近景 | 中虚化 | 背景可辨但不清晰，环境氛围可见 |
| 中景 | 弱虚化到清晰 | 环境需要清晰交代时保留景深 |

### 4.4 构图禁止项

```
❌ 人物面部在画面正中心（证件照构图）
❌ 头顶留白超过画面高度的15%
❌ 背景过曝/死白（AI常见错误）
❌ 人物在画面中占比低于20%（竖屏浪费）
❌ 多人入镜时人脸重叠
❌ 人物看镜头（打破第四面墙，除非剧情需要）
```

---

## 五、景别边界定义

### 5.1 景别分类及画面占比

| 景别 | 取景范围 | 画面中人物占比 | 用途 |
|------|---------|---------------|------|
| 极特写 | 仅眼睛/嘴唇/手部局部 | --- | 情绪关键帧，展现微表情/细节 |
| 特写 | 下巴到额头 | 约占画面60-70% | 台词/情绪爆发时刻 |
| 近景 | 胸部以上 | 约占画面40-50% | 对话主力景别，情感交流 |
| 中近景 | 腰部以上 | 约占画面30-40% | 兼顾表情和上半身动作 |
| 中景 | 膝盖以上 | 约占画面20-30% | 环境+人物关系建立 |
| 全景 | 全身 | ≤画面20% | 场景建立/走位 |

### 5.2 短剧景别使用频率指南

| 景别 | 推荐占比 | 说明 |
|------|---------|------|
| 特写 + 极特写 | 35% | 情绪驱动型短剧的核心景别 |
| 近景 + 中近景 | 45% | 对话和叙事主力 |
| 中景 | 15% | 场景过渡和关系建立 |
| 全景 | 5% | 仅在每场第一镜或关键环境交代时使用 |

---

## 六、运镜逻辑

### 6.1 四种基础运镜

| 运镜方式 | 适用场景 | 提示词写法 |
|---------|---------|-----------|
| 推镜聚焦 | 特写开场/情绪升级/关键台词 | `slow push-in, focusing on the eyes` |
| 固定机位 | 对话/对峙/情绪留白（郭帆标志性用法） | `static camera, locked-off shot` |
| 横移跟随 | 行走/追逐/场景过渡 | `slight pan following the character's movement` |
| 慢推压迫 | 悬疑/危机逼近/情绪施压 | `very slow dolly forward, building tension` |

### 6.2 运镜规则

- 短剧中80%以上镜头应为**固定机位**或**极小幅度运镜**——郭帆式克制。
- 每集运镜变化不超过3次（转换场景/情绪节点使用）。
- 禁止手持摇晃镜头（除非是暴力冲突或追逐场景）。
- 推/拉速度必须均匀且缓慢——AI快速推镜容易产生视觉眩晕。

### 6.3 运镜提示词模板

```
[运镜类型] + [速度/幅度] + [焦点变化] + [结束构图]

示例：
"static camera, locked-off, shallow depth of field focused on the teacup. the only movement is the steam rising."
"slow push-in from medium shot to close-up, focus rack from background to character's eyes, ending on extreme close-up."
```

---

## 七、画质标准

### 7.1 画质参数表

| 维度 | 要求 | 提示词写法 |
|------|------|-----------|
| 解析度 | 8K超清 | `8K, ultra high definition` |
| 胶片质感 | 保留胶片颗粒 | `film grain, 24fps, cinematic texture` |
| 纹理 | 真实材质，拒绝平滑 | `realistic skin texture, fabric weave visible, environmental dust particles` |
| 光线 | 物理正确，来源可辨 | `natural light, single light source from left window` |
| 颜色 | 按题材绑定对应色板 | 见第三节三套色调模板 |

### 7.2 核心禁止项

```
❌ smooth skin / perfect skin / airbrushed / beauty mode（禁止磨皮）
❌ plastic look / CG render / 3D render / unreal engine（禁止CG感）
❌ oversaturated / vibrant / neon glow（除非是悬疑霓虹模板）
❌ lens flare without source（禁止无光源的镜头光晕）
❌ shallow depth of field on whole frame（禁止全画幅无差别虚化）
❌ bloom effect / glowing edges（禁止辉光效果）
```

---

## 八、特效规则

### 8.1 按题材绑定特效

| 题材 | 允许的特效 | 禁止的特效 |
|------|-----------|-----------|
| 甜宠 | 暖色柔光、空气粒子浮尘、窗外光斑 | 梦幻光晕、慢动作过度使用、星尘效果 |
| 豪门 | 玻璃反光、雨水在窗面的倒影、慢推 | 金色粒子、炫光、飞溅火花 |
| 悬疑 | 霓虹灯光闪烁、阴影缓动、镜子反射 | 烟雾过度使用、闪白过渡、快速闪回 |
| 都市情感 | 地铁窗外的光影流动、雨滴、街头霓虹 | 慢镜头泛滥、人为添加的柔光 |

### 8.2 特效使用原则

- 所有特效必须有物理来源：光来自灯具或太阳，雾来自环境，雨来自天气。
- 禁止添加剧本中不存在的光源。
- 特效强度：让观众不会注意到"这里用了特效"——物理级真实。

---

## 九、输出示例

### 完整分镜提示词示例（甜宠题材）

```
[CHARACTER: 林晚]
hairstyle: long black straight hair, center part, reaching waist
skin: fair, warm undertone, natural pore texture
accessory: silver ring on right index finger
outfit: oversized grey wool coat, black turtleneck, dark denim

[SHOT 1 - 特写]
9:16 vertical shot. extreme close-up on hands. her hands are wrapping a red scarf around someone's neck. fingertips trembling slightly. warm golden hour light from behind. shallow depth of field — the scarf's wool texture is visible. film grain. 8K.
-- warm golden hour lighting, cream and peach palette, soft glow

[SHOT 2 - 近景]
9:16 vertical shot. medium close-up of her face, slightly low angle. she's looking upward. there's a reflection of warm light in her eyes. a single tear welling up but not falling. static camera, locked-off. 8K film grain.
-- warm golden hour lighting, cream and peach palette

[SHOT 3 - 中景]
9:16 vertical shot. medium shot from behind. she's standing in a doorway, back to camera. the doorframe is dark, the outside is flooded with warm light. she takes one step forward. slight pan following. 8K.
-- warm golden hour backlight, silhouette with warm edge light
```

---

## 十、负面禁止清单（完整版）

```
❌ 人物长相在连续镜头中不一致（AI形象漂移——必须用四要素锁定）
❌ 磨皮/平滑/美颜效果
❌ 证件照式居中构图
❌ 无来源的光晕/辉光/炫光
❌ 全画幅浅景深（所有物体包括前景都模糊）
❌ 人物看镜头（郭帆体系中表演不承认第四面墙的存在）
❌ 超过每秒24帧的运动模糊
❌ 画面中同时出现3个以上人物（竖屏容纳不了，除非全景）
❌ 色彩方案在单集中跳变（甜宠突然变成冷色调）
❌ 运镜幅度过大/速度过快（眩晕感）
❌ 背景中物体运动逻辑错误（AI常见问题——需检查）
❌ 人物手部/脚部生成异常（AI常见问题——需重试或局部优化）
```

---

## 十一、平台适配说明

| 平台 | 推荐模型 | 特别说明 |
|------|---------|---------|
| Sora | OpenAI Sora | 擅长运镜和光影物理一致性；可生成较长镜头；需多次抽卡选最佳 |
| 可灵 | 可灵 1.5 | 竖屏支持好，人像一致性较好；建议配合四要素锁定 |
| 即梦 | 即梦视频生成 | 擅长特写和近景；注意补充"film grain"避免塑料感 |
| Runway | Gen-3 Alpha | 运镜控制最灵活；适合需要精确运镜的分镜；背景稳定性需要检查 |
| Pika | Pika 2.0 | 适合快速出样片；画质不如上述平台，建议用于pre-viz |

---

> *"每一帧都是选择，不是填充。"*
> —— 郭帆风格视频生成指南
