---
name: agent_dev_pattern
description: Profile Agent开发的标准模式——每个Agent的通用开发套路
type: project
---

## Profile Agent 开发完整过程记录

### 最终代码

`app/agents/profile_agent.py`:

```python
def profile_agent(state: LearningState) -> dict:
    history = state.get("history")
    student_id = state.get("student_id")

    # 1. 加载旧画像（增量更新）
    pre_profile = profile_service.get(student_id)
    pre_profile_prompt = ""
    if pre_profile:
        pre_profile_prompt = f"学生的现有画像信息：{pre_profile.json()}\n"

    # 2. Prompt + with_structured_output
    model = ChatTongyi(model="qwen3-max", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个学习画像构建助手...{pre_profile_prompt}..."),
        MessagesPlaceholder("history"),
        ("user", "请根据以上对话，帮我抽取学生的特征，构建画像。"),
    ])

    chain = prompt | model.with_structured_output(StudentProfile)
    profile = chain.invoke({"history": history, "pre_profile_prompt": pre_profile_prompt})
    profile.student_id = state["student_id"]

    # 3. 持久化
    profile_service.save_or_update(profile)

    # 4. 返回 dict 更新 state
    return {"profile": profile, "next_agent": "path_agent"}
```

### 开发每个 Agent 的标准套路（4 步法）

```
┌──────────────────────────────────────────────────┐
│  第1步：接收 state 中需要的数据                   │
│  例：history, student_id, pre_profile 等          │
├──────────────────────────────────────────────────┤
│  第2步：拼 Prompt + 调 LLM                        │
│      · 用 ChatPromptTemplate.format_messages     │
│      · 用 with_structured_output(PydanticModel)  │
│      · chain = prompt | model.with_structured... │
├──────────────────────────────────────────────────┤
│  第3步：持久化（如果需要）                        │
│      · 调对应的 service.save/update               │
│      · 或存 ChromaDB                              │
├──────────────────────────────────────────────────┤
│  第4步：return dict 更新 state                    │
│      · 返回本轮产出的字段                         │
│      · 设置 next_agent 路由（如果 graph 需要）    │
└──────────────────────────────────────────────────┘
```

### 踩过的坑（后续避免）

1. **返回类型必须是 dict，不是 ORM 对象，也不是 Pydantic 实例** — LangGraph 节点函数必须返回 dict 来更新 LearningState
2. **不要直接修改 state** — `state["x"] = y` 不保证生效，用 return dict
3. **LLM 可能返回 JSON 字符串而非列表** — 在 Pydantic model 加 `field_validator` 兼容
4. **Table 创建** — 测试时如果直接跑 Agent 脚本，需要确保 `create_all` 被执行（放 models.py 底部）
5. **ORM 不能当 schema 给 LLM** — 用 `models/user.py` 的纯 Pydantic model
6. **`list[BaseMessage]` vs `list[tuple]`** — MessagePlaceholder 只认 BaseMessage 对象
7. **运行方式** — `python app/xxx.py` 报 No module named 'app'，必须用 `python -m app.xxx`

### 架构分层

```
api/routes.py  ─────  HTTP 层（请求/响应）
      │
graph/graph.py  ────  编排层（LangGraph 图）
      │
agents/xxx_agent.py  LLM 交互层（拼 prompt + 调模型）
      │
services/xxx_service  业务逻辑层（持久化等）
      │
database/models.py    数据访问层（ORM）
```


  开发 Profile Agent 的标准套路

  你这次实际走通了一个完整的 "4 步法"，后续 6 个 Agent 全按这个模式来：

  1. 从 state 取数据
          ↓
  2. 拼 Prompt → 调 LLM（with_structured_output）
          ↓
  3. 持久化（数据库 / ChromaDB）
          ↓
  4. return dict 更新 state

  关键原则（以后每个 Agent 都一样）

  ┌──────────────────┬─────────────────────────────────────────┐
  │       原则       │                  说明                   │
  ├──────────────────┼─────────────────────────────────────────┤
  │ Agent 不碰数据库 │ LLM 只管生成，存库交给 service          │
  ├──────────────────┼─────────────────────────────────────────┤
  │ 返回必须是 dict  │ 不是 ORM，不是 Pydantic 对象            │
  ├──────────────────┼─────────────────────────────────────────┤
  │ 不直接改 state   │ state["x"] = y 无效，用 return {"x": y} │
  ├──────────────────┼─────────────────────────────────────────┤
  │ ORM 不给 LLM     │ 给 LLM 的 schema 用纯 Pydantic model    │
  └──────────────────┴─────────────────────────────────────────┘

  踩过的坑（已记入记忆文件，后续自动提醒）

  1. python app/xxx.py → 报 No module named 'app'，要用 python -m app.xxx
  2. 测试不经过 main.py，要确保 create_all 在 models 里也执行
  3. LLM 可能把 list 输出成 JSON 字符串，需要 field_validator 兼容
  4. MessagePlaceholder 只认 BaseMessage 对象，不认 tuple 或 dict

  ---
  你的用户画像（已记录）

  如果你之后想让我教你新的东西，我会基于以下认知来回答：

  - LangGraph 你已经会了（状态、节点、边、条件路由、循环、Map-Reduce、Send）
  - LangChain 核心组件你会了（ChatPromptTemplate、with_structured_output、ChromaDB、RAG）
  - SQLAlchemy+SQLite 你刚入门，但足够用了
  - 你喜欢先试再问，会主动提优化方案，需要我判断"对不对" + 给出"标准做法"
  - 沟通用中文 + 代码对比（✅ vs ❌）+ 讲原因

  ---
  准备好了告诉我，继续开发下一个 Agent。