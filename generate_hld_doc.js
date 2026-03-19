const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        Header, Footer, AlignmentType, PageNumber, HeadingLevel, 
        BorderStyle, WidthType, ShadingType, PageBreak } = require('docx');

// 文档内容数据
const documentData = {
  projectInfo: {
    name: "EmoHealer 情绪疗愈平台",
    version: "v1.0",
    date: "2026-03-19",
    author: "基于 EmoHealer 项目代码分析生成",
    srs: "EmoHealer_功能需求文档.md"
  },
  
  chapters: [
    {
      title: "1. 简介",
      sections: [
        {
          title: "1.1 目的",
          content: "本文档描述 EmoHealer 情绪疗愈平台的高层设计,包括系统架构、组件设计、数据模型和技术规范。HLD 文档旨在为开发团队、架构师和技术决策者提供系统的技术设计指导。"
        },
        {
          title: "1.2 范围",
          content: "EmoHealer 是一个基于 AIGC(人工智能生成内容)技术的情绪疗愈平台,为 18-35 岁用户提供 7×24 小时专业且温暖的情绪支持服务。系统包括以下核心组件:",
          list: [
            "用户认证与管理模块",
            "AI 智能对话系统(基于 CBT 认知行为疗法)",
            "多模态情绪识别(文本、语音、表情)",
            "个性化疗愈方案生成",
            "情绪日记与数据分析",
            "危机预警与干预机制",
            "心理测评与咨询师预约",
            "系统管理后台"
          ]
        },
        {
          title: "1.3 定义、缩写和术语",
          table: {
            headers: ["术语/缩写", "全称/定义"],
            rows: [
              ["HLD", "High-Level Design (高层设计)"],
              ["SRS", "Software Requirements Specification (软件需求规格说明书)"],
              ["CBT", "Cognitive Behavioral Therapy (认知行为疗法)"],
              ["LLM", "Large Language Model (大语言模型)"],
              ["RAG", "Retrieval-Augmented Generation (检索增强生成)"],
              ["API", "Application Programming Interface (应用程序接口)"],
              ["REST", "Representational State Transfer (表述性状态转移)"],
              ["ORM", "Object-Relational Mapping (对象关系映射)"],
              ["Docker", "容器化平台"],
              ["SQLAlchemy", "Python ORM 框架"],
              ["ECharts", "Enterprise Charts (商业级图表库)"]
            ]
          }
        },
        {
          title: "1.4 参考文献",
          list: [
            "EmoHealer 软件需求规格说明书 (SRS)",
            "FastAPI 官方文档: https://fastapi.tiangolo.com/",
            "SQLAlchemy 文档: https://docs.sqlalchemy.org/",
            "WebSocket 协议规范: RFC 6455",
            "MySQL 8.0 参考手册",
            "Docker 官方文档",
            "心理健康服务相关法律法规"
          ]
        }
      ]
    },
    {
      title: "2. 总体描述",
      sections: [
        {
          title: "2.1 产品视角",
          content: "EmoHealer 采用前后端分离的三层架构:",
          subsections: [
            {
              subtitle: "表现层 (Presentation Layer)",
              list: [
                "Web 浏览器客户端",
                "响应式 HTML5/JavaScript 界面",
                "ECharts 数据可视化组件",
                "WebSocket 实时通信客户端"
              ]
            },
            {
              subtitle: "应用层 (Application Layer)",
              list: [
                "FastAPI RESTful API 服务",
                "WebSocket 实时通信服务",
                "AI 智能体服务(多角色 LLM 集成)",
                "业务逻辑处理服务",
                "认证与授权服务"
              ]
            },
            {
              subtitle: "数据层 (Data Layer)",
              list: [
                "MySQL 8.0 关系型数据库",
                "SQLAlchemy ORM 数据访问层",
                "数据缓存策略(可选 Redis)"
              ]
            }
          ]
        },
        {
          title: "2.2 产品功能",
          table: {
            headers: ["功能模块", "功能描述", "优先级"],
            rows: [
              ["用户认证", "注册、登录、登出、Token 管理、密码修改", "高"],
              ["AI 对话", "智能对话、情绪识别、危机检测、多角色回复", "高"],
              ["情绪分析", "文本/语音/表情情绪识别、情绪趋势分析、情绪报告", "高"],
              ["疗愈方案", "AI 生成个性化方案、任务执行、完成率统计", "中"],
              ["情绪日记", "创建、查询、更新、删除日记(软删除)", "中"],
              ["危机预警", "关键词检测、预警级别评估、管理员处理", "高"],
              ["心理测评", "PHQ-9/GAD-7 测评提交、历史查询", "中"],
              ["咨询预约", "提交预约、预约列表、状态管理", "中"],
              ["系统管理", "数据驾驶舱、用户管理、Token 统计、操作日志", "中"]
            ]
          }
        },
        {
          title: "2.3 用户特征",
          table: {
            headers: ["用户类型", "特征描述", "需求", "使用场景"],
            rows: [
              ["普通用户", "18-35岁,面临工作压力、情感困扰、情绪管理需求", "完整功能访问", "随时访问、移动友好、隐私保护"],
              ["管理员", "负责系统运维、数据监控、危机处理", "管理权限", "数据看板、危机预警处理"],
              ["咨询师", "接受预约,提供专业心理咨询", "预约管理", "查看预约、提供咨询"]
            ]
          }
        },
        {
          title: "2.4 约束条件",
          subsections: [
            {
              subtitle: "技术约束",
              table: {
                headers: ["约束项", "约束描述"],
                rows: [
                  ["浏览器兼容性", "需支持 Chrome 80+、Firefox 75+、Edge 80+"],
                  ["数据库", "必须使用 MySQL 8.0+,支持 InnoDB 引擎"],
                  ["Python 版本", "后端需要 Python 3.10+"],
                  ["API 版本", "RESTful API 遵循 HTTP/1.1 规范"],
                  ["WebSocket", "必须支持 RFC 6455 协议"],
                  ["LLM 响应时间", "AI 对话响应时间 < 5 秒"]
                ]
              }
            },
            {
              subtitle: "业务约束",
              table: {
                headers: ["约束项", "约束描述"],
                rows: [
                  ["Token 有效期", "访问 Token 有效期为 7 天"],
                  ["每日对话限制", "每日最多 100 次对话"],
                  ["密码加密", "必须使用 SHA256 加密存储(带盐值)"],
                  ["数据隔离", "用户数据严格隔离,无法访问其他用户数据"],
                  ["危机响应", "检测到危机必须在 1 秒内推送预警"]
                ]
              }
            }
          ]
        },
        {
          title: "2.5 假设和依赖",
          table: {
            headers: ["依赖项", "版本/说明", "用途"],
            rows: [
              ["Python", "3.10+", "后端运行环境"],
              ["FastAPI", "0.104.0+", "Web 框架"],
              ["SQLAlchemy", "2.0+", "ORM 框架"],
              ["PyMySQL", "1.1.0+", "MySQL 数据库驱动"],
              ["Pydantic", "2.0+", "数据验证"],
              ["MySQL", "8.0+", "数据库"],
              ["ECharts", "5.4+", "前端图表库"],
              ["Docker", "20.10+", "容器化部署"],
              ["文心一言 API", "-", "LLM 服务"]
            ]
          }
        }
      ]
    },
    {
      title: "3. 系统架构",
      sections: [
        {
          title: "3.1 架构概览",
          content: "EmoHealer 采用经典的三层架构(Tiered Architecture),结合微服务理念。系统架构包括表现层、应用层、数据层和外部服务四大部分。",
          note: "架构图请参见附录中的 PlantUML 系统架构图"
        },
        {
          title: "3.2 系统设计原则",
          table: {
            headers: ["设计原则", "说明", "应用场景"],
            rows: [
              ["关注点分离", "表现层、应用层、数据层职责明确", "整体架构设计"],
              ["单一职责", "每个组件只负责一个功能领域", "服务模块划分"],
              ["开闭原则", "对扩展开放,对修改关闭", "AI 服务可替换"],
              ["依赖倒置", "依赖抽象而非具体实现", "ORM 抽象层"],
              ["RESTful 设计", "使用标准 HTTP 方法和状态码", "API 设计"],
              ["安全优先", "认证、加密、输入验证贯穿全层", "安全设计"],
              ["可扩展性", "支持横向扩展,增加服务器实例", "部署架构"],
              ["高可用性", "无单点故障,支持故障恢复", "部署和运维"],
              ["用户数据隔离", "严格的数据权限控制", "数据访问层"]
            ]
          }
        },
        {
          title: "3.3 技术栈",
          table: {
            headers: ["层次", "技术", "版本", "说明"],
            rows: [
              ["表现层", "HTML/CSS/JavaScript", "-", "标准前端技术"],
              ["表现层", "ECharts", "5.4+", "数据可视化图表库"],
              ["表现层", "WebSocket", "RFC 6455", "实时通信协议"],
              ["应用层", "Python", "3.10+", "后端编程语言"],
              ["应用层", "FastAPI", "0.104.0+", "Web 框架"],
              ["应用层", "SQLAlchemy", "2.0+", "ORM 框架"],
              ["数据层", "MySQL", "8.0+", "关系型数据库"],
              ["数据层", "Redis (可选)", "6.0+", "缓存数据库"],
              ["外部服务", "文心一言", "-", "百度 LLM API"],
              ["外部服务", "ChatGLM", "-", "智谱 AI LLM API"]
            ]
          }
        }
      ]
    },
    {
      title: "4. 组件设计",
      sections: [
        {
          title: "4.1 前端组件",
          table: {
            headers: ["组件名称", "功能描述", "技术实现"],
            rows: [
              ["页面路由器", "单页应用(SPA)路由切换", "JavaScript showPage() 函数"],
              ["认证管理器", "Token 存储、验证、自动刷新", "localStorage + 拦截器"],
              ["聊天界面", "消息显示、输入框、情绪标签选择", "HTML + CSS + JS"],
              ["WebSocket 客户端", "实时通信、心跳保活", "WebSocket API"],
              ["情绪图表", "ECharts 情绪趋势图", "ECharts line/bar 图表"],
              ["疗愈方案", "方案展示、任务执行、进度跟踪", "HTML + JS 状态管理"],
              ["情绪日记", "日记列表、编辑器、删除功能", "表单 + 列表组件"],
              ["心理测评", "PHQ-9/GAD-7 量表、结果展示", "表单 + 结果页面"],
              ["危机预警", "预警弹窗、求助热线显示", "模态框组件"]
            ]
          },
          note: "前端组件交互图请参见附录"
        },
        {
          title: "4.2 后端组件",
          table: {
            headers: ["路由模块", "路径前缀", "主要端点"],
            rows: [
              ["API 路由", "/api", "所有业务 API"],
              ["认证路由", "/api/auth", "登录/注册/登出/验证"],
              ["聊天路由", "/api/chat", "发送消息/历史记录"],
              ["情绪路由", "/api/emotion", "情绪分析/趋势/报告"],
              ["疗愈方案路由", "/api/plans", "生成/查询方案"],
              ["日记路由", "/api/diary", "CRUD 操作"],
              ["测评路由", "/api/assessment", "提交/查询测评"],
              ["预约路由", "/api/appointment", "提交/查询预约"],
              ["管理路由", "/api/admin", "驾驶舱/用户管理/统计"],
              ["WebSocket 路由", "/ws", "实时聊天连接"]
            ]
          },
          note: "后端组件架构图请参见附录"
        },
        {
          title: "4.3 AI 智能体设计",
          content: "多角色智能体架构:",
          table: {
            headers: ["角色", "ID", "特质", "适用场景"],
            rows: [
              ["Listener (倾听者)", "1", "温暖、同理心、耐心", "初期对话、负面情绪"],
              ["Supporter (支持者)", "2", "积极、乐观、坚定", "需要鼓励时"],
              ["Coach (教练)", "3", "启发性、好奇心", "中期引导、思考启发"],
              ["Educator (教育者)", "4", "专业、清晰、博学", "需要知识解释时"],
              ["MindfulnessGuide (正念引导)", "5", "平和、宁静", "正念练习引导"]
            ]
          }
        },
        {
          title: "4.4 数据库组件",
          table: {
            headers: ["表名", "用途", "记录量预估"],
            rows: [
              ["user", "用户基本信息", "10,000+"],
              ["user_token", "用户登录 Token", "50,000+"],
              ["chat_record", "对话记录", "1,000,000+"],
              ["emotion_log", "情绪日志", "2,000,000+"],
              ["healing_plan", "疗愈方案", "100,000+"],
              ["crisis_alert", "危机预警记录", "1,000+"],
              ["psychological_assessment", "心理测评", "50,000+"],
              ["consultation_appointment", "咨询预约", "10,000+"],
              ["emotion_diary", "情绪日记", "200,000+"],
              ["system_config", "系统配置", "50"],
              ["token_usage", "Token 消耗记录", "500,000+"],
              ["operation_log", "操作日志", "1,000,000+"]
            ]
          },
          note: "数据库 ER 图请参见附录"
        }
      ]
    },
    {
      title: "5. 数据设计",
      sections: [
        {
          title: "5.1 数据模型",
          content: "核心数据实体包括用户、Token、对话记录、情绪日志、疗愈方案、危机预警、心理测评、咨询预约、情绪日记、系统配置、Token消耗和操作日志。",
          note: "完整的数据模型关系请参见附录中的 ER 图"
        },
        {
          title: "5.2 数据库架构",
          subsections: [
            {
              subtitle: "存储引擎",
              content: "所有表使用 InnoDB 引擎,支持事务(ACID)、行级锁定、外键约束和崩溃恢复。"
            },
            {
              subtitle: "字符集",
              content: "字符集: utf8mb4 (支持完整 Unicode 字符包括 emoji); 排序规则: utf8mb4_unicode_ci (不区分大小写)"
            },
            {
              subtitle: "索引策略",
              content: "所有表均建立适当的索引以优化查询性能,主要包括主键索引、唯一索引和普通索引。"
            }
          ]
        },
        {
          title: "5.3 缓存策略",
          content: "当前版本暂未实现缓存,所有数据直接从 MySQL 查询。未来可考虑使用 Redis 作为缓存层。",
          note: "未来缓存设计包括用户信息缓存、Token验证缓存、系统配置缓存等"
        }
      ]
    },
    {
      title: "6. 接口设计",
      sections: [
        {
          title: "6.1 用户接口",
          table: {
            headers: ["页面", "路由路径", "主要功能", "认证要求"],
            rows: [
              ["主页(聊天页面)", "#chat", "AI对话、情绪选择、消息历史", "必须登录"],
              ["登录页", "#login", "用户名/密码登录", "否"],
              ["注册页", "#register", "新用户注册", "否"],
              ["用户中心", "#profile", "个人信息、统计数据", "必须登录"],
              ["情绪报告", "#emotion-report", "情绪趋势图表、分析报告", "必须登录"],
              ["疗愈方案", "#healing-plan", "今日方案、任务执行", "必须登录"],
              ["情绪日记", "#diary", "日记列表、编辑、删除", "必须登录"],
              ["心理测评", "#assessment", "PHQ-9/GAD-7量表", "必须登录"],
              ["咨询师预约", "#appointment", "预约表单、预约列表", "必须登录"]
            ]
          }
        },
        {
          title: "6.2 API 接口",
          content: "RESTful API 设计原则:",
          list: [
            "资源导向: URL 表示资源,HTTP 方法表示操作",
            "统一响应格式: 所有接口返回统一 JSON 结构",
            "状态码使用: 遵循 HTTP 标准状态码",
            "版本控制: 通过 URL 前缀 /api 控制版本"
          ],
          note: "完整的 API 端点清单请参见附录"
        },
        {
          title: "6.3 WebSocket 接口",
          content: "实时通信接口:",
          list: [
            "实时聊天: ws://localhost:8092/ws/chat?token=xxx",
            "管理后台: ws://localhost:8092/ws/admin",
            "消息类型: message, typing, heartbeat, crisis_alert",
            "心跳机制: 每30秒一次"
          ]
        },
        {
          title: "6.4 第三方接口",
          content: "LLM API 集成:",
          table: {
            headers: ["服务提供商", "模型", "优势"],
            rows: [
              ["百度文心一言", "Ernie-Lite-8k", "中文理解强、响应快"],
              ["智谱 ChatGLM", "GLM-4", "开源、可定制"],
              ["OpenAI", "GPT-3.5/4", "能力最强"]
            ]
          }
        }
      ]
    },
    {
      title: "7. 安全设计",
      sections: [
        {
          title: "7.1 认证和授权",
          subsections: [
            {
              subtitle: "Token 认证机制",
              list: [
                "Token 生成: 用户登录成功后生成随机 Token (256位)",
                "Token 验证: 通过 Authorization 头传递,中间件验证",
                "Token 失效: 用户登出时删除,过期自动失效"
              ]
            },
            {
              subtitle: "密码安全",
              table: {
                headers: ["安全措施", "实现方式"],
                rows: [
                  ["加密算法", "SHA-256"],
                  ["盐值", "固定盐值 \"EmoHealer2026\""],
                  ["存储", "只存储哈希值,不存储明文密码"],
                  ["传输加密", "HTTPS (生产环境)"]
                ]
              }
            },
            {
              subtitle: "权限控制",
              table: {
                headers: ["角色", "权限范围", "可访问接口"],
                rows: [
                  ["普通用户", "只能访问自己的数据", "用户中心、聊天、日记、测评等"],
                  ["管理员", "可访问所有数据 + 管理功能", "管理接口、用户管理、危机预警处理"]
                ]
              }
            }
          ]
        },
        {
          title: "7.2 数据加密",
          list: [
            "传输层加密: 生产环境必须使用 HTTPS (SSL/TLS 证书)",
            "存储层加密: 密码使用 SHA-256 哈希存储",
            "未来增强: 可使用 MySQL 加密函数 AES_ENCRYPT() 加密敏感字段"
          ]
        },
        {
          title: "7.3 输入验证",
          content: "前端验证和后端验证双重保障:",
          list: [
            "前端验证: HTML5 表单验证 (pattern, type, maxlength)",
            "后端验证: Pydantic 模型验证",
            "SQL 注入防护: 使用 SQLAlchemy ORM 参数化查询"
          ]
        },
        {
          title: "7.4 安全协议",
          list: [
            "CORS 策略: 开发环境允许所有来源,生产环境配置白名单",
            "速率限制: 未来实现 (登录 5次/10分钟, API调用 100次/分钟)",
            "审计日志: 所有关键操作记录到 operation_log 表"
          ]
        }
      ]
    },
    {
      title: "8. 非功能需求",
      sections: [
        {
          title: "8.1 性能需求",
          table: {
            headers: ["指标", "目标", "测量方法"],
            rows: [
              ["页面加载时间", "< 3秒", "浏览器开发者工具"],
              ["API响应时间(数据库查询)", "< 500ms", "API日志时间戳差"],
              ["AI对话响应时间", "< 5秒", "前端-后端时间差"],
              ["WebSocket连接建立", "< 2秒", "连接事件时间"],
              ["情绪分析响应", "< 1秒", "API日志"],
              ["数据库查询响应", "< 100ms(简单查询)", "MySQL慢查询日志"]
            ]
          }
        },
        {
          title: "8.2 可扩展性",
          subsections: [
            {
              subtitle: "水平扩展",
              list: [
                "应用服务器: 支持 Nginx 负载均衡,多实例部署",
                "数据库: MySQL 主从复制,读写分离"
              ]
            },
            {
              subtitle: "垂直扩展",
              list: [
                "升级服务器配置 (CPU、内存、磁盘)",
                "MySQL 配置优化 (innodb_buffer_pool_size 等)"
              ]
            }
          ]
        },
        {
          title: "8.3 可靠性",
          table: {
            headers: ["故障场景", "容错措施", "恢复策略"],
            rows: [
              ["数据库宕机", "连接池重试", "自动重连 + 错误提示"],
              ["LLM API 超时", "规则模板回退", "使用预设回复"],
              ["网络中断", "WebSocket重连", "指数退避重连"],
              ["服务器崩溃", "日志持久化", "重启后日志恢复"]
            ]
          }
        },
        {
          title: "8.4 可用性",
          content: "系统可用性目标: ≥ 99.5%; 年停机时间: < 43.8 小时",
          list: [
            "应用服务器: 多实例 + 负载均衡 (99.9%)",
            "数据库: 主从复制 + 自动故障转移 (99.5%)",
            "文件存储: OSS 对象存储 (99.99%)"
          ]
        }
      ]
    },
    {
      title: "9. 部署架构",
      sections: [
        {
          title: "9.1 部署环境",
          subsections: [
            {
              subtitle: "开发环境",
              content: "本地运行: 后端 python main.py (8092端口), 前端 python -m http.server 5000"
            },
            {
              subtitle: "测试环境",
              content: "Docker Compose 部署,包含 MySQL 和 Backend 服务"
            },
            {
              subtitle: "生产环境",
              content: "云服务器 + Nginx 负载均衡 + MySQL 主从复制"
            }
          ]
        },
        {
          title: "9.2 基础设施要求",
          table: {
            headers: ["组件", "最低配置", "推荐配置"],
            rows: [
              ["应用服务器", "2核/4GB", "4核/8GB+"],
              ["数据库服务器", "2核/4GB", "4核/16GB+"],
              ["存储", "50GB SSD", "100GB+ SSD"],
              ["带宽", "10Mbps", "100Mbps+"],
              ["操作系统", "Ubuntu 20.04+", "Ubuntu 22.04 LTS"]
            ]
          }
        },
        {
          title: "9.3 部署流程",
          list: [
            "准备服务器,安装基础依赖 (Python 3.10+, MySQL 8.0+)",
            "克隆代码仓库",
            "安装 Python 依赖 (pip install -r requirements.txt)",
            "初始化数据库 (mysql < init.sql)",
            "配置环境变量 (.env文件)",
            "启动应用服务 (python main.py)",
            "配置 Nginx 反向代理",
            "申请 SSL 证书 (Let's Encrypt)",
            "配置防火墙规则 (开放端口 80, 443, 8092)",
            "配置域名解析",
            "测试系统功能",
            "配置监控告警"
          ]
        }
      ]
    },
    {
      title: "10. 附录",
      sections: [
        {
          title: "10.1 架构图表",
          content: "系统逻辑架构图、前端组件图、后端组件图、数据库 ER 图、时序图等请参见对应章节的 PlantUML 图表描述。"
        },
        {
          title: "10.2 数据字典",
          table: {
            headers: ["表名", "字段名", "类型", "说明"],
            rows: [
              ["user", "id", "BIGINT", "用户ID,自增主键"],
              ["user", "username", "VARCHAR(50)", "用户名,唯一"],
              ["user", "password_hash", "VARCHAR(255)", "SHA256密码哈希"],
              ["user", "status", "TINYINT", "用户状态:0-禁用 1-正常"],
              ["chat_record", "emotion_type", "VARCHAR(20)", "情绪类型"],
              ["chat_record", "emotion_score", "DECIMAL(5,2)", "情绪得分0-100"],
              ["crisis_alert", "alert_level", "VARCHAR(20)", "预警级别"],
              ["healing_plan", "tasks", "JSON", "任务列表,JSON数组"],
              ["emotion_diary", "mood_tags", "JSON", "心情标签,JSON数组"],
              ["token_usage", "total_tokens", "INT", "总Token消耗"]
            ]
          }
        },
        {
          title: "10.3 API 接口清单",
          content: "完整的 API 接口列表包括认证接口、聊天接口、情绪接口、疗愈方案接口、日记接口、测评接口、预约接口、管理接口等,详见第6章接口设计。"
        },
        {
          title: "10.4 配置参数",
          table: {
            headers: ["配置项", "环境变量", "默认值", "说明"],
            rows: [
              ["数据库主机", "DB_HOST", "localhost", "MySQL服务器地址"],
              ["数据库端口", "DB_PORT", "3306", "MySQL端口"],
              ["数据库用户", "DB_USER", "root", "MySQL用户名"],
              ["数据库密码", "DB_PASSWORD", "19891213", "MySQL密码"],
              ["数据库名", "DB_NAME", "emohealer", "数据库名称"],
              ["服务主机", "HOST", "0.0.0.0", "监听地址"],
              ["服务端口", "PORT", "8092", "FastAPI端口"]
            ]
          }
        },
        {
          title: "10.5 错误代码",
          table: {
            headers: ["错误代码", "HTTP状态", "描述", "处理建议"],
            rows: [
              ["200", "200", "成功", "-"],
              ["400", "400", "请求参数错误", "检查参数格式"],
              ["401", "401", "未授权/Token无效", "重新登录"],
              ["403", "403", "账号禁用", "联系管理员"],
              ["404", "404", "资源不存在", "检查资源ID"],
              ["422", "422", "数据验证失败", "检查输入数据"],
              ["500", "500", "服务器内部错误", "联系技术支持"],
              ["503", "503", "服务不可用", "稍后重试"]
            ]
          }
        },
        {
          title: "10.6 安全需求总结",
          content: "关键安全措施:",
          list: [
            "认证: Token + Salted SHA256密码",
            "授权: 基于角色的访问控制(RBAC)",
            "加密: HTTPS + SHA256哈希",
            "验证: Pydantic + 参数化查询(防SQL注入)",
            "审计: operation_log表记录所有操作",
            "CORS: 配置CORS白名单",
            "危机响应: 实时检测 + 即时推送"
          ]
        },
        {
          title: "10.7 部署检查清单",
          list: [
            "服务器配置满足最低要求",
            "Python 3.10+ 已安装",
            "MySQL 8.0+ 已安装并初始化",
            "所有依赖包已安装(requirements.txt)",
            "环境变量已配置(.env文件)",
            "数据库连接测试通过",
            "API服务启动成功(python main.py)",
            "Nginx反向代理已配置",
            "SSL证书已安装",
            "域名DNS解析已配置",
            "防火墙规则已设置",
            "API文档可访问(/docs)",
            "前端页面可访问(/emohealer)",
            "WebSocket连接测试通过",
            "用户注册/登录功能测试通过",
            "AI对话功能测试通过",
            "情绪分析功能测试通过",
            "危机预警功能测试通过",
            "监控系统已配置",
            "备份策略已设置",
            "日志系统已启用"
          ]
        }
      ]
    }
  ]
};

// 创建文档
async function createDocument() {
  const doc = new Document({
    styles: {
      default: {
        document: {
          run: {
            font: "Arial",
            size: 24 // 12pt
          }
        }
      },
      paragraphStyles: [
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: {
            size: 32, // 16pt
            bold: true,
            font: "Arial",
            color: "2E75B6"
          },
          paragraph: {
            spacing: { before: 240, after: 240 }
          }
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: {
            size: 28, // 14pt
            bold: true,
            font: "Arial",
            color: "2E75B6"
          },
          paragraph: {
            spacing: { before: 180, after: 180 }
          }
        },
        {
          id: "Heading3",
          name: "Heading 3",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: {
            size: 26, // 13pt
            bold: true,
            font: "Arial",
            color: "2E75B6"
          },
          paragraph: {
            spacing: { before: 120, after: 120 }
          }
        }
      ]
    },
    sections: [{
      properties: {
        page: {
          size: {
            width: 12240, // US Letter: 8.5 inches
            height: 15840 // US Letter: 11 inches
          },
          margin: {
            top: 1440,    // 1 inch
            right: 1440,
            bottom: 1440,
            left: 1440
          }
        }
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: `${documentData.projectInfo.name} - 高层设计文档 (HLD)`,
                  bold: true,
                  size: 20
                })
              ],
              alignment: AlignmentType.CENTER
            })
          ]
        })
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              children: [
                new TextRun({ text: "版本: ", size: 20 }),
                new TextRun({ text: documentData.projectInfo.version, size: 20 }),
                new TextRun({ text: "  |  日期: ", size: 20 }),
                new TextRun({ text: documentData.projectInfo.date, size: 20 }),
                new TextRun({ text: "  |  页码: ", size: 20 }),
                new TextRun({ children: [PageNumber.CURRENT], size: 20 })
              ],
              alignment: AlignmentType.CENTER
            })
          ]
        })
      },
      children: buildDocumentContent()
    }]
  });

  // 生成文档
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync("EmoHealer_HLD_v1.0.docx", buffer);
  console.log("文档生成成功: EmoHealer_HLD_v1.0.docx");
}

// 构建文档内容
function buildDocumentContent() {
  const children = [];
  
  // 标题页
  children.push(
    new Paragraph({
      children: [
        new TextRun({
          text: documentData.projectInfo.name,
          bold: true,
          size: 48,
          color: "2E75B6"
        })
      ],
      alignment: AlignmentType.CENTER,
      spacing: { before: 1200, after: 600 }
    })
  );
  
  children.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "高层设计文档 (High-Level Design)",
          size: 32,
          color: "2E75B6"
        })
      ],
      alignment: AlignmentType.CENTER,
      spacing: { after: 600 }
    })
  );
  
  // 文档信息
  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "版本: ", bold: true }),
        new TextRun(documentData.projectInfo.version)
      ],
      spacing: { before: 600 }
    })
  );
  
  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "日期: ", bold: true }),
        new TextRun(documentData.projectInfo.date)
      ]
    })
  );
  
  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "作者: ", bold: true }),
        new TextRun(documentData.projectInfo.author)
      ]
    })
  );
  
  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "对应 SRS: ", bold: true }),
        new TextRun(documentData.projectInfo.srs)
      ],
      spacing: { after: 1200 }
    })
  );
  
  // 分页
  children.push(new Paragraph({ children: [new PageBreak()] }));
  
  // 目录
  children.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "目录",
          bold: true,
          size: 32,
          color: "2E75B6"
        })
      ],
      spacing: { before: 240, after: 240 }
    })
  );
  
  documentData.chapters.forEach(chapter => {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: chapter.title, size: 24 })],
        spacing: { before: 120 }
      })
    );
    
    if (chapter.sections) {
      chapter.sections.forEach(section => {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: "    " + section.title, size: 22 })],
            spacing: { before: 60 }
          })
        );
      });
    }
  });
  
  // 分页
  children.push(new Paragraph({ children: [new PageBreak()] }));
  
  // 章节内容
  documentData.chapters.forEach(chapter => {
    // 章节标题
    children.push(
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: chapter.title })]
      })
    );
    
    // 小节内容
    if (chapter.sections) {
      chapter.sections.forEach(section => {
        children.push(...buildSection(section));
      });
    }
    
    // 章节间分页
    children.push(new Paragraph({ children: [new PageBreak()] }));
  });
  
  // 文档版本历史
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun({ text: "文档版本历史" })]
    })
  );
  
  const versionTable = createTable({
    headers: ["版本", "日期", "修订人", "修订内容"],
    rows: [
      ["v1.0", "2026-03-19", "Claude", "初始版本,基于EmoHealer项目代码分析生成"]
    ]
  });
  children.push(versionTable);
  
  return children;
}

// 构建小节内容
function buildSection(section) {
  const children = [];
  
  // 小节标题
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_2,
      children: [new TextRun({ text: section.title })]
    })
  );
  
  // 文本内容
  if (section.content) {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: section.content, size: 24 })],
        spacing: { before: 120, after: 120 }
      })
    );
  }
  
  // 列表内容
  if (section.list) {
    section.list.forEach((item, index) => {
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: `${index + 1}. `, bold: true }),
            new TextRun({ text: item, size: 24 })
          ],
          spacing: { before: 60 }
        })
      );
    });
  }
  
  // 表格内容
  if (section.table) {
    children.push(createTable(section.table));
  }
  
  // 子小节
  if (section.subsections) {
    section.subsections.forEach(subsection => {
      children.push(
        new Paragraph({
          heading: HeadingLevel.HEADING_3,
          children: [new TextRun({ text: subsection.subtitle })]
        })
      );
      
      if (subsection.content) {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: subsection.content, size: 24 })],
            spacing: { before: 120, after: 120 }
          })
        );
      }
      
      if (subsection.list) {
        subsection.list.forEach((item, index) => {
          children.push(
            new Paragraph({
              children: [
                new TextRun({ text: `${index + 1}. `, bold: true }),
                new TextRun({ text: item, size: 24 })
              ],
              spacing: { before: 60 }
            })
          );
        });
      }
      
      if (subsection.table) {
        children.push(createTable(subsection.table));
      }
    });
  }
  
  // 备注
  if (section.note) {
    children.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "注: ",
            bold: true,
            italics: true,
            size: 22,
            color: "666666"
          }),
          new TextRun({
            text: section.note,
            italics: true,
            size: 22,
            color: "666666"
          })
        ],
        spacing: { before: 120, after: 120 }
      })
    );
  }
  
  return children;
}

// 创建表格
function createTable(data) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
  const borders = { top: border, bottom: border, left: border, right: border };
  
  const rows = [];
  
  // 表头
  rows.push(
    new TableRow({
      children: data.headers.map(header => 
        new TableCell({
          borders,
          shading: { fill: "2E75B6", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: header,
                  bold: true,
                  color: "FFFFFF",
                  size: 22
                })
              ]
            })
          ]
        })
      )
    })
  );
  
  // 数据行
  data.rows.forEach((row, index) => {
    rows.push(
      new TableRow({
        children: row.map(cell =>
          new TableCell({
            borders,
            shading: { 
              fill: index % 2 === 0 ? "F2F2F2" : "FFFFFF",
              type: ShadingType.CLEAR
            },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [
              new Paragraph({
                children: [new TextRun({ text: cell, size: 22 })]
              })
            ]
          })
        )
      })
    );
  });
  
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    rows,
    spacing: { before: 120, after: 120 }
  });
}

// 执行
createDocument().catch(err => {
  console.error("生成文档失败:", err);
  process.exit(1);
});
