# Style Profile 数据结构说明

本文档定义了存储在 powermem 中的 Style Profile 的完整数据结构。

## 存储位置

- **命名空间**：`user_id="style_profiles"` + `agent_id="extraction"`
- **存储方式**：通过 powermem SDK 的 `memory.add()` 方法存储为 JSON 文档

## 数据结构

```json
{
  "profile_type": "style_profile",
  "profile_id": "default",
  "profile_name": "默认风格",
  "features": {
    "narrative_rhythm": "短句为主，每段2-4行，信息密度适中",
    "key_phrase_placement": "段首强调核心观点，段尾升华",
    "formatting_symbols": "使用「」引号强调，• 符号作列表",
    "punctuation_habits": "省略号表达余韵，破折号补充说明",
    "paragraph_structure": "总-分-总结构，逻辑递进",
    "emotional_tone": "理性克制为主，偶有情感共鸣点",
    "rhetorical_devices": "比喻形象化抽象概念，反问引发思考",
    "opening_style": "开门见山直入主题，偶用案例引入",
    "closing_style": "总结升华，留白引发思考"
  },
  "source": "《如何写好技术文章》- https://example.com/article",
  "version": "1.0",
  "created_at": "2026-03-06T10:30:00Z",
  "updated_at": "2026-03-06T10:30:00Z"
}
```

## 字段说明

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `profile_type` | string | 是 | 固定值 `"style_profile"`，用于区分不同类型的记忆 |
| `profile_id` | string | 是 | Profile 唯一标识符，如 `"default"`, `"emotion-style"` |
| `profile_name` | string | 是 | Profile 显示名称，如 `"默认风格"`, `"情绪煽动版"` |
| `features` | object | 是 | 风格特征对象，详见下方 |
| `source` | string | 是 | 来源标题或 URL，用于溯源 |
| `version` | string | 是 | 版本号（语义化版本，如 `"1.0"`, `"2.1"`） |
| `created_at` | string | 否 | 创建时间（ISO 8601 格式） |
| `updated_at` | string | 否 | 更新时间（ISO 8601 格式） |

### features 对象

`features` 对象包含 9 个核心维度，每个维度用简洁的描述性语言概括风格特征：

| 维度字段 | 说明 | 示例值 |
|---------|------|--------|
| `narrative_rhythm` | 叙事节奏：句子长度偏好、段落节奏、信息密度 | `"短句为主，每段2-4行，信息密度适中"` |
| `key_phrase_placement` | 金句位置：强调内容的位置习惯 | `"段首强调核心观点，段尾升华"` |
| `formatting_symbols` | 排版符号：特殊引号、列表符号、分隔符使用习惯 | `"使用「」引号强调，• 符号作列表"` |
| `punctuation_habits` | 标点习惯：省略号、破折号、感叹号等使用频率和场景 | `"省略号表达余韵，破折号补充说明"` |
| `paragraph_structure` | 段落结构：段落组织方式 | `"总-分-总结构，逻辑递进"` |
| `emotional_tone` | 情感基调：理性/感性、克制/热烈、严肃/幽默等 | `"理性克制为主，偶有情感共鸣点"` |
| `rhetorical_devices` | 修辞手法：比喻、排比、反问等惯用修辞 | `"比喻形象化抽象概念，反问引发思考"` |
| `opening_style` | 开篇风格：如何引入话题 | `"开门见山直入主题，偶用案例引入"` |
| `closing_style` | 结尾风格：如何收束内容 | `"总结升华，留白引发思考"` |

### 特征值编写原则

1. **描述性而非枚举性**：使用自然语言描述风格特点，而不是简单分类
   - ✅ 好：`"短句为主，每段2-4行，信息密度适中"`
   - ❌ 差：`"短句"`

2. **具体而非抽象**：提供可操作的具体描述
   - ✅ 好：`"段首强调核心观点，段尾升华"`
   - ❌ 差：`"重点突出"`

3. **剥离事实信息**：只保留风格骨架，不包含具体内容
   - ✅ 好：`"开门见山直入主题，偶用案例引入"`
   - ❌ 差：`"以乔布斯的故事开头"`

4. **长度适中**：每个特征值控制在 10-30 字，既不过于简略也不冗长

## 存储操作示例

### 使用 powermem SDK 存储

```python
from powermem import create_memory
import json

# 创建 memory 实例（自动从 .env 加载配置）
memory = create_memory()

# 构建 profile 数据
profile = {
    "profile_type": "style_profile",
    "profile_id": "default",
    "profile_name": "默认风格",
    "features": {
        "narrative_rhythm": "短句为主，每段2-4行",
        # ... 其他特征
    },
    "source": "文章标题或URL",
    "version": "1.0"
}

# 存储到 powermem（以 JSON 字符串形式）
memory.add(
    json.dumps(profile, ensure_ascii=False),
    user_id="style_profiles",
    agent_id="extraction"
)
```

### 向量搜索相似 Profile

```python
import json

# 搜索相似 Profile（以特征摘要作为 query）
features_summary = "短句节奏，理性克制，总分总结构"
results = memory.search(
    features_summary,
    user_id="style_profiles",
    agent_id="extraction",
    limit=5
)

# 解析结果
for item in results["results"]:
    profile = json.loads(item["memory"])
    similarity = item["score"]
    print(f"Profile: {profile['profile_name']}, 相似度: {similarity}")
```

## 版本演进

### 版本号规则

使用语义化版本号 `MAJOR.MINOR`：

- **MAJOR**：风格发生根本性变化（如从"理性克制"转为"情绪煽动"）
- **MINOR**：局部特征优化（如调整标点习惯细节）

### 覆盖更新

覆盖模式下，先删除旧 Profile，再写入新版本：

```python
# 1. 搜索并删除旧 Profile
old_results = memory.search(
    f"profile_id:{profile_id}",
    user_id="style_profiles",
    agent_id="extraction"
)
for item in old_results["results"]:
    memory.delete(item["id"], user_id="style_profiles")

# 2. 写入新版本（version 递增）
profile["version"] = "2.0"
memory.add(json.dumps(profile, ensure_ascii=False), ...)
```

### 分支创建

分支模式下，保留原 Profile，创建新的 profile_id：

```python
# 原 Profile 保持不变
# 新建独立 Profile
new_profile = {
    "profile_type": "style_profile",
    "profile_id": "emotion-style",  # 新 ID
    "profile_name": "情绪煽动版",     # 新名称
    # ... 新特征
}
memory.add(json.dumps(new_profile, ensure_ascii=False), ...)
```

## 冲突判定逻辑

### 相似度阈值

- 向量搜索相似度 > 0.85 时，视为"相关 Profile"
- 需进一步进行语义冲突检测

### 语义冲突检测

比对关键特征维度的语义是否相反：

| 维度 | 冲突示例 |
|------|---------|
| `narrative_rhythm` | "极简短句" vs "长句排比" |
| `emotional_tone` | "理性克制" vs "热烈煽情" |
| `paragraph_structure` | "碎片化并列" vs "严密逻辑链" |

使用 LLM 判断两个特征值是否语义冲突：

```python
def detect_conflict(old_value: str, new_value: str) -> bool:
    prompt = f"""
    判断以下两个风格特征描述是否存在语义冲突（相反或矛盾）：
    
    特征A：{old_value}
    特征B：{new_value}
    
    仅回答 YES 或 NO。
    """
    # 调用 LLM 判断
    response = llm.generate(prompt)
    return "YES" in response.upper()
```

## 扩展字段

未来可扩展的字段：

- `tags`: 标签数组，如 `["技术写作", "长文"]`
- `performance_metrics`: 关联的效果数据（待 Reflection Skill 接入）
- `parent_profile_id`: 分支时记录父 Profile ID
- `merge_history`: 合并历史记录

扩展字段不影响现有功能，向后兼容。
