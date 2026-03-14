# 高考模式考场编排功能设计文档

**日期**: 2026-03-14
**版本**: 1.0
**状态**: 待审批

---

## 一、背景与目标

### 1.1 功能背景

中国新高考采用"3+1+2"选科模式：
- **3门必考**：语文、数学、英语
- **1门首选**：物理或历史（二选一）
- **2门再选**：化学、生物、政治、地理（四选二）

这产生了12种选科组合（2×6=12）。高考考试时间安排如下（以2025年广东为例）：

**6月7日**
- 09:00-11:30 语文
- 15:00-17:00 数学

**6月8日**
- 09:00-10:15 物理/历史（同时开考）
- 15:00-17:00 外语

**6月9日**
- 08:30-09:45 化学
- 11:00-12:15 地理
- 14:30-15:45 思想政治
- 17:00-18:15 生物学

### 1.2 业务需求

用户需要一个"高考模式"的考场编排功能，具有以下特点：

**统考科目（语数英+物理/历史）**：
- 4科考试时，考生的考场号和座位号固定不变
- 按物理/历史分组编排
- 先编排物理组（人数较多），再编排历史组
- 同一考场只能有物理学生或历史学生，不能混合

**选考科目（化学、地理、政治、生物）**：
- 每个科目有独立的考试时间段
- 考场分为两类：
  - **考试考场**：选了该科的学生参加考试
  - **自习考场**：未选该科的学生进行自习
- 考试考场和自习考场不能混合
- 考场编号顺序：先编排考试考场（1、2、3...），再编排自习考场
- 每个科目的座位号重新随机分配

### 1.3 输出要求

系统需要生成3种类型的表格：

**A. 考场安排（学生）** - 学生中心视图
- 一行对应一个学生
- 横向展开9个科目，每个科目占4列（科目状态、考场号、考场、座位号）
- 列结构：姓名、考号、班级、学号、语文科目、语文考场号、语文考场、语文座位号、数学科目、数学考场号、数学考场、数学座位号...
- 科目状态列（如"化学科目"）的值：
  - 统考科目（语数英物理）：显示科目名称（如"语文"、"物理"）
  - 选考科目：如果学生选了该科则显示科目名称（如"化学"），否则显示"自习"

**示例**：
| 姓名 | 考号 | 班级 | 学号 | 语文科目 | 语文考场号 | 语文考场 | 语文座位号 | ... | 化学科目 | 化学考场号 | 化学考场 | 化学座位号 |
|------|------|------|------|----------|-----------|---------|-----------|-----|----------|-----------|---------|-----------|
| 张三 | 001  | 1班  | 01   | 语文     | 1         | 第1考场 | 01        | ... | 化学     | 5         | 第5考场 | 12        |
| 李四 | 002  | 1班  | 02   | 语文     | 1         | 第1考场 | 02        | ... | 自习     | 15        | 第15考场| 08        |

**B. 考场安排（座位）** - 座位中心视图
- 1个sheet，包含所有科目
- 一行对应一个座位（考场号+座位号的组合）
- 列结构：考场号、考场、座位号、然后是9个科目的列组合
- 每个科目占5列：科目状态、姓名、考号、班级、学号
  - 例如化学科目的5列：化学科目、化学姓名、化学考号、化学班级、化学学号
- 科目状态列（如"化学科目"）的值：
  - 统考科目：显示科目名称（如"语文"、"物理"）
  - 选考科目：如果该座位上的学生选了该科则显示科目名称（如"化学"），否则显示"自习"

**示例**：
| 考场号 | 考场 | 座位号 | 语文科目 | 语文姓名 | 语文考号 | 语文班级 | 语文学号 | ... | 化学科目 | 化学姓名 | 化学考号 | 化学班级 | 化学学号 |
|--------|------|--------|----------|----------|----------|----------|----------|-----|----------|----------|----------|----------|----------|
| 1      | 第1考场 | 01  | 语文     | 张三     | 001      | 1班      | 01       | ... | 化学     | 王五     | 003      | 2班      | 05       |
| 1      | 第1考场 | 02  | 语文     | 李四     | 002      | 1班      | 02       | ... | 自习     | 赵六     | 004      | 2班      | 06       |

**C. 各科考试时间编排结果表** - 时间段视图
- 5个独立的sheet：
  - Sheet 1: 统考编排结果（语数英+物理/历史）- 包含所有学生
  - Sheet 2-5: 化学编排结果、地理编排结果、政治编排结果、生物编排结果
- 每个选考sheet包含所有学生
- 列"科目"显示：参加考试的学生显示科目名（如"化学"），自习的学生显示"自习"
- 列结构：考场号、考场、座位号、考号、姓名、班级、学号、科目

---

## 二、数据结构设计

### 2.1 内部数据结构

在 `ExamArrangement` 类中，高考模式需要维护9个科目的独立编排结果：

```python
self.gaokao_results = {
    'unified': {  # 统考：语数英 + 物理/历史
        'subjects': ['语文', '数学', '英语', '物理/历史'],
        'arrangement': pd.DataFrame  # 包含所有学生的统考编排结果
    },
    'electives': {  # 选考：化学、地理、政治、生物
        '化学': pd.DataFrame,
        '地理': pd.DataFrame,
        '政治': pd.DataFrame,
        '生物': pd.DataFrame
    }
}
```

### 2.2 学生记录结构

每个学生的最终记录包含9个科目的考场信息（每个科目4列）：

```python
{
    # 基本信息
    '班级': '1',
    '学号': '01',
    '考号': '240001',
    '姓名': '张三',
    '选科': '物化生',

    # 统考科目（考场号和座位号相同，科目状态为科目名）
    '语文科目': '语文', '语文考场号': '001', '语文考场': '第1考场', '语文座位号': '01',
    '数学科目': '数学', '数学考场号': '001', '数学考场': '第1考场', '数学座位号': '01',
    '英语科目': '英语', '英语考场号': '001', '英语考场': '第1考场', '英语座位号': '01',
    '物理科目': '物理', '物理考场号': '001', '物理考场': '第1考场', '物理座位号': '01',

    # 选考科目（考场号和座位号独立，科目状态为科目名或"自习"）
    '化学科目': '化学', '化学考场号': '005', '化学考场': '第5考场', '化学座位号': '12',
    '地理科目': '自习', '地理考场号': '015', '地理考场': '第15考场', '地理座位号': '08',
    '政治科目': '自习', '政治考场号': '020', '政治考场': '第20考场', '政治座位号': '15',
    '生物科目': '生物', '生物考场号': '010', '生物考场': '第10考场', '生物座位号': '05',
}
```

### 2.3 座位记录结构

座位中心视图中，每个座位包含9个科目的学生信息（每个科目5列）：

```python
{
    # 座位基本信息
    '考场号': '001',
    '考场': '第1考场',
    '座位号': '01',

    # 语文科目（统考）
    '语文科目': '语文',
    '语文姓名': '张三',
    '语文考号': '240001',
    '语文班级': '1',
    '语文学号': '01',

    # 数学科目（统考）
    '数学科目': '数学',
    '数学姓名': '张三',
    '数学考号': '240001',
    '数学班级': '1',
    '数学学号': '01',

    # ... 其他统考科目 ...

    # 化学科目（选考）
    '化学科目': '化学',  # 或 "自习"
    '化学姓名': '王五',
    '化学考号': '240003',
    '化学班级': '2',
    '化学学号': '05',

    # ... 其他选考科目 ...
}
```

---

## 三、核心算法设计

### 3.1 统考科目编排算法

**输入**：
- 学生名单（包含选科信息）
- 考场列表（考场号、考场名称、容量）

**步骤**：

1. **按物理/历史分组**
```python
physics_students = students[students['选科'].str.startswith('物')]
history_students = students[students['选科'].str.startswith('史')]
```

2. **随机打乱物理组学生**
```python
import secrets
random_state = secrets.randbelow(2**32)
physics_students = physics_students.sample(frac=1, random_state=random_state)
```

3. **编排物理组学生**
- 从考场1开始依次填充
- 每个考场填满后进入下一个考场
- 记录最后使用的考场编号 `last_physics_room`

4. **随机打乱历史组学生**

5. **编排历史组学生**
- 从考场 `last_physics_room + 1` 开始填充
- 依次填充后续考场

6. **为每个学生分配座位号**
- 座位号从01开始，按填充顺序递增

7. **复制到4个科目**
- 将考场号、考场名称、座位号复制到语文、数学、英语、物理/历史4个科目

**输出**：
- 统考编排结果 DataFrame，包含所有学生及其4科的考场信息

### 3.2 选考科目编排算法

对每个选考科目（化学、地理、政治、生物）独立执行以下步骤：

**输入**：
- 学生名单
- 当前科目名称（如"化学"）
- 考场列表

**步骤**：

1. **分离考试学生和自习学生**
```python
# 以化学为例
exam_students = students[students['选科'].str.contains('化')]
self_study_students = students[~students['选科'].str.contains('化')]
```

2. **随机打乱考试学生**

3. **编排考试学生到考试考场**
- 从考场1开始依次填充
- 记录最后使用的考场编号 `last_exam_room`
- 标记科目类型为"考试"或科目名称（如"化学"）

4. **随机打乱自习学生**

5. **编排自习学生到自习考场**
- 从考场 `last_exam_room + 1` 开始填充
- 标记科目类型为"自习"

6. **为每个学生分配座位号**
- 座位号从01开始，按填充顺序递增

**输出**：
- 该科目的编排结果 DataFrame，包含所有学生及其考场信息和科目类型

### 3.3 结果合并算法

将统考和选考的编排结果合并为学生中心视图：

**步骤**：

1. **以学生为主键**
- 使用考号作为唯一标识

2. **合并统考结果**
- 添加语文、数学、英语、物理/历史的考场号、考场、座位号列

3. **合并选考结果**
- 依次添加化学、地理、政治、生物的考场号、考场、座位号列

4. **生成最终DataFrame**
- 列顺序：基本信息 + 9个科目 × 3列

**输出**：
- 学生中心视图 DataFrame（用于表格A）

---

## 四、代码架构设计

### 4.1 核心方法结构

在 `backend/examroom/core/arrangement.py` 的 `ExamArrangement` 类中添加以下方法：

```python
def arrange_gaokao_mode(self):
    """高考模式编排：统考(语数英+物/历史) + 选考(化地政生)"""
    # 1. 编排统考科目
    unified_result = self._arrange_unified_exams()

    # 2. 编排选考科目
    elective_results = {}
    for subject in ['化学', '地理', '政治', '生物']:
        elective_results[subject] = self._arrange_elective_exam(subject)

    # 3. 保存结果
    self.gaokao_results = {
        'unified': unified_result,
        'electives': elective_results
    }

    # 4. 合并为学生中心视图
    self.arranged_students = self._merge_gaokao_results()

    return True, f"高考模式编排完成，共编排{len(self.students)}名学生"

def _arrange_unified_exams(self):
    """编排统考科目（语数英+物理/历史）"""
    # 按物理/历史分组
    # 先编排物理组，再编排历史组
    # 同一考场只能有一个组
    # 返回包含考场和座位分配的DataFrame
    pass

def _arrange_elective_exam(self, subject: str):
    """编排单个选考科目"""
    # 分离考试学生和自习学生
    # 先编排考试学生（考场1, 2, 3...）
    # 再编排自习学生（考场N+1, N+2...）
    # 返回包含考场、座位和科目类型的DataFrame
    pass

def _merge_gaokao_results(self):
    """合并所有科目的编排结果为学生中心视图"""
    # 创建一行一个学生的DataFrame
    # 添加列：[科目考场号, 科目考场, 科目座位号] × 9个科目
    # 返回最终DataFrame
    pass
```

### 4.2 导出方法结构

添加3种表格的导出方法：

```python
def save_gaokao_results(self, output_file="高考编排结果.xlsx"):
    """保存高考模式编排结果（3种表格）"""
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # 表格A: 学生中心视图（1个sheet）
        self._export_gaokao_student_table(writer)

        # 表格B: 座位中心视图（1个sheet）
        self._export_gaokao_seat_tables(writer)

        # 表格C: 时间段视图（5个sheet）
        self._export_gaokao_timeslot_tables(writer)

    return True, f"高考编排结果已保存至 {output_file}"

def _export_gaokao_student_table(self, writer):
    """导出考场安排（学生）表"""
    # 横向布局：姓名, 考号, 班级, 学号,
    # 语文科目, 语文考场号, 语文考场, 语文座位号,
    # 数学科目, 数学考场号, 数学考场, 数学座位号, ...
    # 每个科目4列，共9个科目36列
    # Sheet名称：考场安排（学生）
    pass

def _export_gaokao_seat_tables(self, writer):
    """导出考场安排（座位）表 - 1个sheet包含所有科目"""
    # 列结构：考场号, 考场, 座位号,
    # 语文科目, 语文姓名, 语文考号, 语文班级, 语文学号,
    # 数学科目, 数学姓名, 数学考号, 数学班级, 数学学号, ...
    # 每个科目5列，共9个科目45列
    # Sheet名称：考场安排（座位）
    pass

def _export_gaokao_timeslot_tables(self, writer):
    """导出各科考试时间编排结果表 - 5个sheet"""
    # Sheet 1: 统考编排结果（所有学生）
    # Sheet 2-5: 化学/地理/政治/生物编排结果（所有学生，带科目列）
    pass
```

### 4.3 辅助工具函数

添加可复用的工具函数：

```python
def _shuffle_students(self, students_df):
    """使用安全随机数打乱学生顺序"""
    import secrets
    random_state = secrets.randbelow(2**32)
    return students_df.sample(frac=1, random_state=random_state).reset_index(drop=True)

def _fill_rooms_sequential(self, students_list, start_room_num):
    """将学生顺序填充到考场，返回考场分配结果"""
    rooms = []
    current_room_num = start_room_num
    current_room_students = []

    for idx, student in students_list.iterrows():
        room_capacity = self.get_room_capacity(str(current_room_num))

        if len(current_room_students) >= room_capacity:
            # 当前考场已满，进入下一个考场
            rooms.append({
                'room_num': str(current_room_num),
                'students': current_room_students
            })
            current_room_num += 1
            current_room_students = []

        current_room_students.append(student)

    # 添加最后一个考场
    if current_room_students:
        rooms.append({
            'room_num': str(current_room_num),
            'students': current_room_students
        })

    return rooms, current_room_num

def _extract_subject_from_combination(self, combination_str, subject_abbr):
    """从选科组合中提取是否包含某科目"""
    # 例如：combination_str="物化生", subject_abbr="化" -> True
    return subject_abbr in str(combination_str)
```

---

## 五、RPC接口集成

### 5.1 更新模式映射

在 `backend/application/rooms_service.py` 的 `_build_exam_arrangement` 方法中：

```python
def _build_exam_arrangement(settings: list, config: dict, student_path: str) -> ExamArrangement:
    # 更新模式映射
    mode_map = {
        "3+1+2": "subject_mode",
        "normal": "normal_mode",
        "random": "random_mode",
        "gaokao": "gaokao_mode"  # 新增
    }
    mode = mode_map.get(config.get("mode", "normal"), "normal_mode")

    # ... 其余代码保持不变
```

### 5.2 更新编排路由

在 `backend/examroom/core/arrangement.py` 的 `arrange_exam_rooms` 方法中：

```python
def arrange_exam_rooms(self):
    """编排考场（支持四种模式）"""
    if self.arrangement_mode == "normal_mode":
        return self.arrange_normal_mode()
    elif self.arrangement_mode == "random_mode":
        return self.arrange_random_mode()
    elif self.arrangement_mode == "gaokao_mode":  # 新增
        return self.arrange_gaokao_mode()
    else:
        return self.arrange_subject_mode()
```

### 5.3 更新导出方法

在 `backend/application/rooms_service.py` 的 `export` 方法中：

```python
def export(self, params: dict) -> Any:
    # ... 现有代码 ...

    # 检查是否为高考模式
    if ea.arrangement_mode == "gaokao_mode":
        success, msg = ea.save_gaokao_results(path)
    else:
        success, msg = ea.save_results(path)

    return {} if success else {"error": msg}
```

---

## 六、前端界面调整

### 6.1 添加高考模式选项

在 `frontend/src/views/RoomsPage/RoomsSidebar.vue` 中添加模式选项：

```vue
<el-select v-model="config.mode" placeholder="选择编排模式">
  <el-option label="3+1+2选科编排" value="3+1+2" />
  <el-option label="顺序编排" value="normal" />
  <el-option label="随机编排" value="random" />
  <el-option label="高考模式" value="gaokao" />  <!-- 新增 -->
</el-select>
```

### 6.2 结果展示适配

在 `frontend/src/views/RoomsPage/RoomsContent.vue` 中：

- 检测编排模式
- 如果是高考模式，展示9个科目的列（语文考场号、语文考场、语文座位号...）
- 如果是其他模式，展示现有的列结构

**注意**：由于高考模式的列数较多（27列），建议：
- 使用横向滚动
- 或者提供"按科目筛选"功能
- 或者只显示关键信息，详细信息通过导出Excel查看

---

## 七、可复用组件

### 7.1 复用现有代码

以下现有功能可以直接复用：

**考场初始化** (`_initialize_rooms`):
- 复用考场结构创建逻辑
- 需要修改以支持独立的考场池

**考场容量逻辑** (`get_room_capacity`):
- 直接复用，无需修改

**考场名称映射** (`_apply_room_names`):
- 复用考场号到考场名称的映射逻辑

**选科解析** (`parse_subject_combination`):
- 复用选科字符串解析逻辑
- 提取首选科目（物理/历史）
- 提取再选科目（化生政地）

**Excel导出基础** (`save_results`):
- 参考现有的Excel导出模式
- 使用 `openpyxl` 引擎
- 使用 `pd.ExcelWriter` 管理多sheet

### 7.2 需要新增的组件

**学生打乱函数** (`_shuffle_students`):
- 使用 `secrets` 模块生成安全随机数
- 确保编排的公平性

**顺序填充函数** (`_fill_rooms_sequential`):
- 将学生列表按顺序填充到考场
- 处理考场容量限制
- 返回考场分配结果

**科目检测函数** (`_extract_subject_from_combination`):
- 从选科组合字符串中检测是否包含某科目
- 支持缩写（物化生）和全称（物理+化学+生物）

---

## 八、实施步骤

### 阶段1：后端核心算法（2-3天）

1. **实现统考编排逻辑**
   - 添加 `_arrange_unified_exams()` 方法
   - 实现物理/历史分组逻辑
   - 实现顺序填充逻辑
   - 测试：验证物理组在前、历史组在后，同一考场不混合

2. **实现选考编排逻辑**
   - 添加 `_arrange_elective_exam()` 方法
   - 实现考试/自习学生分离逻辑
   - 实现考试考场在前、自习考场在后的逻辑
   - 测试：验证考试和自习考场不混合

3. **实现结果合并逻辑**
   - 添加 `_merge_gaokao_results()` 方法
   - 将9个科目的编排结果合并为学生中心视图
   - 测试：验证每个学生有9个科目的完整信息

4. **实现主编排方法**
   - 添加 `arrange_gaokao_mode()` 方法
   - 整合统考、选考、合并三个步骤
   - 测试：端到端测试完整编排流程

### 阶段2：后端导出逻辑（1-2天）

5. **实现学生表导出**
   - 添加 `_export_gaokao_student_table()` 方法
   - 生成横向展开的学生中心表（每个科目4列：科目状态、考场号、考场、座位号）
   - 测试：验证列结构和数据完整性

6. **实现座位表导出**
   - 添加 `_export_gaokao_seat_tables()` 方法
   - 生成1个包含所有科目的座位表sheet（每个科目5列：科目状态、姓名、考号、班级、学号）
   - 测试：验证每个座位在不同科目下的学生信息正确性

7. **实现时间段表导出**
   - 添加 `_export_gaokao_timeslot_tables()` 方法
   - 生成5个时间段表sheet
   - 测试：验证科目列的正确性（考试/自习）

8. **实现主导出方法**
   - 添加 `save_gaokao_results()` 方法
   - 整合3种表格的导出
   - 测试：验证生成的Excel文件包含所有sheet

### 阶段3：后端集成（0.5天）

9. **更新编排路由**
   - 修改 `arrange_exam_rooms()` 方法
   - 添加高考模式的路由分支

10. **更新模式映射**
    - 修改 `_build_exam_arrangement()` 方法
    - 添加 "gaokao" 到 "gaokao_mode" 的映射

11. **更新导出路由**
    - 修改 `export()` 方法
    - 根据模式选择不同的导出方法

### 阶段4：前端集成（0.5天）

12. **添加模式选项**
    - 修改 `RoomsSidebar.vue`
    - 添加"高考模式"选项到下拉菜单

13. **更新结果展示**
    - 修改 `RoomsContent.vue`
    - 适配高考模式的列结构（可选，建议通过Excel查看详细结果）

### 阶段5：测试与验证（1天）

14. **单元测试**
    - 测试统考编排（纯物理、纯历史、混合）
    - 测试选考编排（全考试、全自习、混合）
    - 测试结果合并

15. **集成测试**
    - 测试完整流程：导入学生 → 编排 → 导出
    - 验证3种表格的数据一致性

16. **边界测试**
    - 测试考场不足的情况
    - 测试单个学生的情况
    - 测试所有学生选同一组合的情况

---

## 九、关键文件清单

### 需要修改的文件

1. **backend/examroom/core/arrangement.py** (核心文件)
   - 添加 `arrange_gaokao_mode()` 方法
   - 添加 `_arrange_unified_exams()` 方法
   - 添加 `_arrange_elective_exam()` 方法
   - 添加 `_merge_gaokao_results()` 方法
   - 添加 `save_gaokao_results()` 方法
   - 添加 `_export_gaokao_student_table()` 方法
   - 添加 `_export_gaokao_seat_tables()` 方法
   - 添加 `_export_gaokao_timeslot_tables()` 方法
   - 添加辅助工具函数
   - 修改 `arrange_exam_rooms()` 方法

2. **backend/application/rooms_service.py**
   - 修改 `_build_exam_arrangement()` 方法（更新模式映射）
   - 修改 `export()` 方法（添加高考模式分支）

3. **frontend/src/views/RoomsPage/RoomsSidebar.vue**
   - 添加"高考模式"选项到模式选择下拉菜单

4. **frontend/src/views/RoomsPage/RoomsContent.vue** (可选)
   - 适配高考模式的结果展示

### 参考文件

- **backend/examroom/core/stats_sheet.py** - Excel导出模式参考
- **backend/examroom/core/arrangement.py** 中的 `arrange_subject_mode()` - 选科编排逻辑参考

---

## 十、验证方案

### 10.1 功能验证

**统考编排验证**：
- [ ] 物理组学生在前，历史组学生在后
- [ ] 同一考场只有物理或历史学生
- [ ] 语数英物/历史4科的考场号和座位号相同
- [ ] 座位号从01开始连续编号

**选考编排验证**：
- [ ] 考试考场在前，自习考场在后
- [ ] 同一考场不混合考试和自习学生
- [ ] 每个科目的座位号独立分配
- [ ] 科目类型标记正确（考试/自习）

**表格导出验证**：
- [ ] 学生表：一行一个学生，40列（基本信息4列 + 9科目×4列）
- [ ] 学生表：科目状态列正确显示科目名或"自习"
- [ ] 座位表：1个sheet，包含所有座位和所有科目
- [ ] 座位表：48列（座位信息3列 + 9科目×5列）
- [ ] 座位表：每个座位在不同科目下可能有不同的学生
- [ ] 时间段表：5个sheet，统考1个+选考4个

### 10.2 边界情况测试

- [ ] 考场数量不足时返回错误提示
- [ ] 单个学生能正常编排
- [ ] 所有学生选同一组合能正常编排
- [ ] 自定义考场容量能正确应用
- [ ] 考场名称映射能正确应用

### 10.3 性能测试

- [ ] 1000名学生编排时间 < 5秒
- [ ] 导出Excel时间 < 10秒
- [ ] 内存使用合理（< 500MB）

---

## 十一、潜在风险与应对

### 风险1：考场数量不足

**问题**：学生人数过多，考场不够用
**应对**：
- 在编排前计算所需考场数量
- 如果不足，返回明确的错误信息
- 提示用户需要增加考场或减少每考场人数

### 风险2：Excel列数过多

**问题**：
- 学生表有40列（基本信息4列 + 9科目×4列）
- 座位表有48列（座位信息3列 + 9科目×5列）
- 可能导致Excel显示不便

**应对**：
- 使用冻结首列功能，固定基本信息列
- 提供列宽自动调整
- 为每个科目的列组添加背景色区分
- 建议用户主要通过时间段表查看单个科目的详细信息

### 风险3：选科数据不规范

**问题**：学生选科字段格式不统一
**应对**：
- 复用现有的选科验证逻辑
- 在编排前进行数据校验
- 返回明确的错误提示

### 风险4：内存占用

**问题**：大规模学生数据可能占用大量内存
**应对**：
- 使用pandas的高效操作
- 避免不必要的数据复制
- 及时释放中间结果

---

## 十二、后续优化方向

完成基本功能后，可以考虑以下优化：

1. **前端结果预览优化**
   - 添加"按科目查看"的标签页
   - 每个标签页显示一个科目的编排结果
   - 提供更友好的数据浏览体验

2. **导出格式优化**
   - 添加Excel样式（表头加粗、边框、颜色）
   - 添加冻结窗格
   - 添加自动筛选功能

3. **编排策略优化**
   - 支持按班级聚集编排（同班学生尽量在同一考场）
   - 支持按学号顺序编排（便于查找）
   - 支持自定义编排优先级

4. **统计功能**
   - 生成考场使用统计表
   - 生成选科组合分布统计
   - 生成监考需求统计

---

**文档版本**: 1.0
**最后更新**: 2026-03-14

