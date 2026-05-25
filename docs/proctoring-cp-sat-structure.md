# 监考编排 CP-SAT 结构图

本文档根据当前仓库代码整理监考编排求解器的结构，重点覆盖变量、约束、目标函数和求解流程。

相关代码入口：

- `backend/rpc_server.py`
- `backend/application/proctoring_service.py`
- `backend/proctoring/core/cp_sat/solver.py`
- `backend/proctoring/core/cp_sat/assignment.py`
- `backend/proctoring/core/cp_sat/objectives.py`
- `backend/proctoring/core/validators.py`

## 1. 结构图

```mermaid
flowchart TD
    A["输入数据
    teachers
    subjects_data
    config
    imported schedule/preset"] --> B["构造 Schedule
    mode
    roomCount
    subjectDurations
    constraints"]
    B --> C["预检查
    check_feasibility()
    锁定安排冲突诊断"]
    C --> D["构造 SubjectContext
    subject_id
    date
    time
    duration
    sort_key"]

    D --> E["生成槽位 Slot
    slot = (subject_id, room, slot_index)"]
    B --> E

    E --> F["候选老师过滤
    _teacher_can_take_slot()"]

    F --> G["布尔变量
    x[t, s, r, k] ∈ {0,1}
    老师 t 是否负责槽位 (s,r,k)"]

    G --> H["硬约束"]
    H --> H1["每个槽位恰好 1 人
    sum_t x[t,s,r,k] = 1"]
    H --> H2["老师场次数上限
    count_t <= max_sessions"]
    H --> H3["同一老师不能同时出现在冲突科目
    overlap pair <= 1"]
    H --> H4["锁定安排必须保留
    fixed slot = 1"]
    H --> H5["预设考场限制
    preset_room only"]
    H --> H6["禁监考科目限制
    unavailable_subjects"]
    H --> H7["双监考搭配
    gender_mix / internal_mix"]
    H --> H8["对称性消除
    双监考左右槽位顺序规范化"]

    G --> I["派生统计变量"]
    I --> I1["load[t,s]
    老师 t 是否承担科目 s"]
    I --> I2["count_t
    老师总监考科目数"]
    I --> I3["current_duration_t
    本次监考时长"]
    I --> I4["overall_duration_t
    历史 + 本次总时长"]
    I --> I5["room_usage_total
    使用过多少不同考场"]
    I --> I6["consecutive_total
    连续场次次数"]

    I --> J["目标函数阶段
    _build_objective_stages()"]

    J --> J1["时长均衡模式
    1 minimize max_overall_duration
    2 minimize count_range
    3 maximize min_overall_duration
    4 minimize overall_duration_deviation
    5 minimize max_count
    6 minimize count_deviation"]

    J --> J2["场次数均衡模式
    1 minimize max_count
    2 maximize min_count
    3 minimize count_deviation
    4 minimize max_overall_duration
    5 maximize min_overall_duration
    6 minimize overall_duration_deviation"]

    J --> J3["附加偏好
    minimize/maximize distinct_rooms
    minimize consecutive_sessions"]

    J --> K["分阶段 CP-SAT 求解
    每阶段锁定上一阶段最优值
    可用 hint 继续搜索"]
    K --> L["输出 schedule
    exams
    teacher assignments
    metrics
    stages report"]
```

## 2. 读图说明

### 2.1 变量层

- 核心决策变量是 `x[t,s,r,k]`
- 含义是“老师 `t` 是否被分配到科目 `s`、考场 `r`、槽位 `k`”
- 这是一个布尔变量，也是整个模型唯一真正做离散决策的主变量

### 2.2 约束层

- 每个监考槽位必须且只能有一位老师
- 每位老师的总监考段数不能超过 `max_sessions`
- 同一老师不能被安排到时间重叠的两个科目
- 导入并锁定的位置必须保留
- 如果教师设置了预设考场，则只能出现在对应考场
- 如果教师设置了禁监考科目，则对应科目不能分配
- 双监考模式下可以额外启用性别搭配和本外校搭配

### 2.3 目标函数层

- 求解器不是把所有目标做成一个总加权和
- 当前实现采用“分阶段字典序优化”
- 即先求最重要目标的最优值，再把该值锁住，继续优化下一目标
- 这样能减少权重难调的问题，也更符合排班系统里的“主目标优先，次目标细化”思路

## 3. 代码映射

- 求解入口：`backend/application/proctoring_service.py`
- 主求解器：`backend/proctoring/core/cp_sat/solver.py`
- 候选过滤与冲突对构造：`backend/proctoring/core/cp_sat/assignment.py`
- 目标阶段定义：`backend/proctoring/core/cp_sat/objectives.py`
- 预检查：`backend/proctoring/core/validators.py`
- 结果指标：`backend/proctoring/core/cp_sat/metrics.py`

## 4. 备注

- 本文档描述的是当前仓库实现，不是抽象设计稿
- 如果后续新增目标函数或搭配约束，建议同步更新这张 Mermaid 图
