# 论文数据结构字段说明

本文档描述了 `one_paper_schema.json` 文件中各个字段的含义和结构。

## 根级字段

### alphaxiv_overview
论文的 AlphaXiv 概览信息，包含状态、更新时间和多语言概览内容。
- **state**: 处理状态（如 "done" 表示已完成）
- **updatedAt**: 最后更新时间戳（毫秒）
- **overviews**: 多语言概览对象
  - **zh**: 中文版本概览
    - **title**: 论文中文标题
    - **abstract**: 中文摘要
    - **summary**: 摘要信息对象
      - **summary**: 简短总结
      - **originalProblem**: 原始问题列表
      - **solution**: 解决方案列表
      - **keyInsights**: 关键洞察列表
      - **results**: 结果列表
    - **overview**: 详细概述（Markdown 格式）
    - **citations**: 引用文献列表
  - **en**: 英文版本概览（结构同中文）

### arxiv_id
论文的 arXiv ID（如 "2512.23647"）

### abstract
论文的英文摘要

### affiliation_detail
论文作者的机构详细信息
- **affiliations**: 作者列表，每个作者包含：
  - **author**: 作者姓名
  - **author_email**: 作者邮箱（可能为空）
  - **org**: 所属机构
  - **org_email**: 机构邮箱（可能为空）
  - **is_industry**: 是否为产业界（布尔值）
- **timestamp**: 时间戳
- **text_length**: 文本长度
- **pdf_minio_info**: PDF 文件存储信息
  - **bucket**: 存储桶名称
  - **object_name**: 对象名称
  - **uploaded_at**: 上传时间
  - **size**: 文件大小（字节）
- **markdown_minio_info**: Markdown 文件存储信息（结构同 PDF）

### title
论文标题

### metadata
论文元数据信息
- **category**: 类别缩写
- **authors**: 作者列表
- **timestamp**: 时间戳
- **date**: 发布日期
- **pdf_url**: PDF 下载链接
- **arxiv_url**: arXiv 页面链接
- **doi**: DOI 标识符（可能为空）
- **journal_ref**: 期刊引用（可能为空）
- **primary_category**: 主要类别
- **all_categories**: 所有类别列表

### alphaxiv_detail
AlphaXiv 平台的详细信息
- **id**: AlphaXiv 内部 ID
- **universal_paper_id**: 通用论文 ID
- **title**: 标题
- **abstract**: 摘要
- **authors**: 作者列表
- **publication_date**: 发布日期
- **license**: 许可证链接
- **topics**: 主题标签列表
- **primary_category**: 主要类别
- **arxiv_url**: arXiv 链接
- **pdf_url**: PDF 链接
- **image_url**: 图片链接
- **metrics**: 指标统计
  - **upvotes**: 赞同数
  - **downvotes**: 反对数
  - **total_votes**: 总投票数
  - **visits_24h**: 24 小时访问量
  - **visits_7d**: 7 天访问量
  - **visits_30d**: 30 天访问量
  - **visits_all**: 总访问量
- **github**: GitHub 仓库信息
  - **url**: 仓库链接
  - **language**: 编程语言
  - **stars**: 星标数
- **citation**: 引用信息
  - **bibtex**: BibTeX 格式引用
- **comments**: 评论列表

### full_text
论文的完整文本内容

### id
数据库内部 ID（数字）

### hits
访问统计信息
- **views**: 浏览量
- **citations**: 引用数
- **comments**: 评论数
- **trending**: 趋势值

### score_detail
论文评分详情
- **scores**: 各维度评分对象
  - **novelty**: 新颖性评分
  - **methodology**: 方法论评分
  - **relevance**: 相关性评分
  - **ethics**: 伦理评分
  - **technical_quality**: 技术质量评分
  - **impact**: 影响力评分
- **overall_score**: 总体评分
- **reasoning**: 评分理由说明
- **timestamp**: 评分时间戳

### category_detail
论文分类详情
- **category_name**: 类别名称
- **category_description**: 类别描述
- **sub_categories**: 子类别列表
- **confidence**: 分类置信度
- **reasoning**: 分类理由
- **timestamp**: 分类时间戳
