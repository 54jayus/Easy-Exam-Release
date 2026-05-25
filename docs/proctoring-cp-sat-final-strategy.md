# 监考编排 CP-SAT 定版策略说明

本文档记录当前仓库已经落地并验证过的监考编排 CP-SAT 策略，重点说明普通老师/特殊老师划分、场次硬约束回退机制，以及 `duration` 模式下的目标阶段顺序。

相关代码入口：

- `backend/application/proctoring_service.py`
- `backend/proctoring/core/cp_sat/solver.py`
- `backend/proctoring/core/cp_sat/objectives.py`

## 1. 适用范围

本文档描述的是当前仓库默认启用的监考编排求解策略，不是历史版本，也不是试验性方案。

当前策略已经在仓库中的高一、高二真实数据上做过实跑验证，目标是：

- 保住普通老师的场次均衡下限
- 在该前提下继续做总时长均衡
- 控制求解耗时，不额外追求“本次时长”的独立词典序优化

## 2. 普通老师与特殊老师划分

当前实现不要求显式标记普通老师或特殊老师，而是由程序根据 `maxSessions` 自动识别。

规则如下：

- 先统计全体老师的 `maxSessions` 最大值
- `maxSessions == 全体最大值` 的老师，视为普通老师
- `maxSessions < 全体最大值` 的老师，视为特殊老师

这样做的业务含义是：

- 普通老师参与主场次公平指标
- 特殊老师仍然参与合法性约束与整体排班
- 但不会用来强行拉齐普通老师的场次差距

对应代码：

- `backend/application/proctoring_service.py::_classify_count_balance_teacher_indexes`

## 3. 场次硬约束回退机制

当前策略不是直接把“普通老师场次差距 <= 1”写死到底，而是采用分级尝试：

1. 先尝试普通老师 `count_range <= 1`
2. 如果不可行，再尝试普通老师 `count_range <= 2`
3. 如果仍不可行，移除这条硬约束，仅保留后续 count 目标优化

这条机制的目的有两个：

- 优先满足业务上最希望看到的普通老师场次差距 `<= 1`
- 在真实数据条件太紧时，避免直接求解失败

对应代码：

- `backend/application/proctoring_service.py::_build_count_balance_attempt_limits`
- `backend/application/proctoring_service.py::ProctoringService._run_cp_sat`

求解结果元数据中会记录本次实际采用的层级：

- `countBalanceHardLimitApplied`
- `countBalanceConstraintScope`
- `regularTeacherCount`
- `specialTeacherCount`

## 4. Count 公平指标口径

当前实现中，`count` 相关指标不再默认只按“全体老师一锅算”。

当同时存在普通老师和特殊老师时：

- 主 `count` 公平指标按普通老师集合计算
- 全体老师的 `count_deviation` 作为较后面的兜底目标

当不存在可分离的普通/特殊老师集合时：

- 退回全体老师统一口径

这样做的效果是：

- 普通老师之间的场次公平更贴近业务预期
- 特殊老师不会主导主公平指标
- 但全体老师仍保留轻量的整体平滑目标

对应代码：

- `backend/proctoring/core/cp_sat/solver.py::_build_count_fairness_metrics`

## 5. Duration 模式的当前阶段顺序

当前定版策略中，`duration` 模式只保留 `overall_duration` 的词典序优化，不再加入 `current_duration` 的独立三阶段。

当前阶段顺序如下：

1. `minimize_max_overall_duration`
2. `maximize_min_overall_duration`
3. `minimize_overall_duration_deviation`
4. `minimize_regular_count_range` 或 `minimize_count_range`
5. `minimize_regular_max_count` 或 `minimize_max_count`
6. `minimize_regular_count_deviation` 或 `minimize_count_deviation`
7. 如果存在普通/特殊老师分组，再追加全体老师口径的 `minimize_count_deviation`
8. 如果用户启用了附加偏好，再继续处理考场偏好和连续场次偏好

这里的核心取舍是：

- 先保总时长均衡
- 再保普通老师场次护栏与场次软公平
- 不再额外追求“本次监考时长”的单独词典序最优

这样做的原因是：

- 加入 `current_duration` 三阶段后，求解耗时会明显上升
- 在高二真实数据上，耗时大致从 35 秒级上升到 60 秒级
- 但总时长均衡并没有同步得到足够明显的收益

因此当前定版选择：

- 保留 `overall_duration`
- 去掉 `current_duration`

对应代码：

- `backend/proctoring/core/cp_sat/objectives.py::_build_objective_stages`

## 6. Session 模式说明

`session` 模式仍然保留“先场次、后时长”的基本思路：

1. `minimize_max_count`
2. `maximize_min_count`
3. `minimize_count_deviation`
4. `minimize_max_overall_duration`
5. `maximize_min_overall_duration`
6. `minimize_overall_duration_deviation`

如果当前求解作用域是普通老师集合，则 `count` 相关阶段名称会自动变成 `regular_*` 版本。

## 7. 真实数据验证结论

当前策略已经在项目外部的高一、高二真实数据上做过验证。

验证结论：

- 普通老师 `count_range <= 1` 可以在两套真实数据上成功落地
- 高一和高二都不需要退到 `<= 2` 或无硬约束
- 去掉 `current_duration` 三阶段后，求解耗时明显下降
- 同时保留了总时长均衡与普通老师场次护栏

因此当前版本可以视为：

- 业务目标更贴近当前使用习惯
- 求解时间更可控
- 可以作为后续维护基线

## 8. 后续维护建议

- 如果后续再次尝试“本次时长”单独优化，建议先做真实数据耗时对照
- 如果普通老师/特殊老师的业务定义变化，应优先更新 `maxSessions` 分类逻辑
- 如果新增新的公平目标，建议优先考虑是否应该是硬约束、强护栏还是普通 tie-breaker
- 修改策略后，建议至少复跑：
  - `backend/tests/test_proctoring_service.py`
  - `backend/tests/test_proctoring_exempt_slots.py`
  - `backend/tests/test_cp_sat_solver.py`
  - 高一/高二真实数据回归
