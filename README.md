# 文脉 · Wenmai Skills

让中文表达自然，有文采，有依据。

文脉是一组中文写作技能，整理自一份OTFS文献检索报告的多轮改写、检测反馈与阅读样本分析。它支持自然表达、文学措辞迁用，以及用户提出的“降低AI率”目标；实际检测结果必须另行记录，技能不预测分数，也不保证通过检测。

## 三个技能

| 技能 | 用途 | 入口 |
| --- | --- | --- |
| `wenmai-writing` | 保留事实与作者声音，改善措辞、句间联系和长短句节奏，按语境使用成语与书面词 | [SKILL.md](skills/wenmai-writing/SKILL.md) |
| `wenmai-feedback` | 核对标色报告对应的版本，复盘得失，保留基准稿、小步修改，并整理真实检索截图与记录 | [SKILL.md](skills/wenmai-feedback/SKILL.md) |
| `wenmai-review` | 独立核对原意、证据强度、搭配、文体与来源，记录问题、修正及复核范围 | [SKILL.md](skills/wenmai-review/SKILL.md) |

三个技能可以独立使用。普通润色先用写作技能；已有检测报告时，先用反馈技能核对版本，再处理需要修改的段落。用户授权独立督查后，将原稿与候选交给审查者，修正并复核后交付。

## 表达素材与督查

表达库收录 **1,053 条**独立素材，按研究与证据、分析与关系、行动与评论、文学与叙述分为四类。每条包含含义、搭配、适用文体、原创用法例句和误用边界，区分书面词、成语、四字搭配与表达框架。可直接浏览[可读索引](skills/wenmai-writing/assets/lexicon/catalog.md)，数量、用途和审查记录见[素材库说明](skills/wenmai-writing/assets/lexicon/README.md)。

这些是通用表达及原创编辑说明，标为`editorial`；并非全部采自下述47个阅读页面，也不声称逐条经权威词典核证。容量用于扩大候选范围，不要求文章增加某类词的比例。文学意象按语境使用，技术段仍须准确。

先明确原句含义，再检索少量候选；独立督查核对本轮实际用法，发现问题后修正并复核。独立审查能帮助减少返工，不能保证检测分数或用户一次满意。

```sh
python skills/wenmai-writing/scripts/query_lexicon.py --query 依据 --genre 学术综述 --limit 6
python skills/wenmai-writing/scripts/query_lexicon.py --stats
python skills/wenmai-writing/scripts/query_lexicon.py --validate
```

[选用方法](skills/wenmai-writing/references/lexicon-guide.md)说明字面检索、文体筛选和迁用检查。

## 经验依据

| 版本 | 用户反馈比例 | 红色正文段 | 红、橙、紫合计 |
| --- | ---: | ---: | ---: |
| 科技评论文风基准稿 | 26.76% | 5 | 9 |
| 文学表达版，全文改写22段 | 50% | 10 | 17 |
| 回退后局部改写4段 | 27% | 2 | 9 |

这些比例来自用户反馈，Word标色文件本身没有总分字段。原稿未做同稿重复检测，平台设置也未完整记录。回退后，文学版新增着色的8段都不再着色；四段局部改写未显示相对26.76%基准的可靠总分改善。

文学版的成语只从12处增至13处，不能据此把升分归因于成语。更明显的变化是措辞、句式与段落组织一起被调整。详见[完整案例与证据边界](skills/wenmai-feedback/references/otfs-case-study.md)。

阅读材料包括23个科技文章样本和24个文学、文化页面样本，区分完整正文、主体片段、刊发节选与合集。整理出的[阅读样本目录](skills/wenmai-writing/references/reading-corpus.md)只保存出处和原创分析，不转载文章全文。

## 安装与调用

支持技能发现工具时，可使用：

```sh
npx skills add Knights-wtd/wenmai-skills --skill wenmai-writing
npx skills add Knights-wtd/wenmai-skills --skill wenmai-feedback
npx skills add Knights-wtd/wenmai-skills --skill wenmai-review
```

私有仓库需要先具备GitHub读取权限。也可以下载或克隆本仓库，将所需技能目录完整复制到客户端的技能目录；保留其中的`references`、`assets`和`scripts`。具体安装位置以客户端说明为准。

调用示例：

```text
使用 wenmai-writing 润色这份中文报告。希望有文学美感，
保留公式、引用、研究条件和待执行状态，先处理最不顺的两段。
```

```text
使用 wenmai-feedback 对照这两份Word和标色报告。
先确认检测对应哪个版本，分析变化；本轮不要改稿。
```

```text
使用 wenmai-writing 润色这篇文章，先检索合适的表达候选。
派出独立督查子代理，使用 wenmai-review 比较原稿与候选，
重点核对原意、搭配和文体；修正问题并复核后交付。
```

## 附带工具与模板

- [Word版本与直接标色核对脚本](skills/wenmai-feedback/scripts/compare_docx_reports.py)：Python 3标准库即可运行，不调用检测平台，不产生AI分数。
- [迭代记录模板](skills/wenmai-feedback/assets/iteration-log.template.json)：记录稿件、范围、反馈来源和检测口径。
- [检索证据模板](skills/wenmai-feedback/assets/search-evidence.template.json)：记录真实截图、检索词、日期、字段和限制条件。
- [内容保护模板](skills/wenmai-writing/assets/protection-ledger.template.json)：记录不能丢失的主张、数值、条件与研究阶段。
- [独立审查记录模板](skills/wenmai-review/assets/review-record.template.json)：记录审查形式、范围、问题、修正与复核。
- [表达检索工具](skills/wenmai-writing/scripts/query_lexicon.py)：标准库字面检索、文体筛选及跨分库格式与精确去重校验。

脚本示例：

```sh
python skills/wenmai-feedback/scripts/compare_docx_reports.py \
  before.docx after.docx --start 2 --end 35 --output comparison.json
```

`--start`和`--end`采用零基段落索引，结束位置不包含在范围内；示例范围仅适用于本案例，其他文件必须先核对段落范围。标题、参考文献和表格的处理限制见脚本帮助与反馈技能说明。

运行检查：

```sh
python -m unittest discover -s tests -v
```

本仓库保存技能、案例汇总、原创阅读分析和工具；原始作业与检测附件留在本地。外部文章的权利归其权利人，阅读目录中的链接不表示对其所有事实或观点进行了独立验证。
