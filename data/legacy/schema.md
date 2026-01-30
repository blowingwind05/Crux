# 论文数据结构字段说明

本文档描述了 `one_paper_schema.json` 文件中各个字段的含义和结构。

## 字段定义表

| 字段路径 | 类型 | 必需 | 描述 |
|---------|------|------|------|
| `alphaxiv_overview` | Object | 是 | 论文的 AlphaXiv 概览信息，包含状态、更新时间和多语言概览内容 |
| `alphaxiv_overview.state` | String | 是 | 处理状态（如 "done" 表示已完成） |
| `alphaxiv_overview.updatedAt` | Number | 是 | 最后更新时间戳（毫秒） |
| `alphaxiv_overview.overviews` | Object | 是 | 多语言概览对象 |
| `alphaxiv_overview.overviews.zh` | Object | 是 | 中文版本概览 |
| `alphaxiv_overview.overviews.zh.title` | String | 是 | 论文中文标题 |
| `alphaxiv_overview.overviews.zh.abstract` | String | 是 | 中文摘要 |
| `alphaxiv_overview.overviews.zh.summary` | Object | 是 | 摘要信息对象 |
| `alphaxiv_overview.overviews.zh.summary.summary` | String | 是 | 简短总结 |
| `alphaxiv_overview.overviews.zh.summary.originalProblem` | Array | 是 | 原始问题列表 |
| `alphaxiv_overview.overviews.zh.summary.solution` | Array | 是 | 解决方案列表 |
| `alphaxiv_overview.overviews.zh.summary.keyInsights` | Array | 是 | 关键洞察列表 |
| `alphaxiv_overview.overviews.zh.summary.results` | Array | 是 | 结果列表 |
| `alphaxiv_overview.overviews.zh.overview` | String | 是 | 详细概述（Markdown 格式） |
| `alphaxiv_overview.overviews.zh.citations` | Array | 是 | 引用文献列表 |
| `alphaxiv_overview.overviews.en` | Object | 是 | 英文版本概览（结构同中文） |
| `alphaxiv_overview.overviews.en.title` | String | 是 | 论文英文标题 |
| `alphaxiv_overview.overviews.en.abstract` | String | 是 | 英文摘要 |
| `alphaxiv_overview.overviews.en.summary` | Object | 是 | 英文摘要信息对象 |
| `alphaxiv_overview.overviews.en.summary.summary` | String | 是 | 英文简短总结 |
| `alphaxiv_overview.overviews.en.summary.originalProblem` | Array | 是 | 英文原始问题列表 |
| `alphaxiv_overview.overviews.en.summary.solution` | Array | 是 | 英文解决方案列表 |
| `alphaxiv_overview.overviews.en.summary.keyInsights` | Array | 是 | 英文关键洞察列表 |
| `alphaxiv_overview.overviews.en.summary.results` | Array | 是 | 英文结果列表 |
| `alphaxiv_overview.overviews.en.overview` | String | 是 | 英文详细概述（Markdown 格式） |
| `alphaxiv_overview.overviews.en.citations` | Array | 是 | 英文引用文献列表 |
| `arxiv_id` | String | 是 | 论文的 arXiv ID（如 "2512.23647"） |
| `abstract` | String | 是 | 论文的英文摘要 |
| `affiliation_detail` | Object | 是 | 论文作者的机构详细信息 |
| `affiliation_detail.affiliations` | Array | 是 | 作者列表 |
| `affiliation_detail.affiliations[].author` | String | 是 | 作者姓名 |
| `affiliation_detail.affiliations[].author_email` | String | 否 | 作者邮箱（可能为空） |
| `affiliation_detail.affiliations[].org` | String | 是 | 所属机构 |
| `affiliation_detail.affiliations[].org_email` | String | 否 | 机构邮箱（可能为空） |
| `affiliation_detail.affiliations[].is_industry` | Boolean | 是 | 是否为产业界 |
| `affiliation_detail.timestamp` | String | 是 | 时间戳 |
| `affiliation_detail.text_length` | Number | 是 | 文本长度 |
| `affiliation_detail.pdf_minio_info` | Object | 是 | PDF 文件存储信息 |
| `affiliation_detail.pdf_minio_info.bucket` | String | 是 | 存储桶名称 |
| `affiliation_detail.pdf_minio_info.object_name` | String | 是 | 对象名称 |
| `affiliation_detail.pdf_minio_info.uploaded_at` | String | 是 | 上传时间 |
| `affiliation_detail.pdf_minio_info.size` | Number | 是 | 文件大小（字节） |
| `affiliation_detail.markdown_minio_info` | Object | 是 | Markdown 文件存储信息 |
| `affiliation_detail.markdown_minio_info.bucket` | String | 是 | 存储桶名称 |
| `affiliation_detail.markdown_minio_info.object_name` | String | 是 | 对象名称 |
| `affiliation_detail.markdown_minio_info.uploaded_at` | String | 是 | 上传时间 |
| `affiliation_detail.markdown_minio_info.size` | Number | 是 | 文件大小（字节） |
| `title` | String | 是 | 论文标题 |
| `metadata` | Object | 是 | 论文元数据信息 |
| `metadata.category` | String | 是 | 类别缩写 |
| `metadata.authors` | Array | 是 | 作者列表 |
| `metadata.timestamp` | Number | 是 | 时间戳 |
| `metadata.date` | String | 是 | 发布日期 |
| `metadata.pdf_url` | String | 是 | PDF 下载链接 |
| `metadata.arxiv_url` | String | 是 | arXiv 页面链接 |
| `metadata.doi` | String | 否 | DOI 标识符（可能为空） |
| `metadata.journal_ref` | String | 否 | 期刊引用（可能为空） |
| `metadata.primary_category` | String | 是 | 主要类别 |
| `metadata.all_categories` | Array | 是 | 所有类别列表 |
| `alphaxiv_detail` | Object | 是 | AlphaXiv 平台的详细信息 |
| `alphaxiv_detail.id` | String | 是 | AlphaXiv 内部 ID |
| `alphaxiv_detail.universal_paper_id` | String | 是 | 通用论文 ID |
| `alphaxiv_detail.title` | String | 是 | 标题 |
| `alphaxiv_detail.abstract` | String | 是 | 摘要 |
| `alphaxiv_detail.authors` | Array | 是 | 作者列表 |
| `alphaxiv_detail.publication_date` | String | 是 | 发布日期 |
| `alphaxiv_detail.license` | String | 是 | 许可证链接 |
| `alphaxiv_detail.topics` | Array | 是 | 主题标签列表 |
| `alphaxiv_detail.primary_category` | String | 是 | 主要类别 |
| `alphaxiv_detail.arxiv_url` | String | 是 | arXiv 链接 |
| `alphaxiv_detail.pdf_url` | String | 是 | PDF 链接 |
| `alphaxiv_detail.image_url` | String | 是 | 图片链接 |
| `alphaxiv_detail.metrics` | Object | 是 | 指标统计 |
| `alphaxiv_detail.metrics.upvotes` | Number | 是 | 赞同数 |
| `alphaxiv_detail.metrics.downvotes` | Number | 是 | 反对数 |
| `alphaxiv_detail.metrics.total_votes` | Number | 是 | 总投票数 |
| `alphaxiv_detail.metrics.visits_24h` | Number | 是 | 24 小时访问量 |
| `alphaxiv_detail.metrics.visits_7d` | Number | 是 | 7 天访问量 |
| `alphaxiv_detail.metrics.visits_30d` | Number | 是 | 30 天访问量 |
| `alphaxiv_detail.metrics.visits_all` | Number | 是 | 总访问量 |
| `alphaxiv_detail.github` | Object | 是 | GitHub 仓库信息 |
| `alphaxiv_detail.github.url` | String | 是 | 仓库链接 |
| `alphaxiv_detail.github.language` | String | 是 | 编程语言 |
| `alphaxiv_detail.github.stars` | Number | 是 | 星标数 |
| `alphaxiv_detail.citation` | Object | 是 | 引用信息 |
| `alphaxiv_detail.citation.bibtex` | String | 是 | BibTeX 格式引用 |
| `alphaxiv_detail.comments` | Array | 是 | 评论列表 |
| `full_text` | String | 是 | 论文的完整文本内容 |
| `id` | Number | 是 | 数据库内部 ID |
| `hits` | Object | 是 | 访问统计信息 |
| `hits.views` | String | 是 | 浏览量 |
| `hits.citations` | Number | 是 | 引用数 |
| `hits.comments` | Number | 是 | 评论数 |
| `hits.trending` | Number | 是 | 趋势值 |
| `score_detail` | Object | 是 | 论文评分详情 |
| `score_detail.scores` | Object | 是 | 各维度评分对象 |
| `score_detail.scores.novelty` | Number | 是 | 新颖性评分 |
| `score_detail.scores.methodology` | Number | 是 | 方法论评分 |
| `score_detail.scores.relevance` | Number | 是 | 相关性评分 |
| `score_detail.scores.ethics` | Number | 是 | 伦理评分 |
| `score_detail.scores.technical_quality` | Number | 是 | 技术质量评分 |
| `score_detail.scores.impact` | Number | 是 | 影响力评分 |
| `score_detail.overall_score` | Number | 是 | 总体评分 |
| `score_detail.reasoning` | String | 是 | 评分理由说明 |
| `score_detail.timestamp` | String | 是 | 评分时间戳 |
| `category_detail` | Object | 是 | 论文分类详情 |
| `category_detail.category_name` | String | 是 | 类别名称 |
| `category_detail.category_description` | String | 是 | 类别描述 |
| `category_detail.sub_categories` | Array | 是 | 子类别列表 |
| `category_detail.confidence` | Number | 是 | 分类置信度 |
| `category_detail.reasoning` | String | 是 | 分类理由 |
| `category_detail.timestamp` | String | 是 | 分类时间戳 |

## 数据类型说明

- **String**: 字符串类型
- **Number**: 数字类型（整数或浮点数）
- **Boolean**: 布尔类型（true/false）
- **Array**: 数组类型
- **Object**: 对象类型

## 必需性说明

- **是**: 该字段必须存在
- **否**: 该字段可能不存在（可选字段）
