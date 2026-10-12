# 文脉表达素材库

本库用于扩大中文润色的措辞选择，按四种写作任务组织。每条只计一个独立表达，不将同一词搭配不同宾语算作多条；近义表达可以分别收录，但应体现含义、对象或文体的区别。

0.2.0 版保留 **1,053 条**独立素材：书面词757条、成语214条、四字搭配72条、表达框架10条。总量由JSONL原始条目计算，下面的索引和审查记录不另计素材。

| 分库 | 条数 | 内容 | 文件 |
| --- | ---: | --- | --- |
| 研究与证据 | 258 | 检索、阅读、考据、材料组织和论证 | [research.jsonl](research.jsonl) |
| 分析与关系 | 261 | 比较、条件、范围、程度、结构与变化 | [analysis.jsonl](analysis.jsonl) |
| 行动与评论 | 260 | 实践、组织、协作、责任和公共评论 | [commentary.jsonl](commentary.jsonl) |
| 文学与叙述 | 274 | 景物、感官、时序、情绪、人情与文化记忆 | [literary.jsonl](literary.jsonl) |

具体字段见 [SCHEMA.md](SCHEMA.md)。JSONL 为 UTF-8 文本，一行一条完整 JSON；不需要外部数据库。

按[可读索引](catalog.md)浏览，再点击条目ID查看完整用法。计数与文件哈希见[清单](manifest.json)，审查覆盖、问题和处理见[审查记录](review-record.json)。

初稿1,096条经过独立代理逐条核读，修正13条、删除1条近义弱项；跨库41组相同表达择一保留，删除42条重复记录。修改、去重及索引已由督查最终复核，详见[审查说明](review-report.md)。

## 用法与来源

每条提供表达类别、写作任务、释义、自然搭配、适用文体、原创例句和误用边界。书面词、成语、一般四字搭配与表达框架分开标注；长度为四个字并不表示它是成语。

`provenance: editorial` 表示通用词语及原创编写的编辑说明。例句是用法示范，不是某次研究或作者经历的事实记录。这些条目不声称都摘自媒体、不署给作家，也不声称逐条完成权威词典核证。已有47个文章与页面样本的阅读范围和分析另见[阅读目录](../../references/reading-corpus.md)。

独立核读检查词义、搭配、文体、例句和误用边界；自动校验检查格式与规范化后的精确重复。这两项都不等于词典核证或在任意新文章中使用正确。具体覆盖和修正由审查记录说明。

分类存疑时进行局部词条比照，具体页面和范围写入审查记录。固定四字表达未核定严格成语分类时可保守标四字搭配，并在条目说明；这个标签不意味着它不属于成语。

## 检索

从仓库根目录运行：

```sh
python skills/wenmai-writing/scripts/query_lexicon.py --query 依据 --genre 学术综述 --limit 6
python skills/wenmai-writing/scripts/query_lexicon.py --query 光 --genre 散文 --limit 6
python skills/wenmai-writing/scripts/query_lexicon.py --kind 成语 --genre 评论 --limit 8
python skills/wenmai-writing/scripts/query_lexicon.py --stats
python skills/wenmai-writing/scripts/query_lexicon.py --validate
```

关键词使用字面匹配，多词用空格分隔且全部须匹配。`--genre`、`--kind` 与 `--function` 可进一步筛选，`--json` 输出完整条目。词语在误用说明中出现不会因此获得检索推荐。文体标签可能重叠，其计数不相加作为库总量。

先明确原句含义，再检索少量候选，完整阅读边界。没有合适候选就采用普通准确的表达；不以库容量、词语少见程度或成语比例评价文章。实际选用后按[选用方法](../../references/lexicon-guide.md)对照原意，并在获授权时交给独立督查。
