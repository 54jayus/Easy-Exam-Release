# ExamFlow 智能考务系统 - 架构重构设计文档

**日期**: 2026-03-01
**策略**: 渐进式重构，三阶段实施
**时间预算**: 10-13 天
**风险等级**: 中低（每阶段完成后系统可运行）

---

## 一、背景与目标

### 1.1 当前问题

基于 2026-03-01 的代码评审，发现以下关键问题：

**🔴 严重问题（5个）**
1. 后端 RPC 调度过度集中化 - `build_dispatch()` 单函数管理所有路由
2. 前端 RPC 客户端缺乏类型安全 - 方法名是字符串，易出错
3. 缺少单元测试基础设施 - 无任何测试文件
4. 超长函数 - `arrange_subject_mode()` 163 行，圈复杂度过高
5. 前端内存泄漏风险 - `pending` Map 超时后未清理

**🟡 中等问题（6个）**
6. 状态持久化策略不清晰 - 路径逻辑复杂，无版本管理
7. 领域模型与 DTO 混淆 - `AppState` 使用 `Any` 类型
8. 循环依赖风险 - SubjectsService 通过函数内导入操作 ProctoringState
9. 代码重复 - 房间号规范化逻辑重复
10. 异常处理过于宽泛 - 可能掩盖错误或泄露信息
11. 大数据集性能问题 - DataFrame 转换时机不当

### 1.2 重构目标

- **稳定性**: 修复内存泄漏、类型安全等严重问题
- **可维护性**: 拆分超长函数，消除代码重复
- **可测试性**: 建立测试基础设施，引入接口抽象
- **架构清晰**: 分层明确，依赖关系清晰
- **渐进式**: 每个阶段完成后系统都能正常运行

---

## 二、目标架构

### 2.1 后端架构

```
backend/
├── domain/                        # 领域层：纯业务逻辑
│   ├── models/                    # 领域模型
│   │   ├── teacher.py
│   │   ├── exam.py
│   │   ├── room.py
│   │   └── subject.py
│   ├── value_objects/             # 值对象
│   │   └── room_number.py
│   ├── events.py                  # 领域事件
│   ├── errors.py                  # 领域异常
│   └── state.py                   # 应用状态
│
├── dto/                           # 数据传输对象
│   ├── proctoring.py
│   ├── rooms.py
│   └── subjects.py
│
├── application/                   # 应用层：用例编排
│   ├── subjects_service.py
│   ├── proctoring_service.py
│   ├── rooms_service.py
│   ├── printing_service.py
│   ├── assistant_service.py
│   ├── licensing_service.py
│   ├── system_service.py
│   └── dashboard_service.py
│
├── repository/                    # 仓储层：数据访问
│   ├── interfaces.py              # 仓储接口
│   ├── state_repository.py        # 文件持久化实现
│   ├── in_memory_repository.py    # 内存实现（测试用）
│   └── excel_repository.py
│
├── infrastructure/                # 基础设施
│   ├── event_bus.py               # 事件总线
│   └── logging_config.py
│
├── rpc/                           # RPC 层
│   └── dispatcher.py              # RPC 调度器
│
├── rpc_server.py                  # RPC 服务器入口（<100行）
└── __main__.py
```

### 2.2 前端架构

```
frontend/src/
├── types/
│   └── rpc.ts                     # RPC 方法类型定义
├── lib/
│   └── pythonBackend.ts           # 类型安全的 RPC 客户端
├── stores/
│   ├── license.ts
│   └── app.ts
└── views/                         # UI 组件
```

### 2.3 测试架构

```
backend/tests/
├── domain/
│   ├── test_exam_arrangement.py
│   ├── test_proctoring_scheduler.py
│   └── test_subject_validator.py
├── application/
│   ├── test_subjects_service.py
│   └── test_proctoring_service.py
└── conftest.py                    # pytest 配置
```

---

## 三、数据流设计

```
前端 Vue 组件
  ↓ 调用
pythonBackend.request<Method>(method, params)  [类型安全]
  ↓ JSON-RPC over stdin
rpc_server.py
  ↓ 路由分发
RpcDispatcher.dispatch(method, params)
  ↓ 调用
Application Service (用例编排)
  ↓ 调用
Domain Service (业务逻辑) + Repository (数据访问)
  ↓ 读写
AppState (内存状态) ↔ state.json (持久化)
  ↓ 返回
JSON-RPC response
  ↓ 类型推断
前端获得类型安全的结果
```

### 3.1 层间职责

| 层 | 职责 | 依赖 | 可测试性 |
|---|---|---|---|
| Domain | 纯业务逻辑，无 I/O | 无外部依赖 | 纯单元测试 |
| Application | 用例编排，协调 Domain + Repository | Domain + Repository 接口 | Mock Repository |
| Repository | 数据访问，封装 I/O | 文件系统、pandas | 集成测试 |
| RPC | 路由分发，参数解包 | Application | 端到端测试 |

### 3.2 依赖注入示例

```python
# 构建依赖图
state = AppState()
repo = FileStateRepository(state_file_path)
repo.load(state)

event_bus = EventBus()

# 创建 Services（依赖接口）
subjects_svc = SubjectsService(state, repo, event_bus)
proctoring_svc = ProctoringService(state, repo)

# 订阅事件
event_bus.subscribe(SubjectsUpdatedEvent, proctoring_svc.on_subjects_updated)

# 注册 RPC 路由
dispatcher = RpcDispatcher()
dispatcher.register("subjects.list", subjects_svc.list)
dispatcher.register("subjects.update", subjects_svc.update)
# ...
```

---

## 四、渐进式重构计划

### 第一阶段：关键问题修复（3-4天）

**目标**: 修复最严重的稳定性和安全问题，不改变整体架构。

#### 任务 1.1：修复前端 RPC 客户端内存泄漏

**文件**: `frontend/src/lib/pythonBackend.ts`

**问题**:
- `pending` Map 在超时后没有删除条目
- 正常响应时没有清理 timeout
- `stop()` 方法没有清理 `logListeners`

**方案**:
```typescript
async request<T>(...): Promise<T> {
  const timeoutId = setTimeout(() => {
    this.pending.delete(id)  // 关键：清理 Map
    reject(new Error("后端请求超时"))
  }, timeoutMs)

  // 保存 timeoutId 以便清理
  this.pending.set(id, { resolve, reject, timeoutId })
}

private onLine(line: string): void {
  const pending = this.pending.get(String(id))
  if (pending.timeoutId) {
    clearTimeout(pending.timeoutId)  // 清理 timeout
  }
  this.pending.delete(String(id))
  // ...
}

async stop(): Promise<void> {
  this.logListeners = []  // 清理监听器
  // ...
}
```

#### 任务 1.2：引入前端 RPC 类型安全

**新增文件**: `frontend/src/types/rpc.ts`

**方案**:
```typescript
// 定义所有 RPC 方法签名
export type RpcMethods = {
  "subjects.list": {
    params: {}
    result: { subjects: Subject[] }
  }
  "subjects.update": {
    params: { subjects: Subject[] }
    result: { proctoringReset: boolean }
  }
  "proctoring.generateSchedule": {
    params: { config: ScheduleConfig }
    result: { schedule: Schedule }
  }
  // ... 其他方法
}

// 类型安全的 request 方法
async request<M extends keyof RpcMethods>(
  method: M,
  params: RpcMethods[M]["params"],
  timeoutMs = 120_000
): Promise<RpcMethods[M]["result"]>
```

**修改文件**: `frontend/src/lib/pythonBackend.ts`

#### 任务 1.3：拆分超长函数

**文件**: `backend/examroom/core/arrangement.py`

**方案**: 将 `arrange_subject_mode()` (163行) 拆分为：
- `_initialize_rooms()` - 初始化考场列表
- `_group_and_sort_subjects()` - 按物理/历史分组排序
- `_assign_large_groups()` - 分配大组学生
- `_assign_remaining_students()` - 分配剩余学生
- `_generate_results()` - 生成最终结果

每个方法不超过 30 行，职责单一。

#### 任务 1.4：统一错误处理机制

**新增文件**: `backend/domain/errors.py`

```python
from enum import Enum

class ErrorCode(Enum):
    # 业务错误 (1000-1999)
    VALIDATION_ERROR = 1001
    RESOURCE_NOT_FOUND = 1002
    DUPLICATE_RESOURCE = 1003

    # 系统错误 (2000-2999)
    FILE_IO_ERROR = 2001
    DATABASE_ERROR = 2002

class DomainError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self):
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details
        }
```

**修改文件**: `backend/rpc_server.py`

```python
except DomainError as e:
    reply = {"ok": False, "error": e.to_dict()}
except ValueError as e:
    reply = {"ok": False, "error": {
        "code": 1001,
        "message": f"参数错误: {str(e)}"
    }}
except Exception as e:
    logger.exception("Unexpected error")
    reply = {"ok": False, "error": {
        "code": 9999,
        "message": "系统内部错误"
    }}
```

**验证**: 运行 `npm run dev`，测试所有功能正常。

---

### 第二阶段：架构优化（4-5天）

**目标**: 改善架构，引入分层和接口抽象，保持渐进式迁移。

#### 任务 2.1：建立 Repository 接口抽象

**新增文件**: `backend/repository/interfaces.py`

```python
from abc import ABC, abstractmethod
from backend.domain.state import AppState

class IStateRepository(ABC):
    @abstractmethod
    def save(self, state: AppState) -> None:
        """保存应用状态"""
        pass

    @abstractmethod
    def load(self, state: AppState) -> None:
        """加载应用状态"""
        pass
```

**新增文件**: `backend/repository/in_memory_repository.py`

```python
from dataclasses import asdict
from backend.repository.interfaces import IStateRepository

class InMemoryStateRepository(IStateRepository):
    def __init__(self):
        self._data = None

    def save(self, state: AppState) -> None:
        self._data = asdict(state)

    def load(self, state: AppState) -> None:
        if self._data:
            # 从内存加载
            pass
```

**修改**: 所有 Service 类的构造函数，依赖 `IStateRepository` 而非具体实现。

#### 任务 2.2：引入领域模型和 DTO 分离

**新增目录**: `backend/domain/models/`

创建纯领域模型：
- `teacher.py` - Teacher 类（业务逻辑方法）
- `exam.py` - Exam 类
- `room.py` - Room 类
- `subject.py` - Subject 类

**新增目录**: `backend/dto/`

创建数据传输对象：
- `proctoring.py` - TeacherDto, ScheduleDto
- `rooms.py` - RoomDto
- `subjects.py` - SubjectDto

每个 DTO 提供 `from_domain()` 和 `to_domain()` 方法。

**修改**: `backend/domain/state.py`，移除 `Any` 类型：

```python
@dataclass
class ProctoringState:
    teachers: list[dict] = field(default_factory=list)
    schedule: list[dict] = field(default_factory=list)  # 不再是 Any
    config: dict = field(default_factory=dict)
```

#### 任务 2.3：重构 RPC 调度机制

**新增文件**: `backend/rpc/dispatcher.py`

```python
from typing import Callable, Any

class RpcDispatcher:
    def __init__(self):
        self._handlers: dict[str, Callable[[dict], Any]] = {}

    def register(self, method: str, handler: Callable[[dict], Any]):
        self._handlers[method] = handler

    def dispatch(self, method: str, params: dict) -> Any:
        if method not in self._handlers:
            raise ValueError(f"Unknown method: {method}")
        return self._handlers[method](params)
```

**修改**: `backend/rpc_server.py`

```python
def build_dispatcher() -> RpcDispatcher:
    # 构建依赖
    state = AppState()
    repo = FileStateRepository(_get_state_file())
    repo.load(state)

    # 创建 Services
    subjects_svc = SubjectsService(state, repo)
    proctoring_svc = ProctoringService(state, repo)
    # ...

    # 注册路由
    dispatcher = RpcDispatcher()
    dispatcher.register("subjects.list", subjects_svc.list)
    dispatcher.register("subjects.update", subjects_svc.update)
    # ...

    return dispatcher

def main():
    dispatcher = build_dispatcher()

    while True:
        # 读取请求
        req = json.loads(line)

        # 调度
        result = dispatcher.dispatch(req["method"], req.get("params", {}))
        # ...
```

#### 任务 2.4：改进状态持久化策略

**修改**: `backend/repository/state_repository.py`

```python
from pathlib import Path
import shutil
from datetime import datetime

class FileStateRepository(IStateRepository):
    VERSION = "1.0.0"

    def __init__(self, base_path: Path):
        self.state_file = base_path / "state.json"
        self.backup_dir = base_path / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: AppState) -> None:
        # 创建备份
        if self.state_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.backup_dir / f"state_{timestamp}.json"
            shutil.copy2(self.state_file, backup)

            # 只保留最近 10 个备份
            backups = sorted(self.backup_dir.glob("state_*.json"))
            for old in backups[:-10]:
                old.unlink()

        # 保存新状态（带版本号）
        data = {
            "version": self.VERSION,
            "state": asdict(state)
        }
        self.state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load(self, state: AppState) -> None:
        if not self.state_file.exists():
            return

        data = json.loads(self.state_file.read_text())
        version = data.get("version", "0.0.0")

        # 版本迁移
        if version != self.VERSION:
            data = self._migrate(data, version)

        # 加载状态
        # ...
```

**简化路径逻辑**: 使用单一环境变量 `EXAMFLOW_DATA_DIR`

**验证**: 运行系统，检查状态保存和备份功能。

---

### 第三阶段：测试体系和代码质量（3-4天）

**目标**: 建立完整的测试基础设施，修复剩余代码质量问题。

#### 任务 3.1：建立单元测试基础设施

**新增文件**: `backend/pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**新增文件**: `backend/conftest.py`

```python
import pytest
from backend.domain.state import AppState
from backend.repository.in_memory_repository import InMemoryStateRepository

@pytest.fixture
def app_state():
    return AppState()

@pytest.fixture
def in_memory_repo():
    return InMemoryStateRepository()
```

**新增测试文件**:

1. `backend/tests/domain/test_exam_arrangement.py`
   - 测试三种编排模式（顺序、随机、选科）
   - 测试边界情况（考场不足、学生为空）

2. `backend/tests/domain/test_proctoring_scheduler.py`
   - 测试监考分配算法
   - 测试 swap 和 rebalance 功能

3. `backend/tests/domain/test_subject_validator.py`
   - 测试科目验证逻辑
   - 测试各种输入格式

4. `backend/tests/application/test_subjects_service.py`
   - 测试 Service 层（使用 InMemoryRepository）

**运行测试**: `cd backend && pytest -v`

#### 任务 3.2：消除循环依赖

**新增文件**: `backend/domain/events.py`

```python
from dataclasses import dataclass

@dataclass
class SubjectsUpdatedEvent:
    subjects: list[dict]
```

**新增文件**: `backend/infrastructure/event_bus.py`

```python
from typing import Any, Callable

class EventBus:
    def __init__(self):
        self._handlers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Any):
        for handler in self._handlers.get(type(event), []):
            handler(event)
```

**修改**: `backend/application/subjects_service.py`

```python
class SubjectsService:
    def __init__(self, state: AppState, repo: IStateRepository, event_bus: EventBus):
        self._state = state
        self._repo = repo
        self._event_bus = event_bus

    def update(self, params: dict) -> Any:
        self._state.subjects = params.get("subjects", [])
        self._repo.save(self._state)

        # 发布事件
        self._event_bus.publish(SubjectsUpdatedEvent(subjects=self._state.subjects))
        return {}
```

**修改**: `backend/application/proctoring_service.py`

```python
class ProctoringService:
    def on_subjects_updated(self, event: SubjectsUpdatedEvent):
        if self._state.proctoring.schedule:
            self._state.proctoring = ProctoringState()
            self._repo.save(self._state)
```

#### 任务 3.3：消除代码重复

**新增文件**: `backend/domain/value_objects/room_number.py`

```python
class RoomNumber:
    """房间号值对象，封装所有房间号处理逻辑"""

    @staticmethod
    def normalize(room_num: Any) -> str:
        s = str(room_num).strip()
        if s.lower() == "nan":
            return ""
        return s

    @staticmethod
    def strip_leading_zeros(room_num: str) -> str:
        if not room_num or not room_num.isdigit():
            return room_num
        return room_num.lstrip("0") or "0"

    @staticmethod
    def lookup(room_num: Any, mapping: dict) -> str | None:
        key = RoomNumber.normalize(room_num)

        # 直接匹配
        if key in mapping:
            return mapping[key]

        # 去除前导零后匹配
        stripped = RoomNumber.strip_leading_zeros(key)
        for map_key, map_value in mapping.items():
            if RoomNumber.strip_leading_zeros(map_key) == stripped:
                return map_value

        return None
```

**修改**: `backend/examroom/core/arrangement.py`

使用 `RoomNumber` 类替换所有重复的房间号处理逻辑。

#### 任务 3.4：性能优化

**修改**: `backend/examroom/core/arrangement.py`

```python
import secrets

def process_subjects_efficiently():
    for subject, count in ordered_subjects:
        mask = self.students[self.subject_column] == subject
        subject_students = self.students[mask]

        if len(subject_students) > 1:
            # 使用更好的随机源
            random_state = secrets.randbelow(2**32)
            subject_students = subject_students.sample(frac=1, random_state=random_state)

        # 延迟转换为字典，只在需要时转换
        yield subject, count, subject_students
```

#### 任务 3.5：代码规范改进

**提取常量**:
```python
# backend/examroom/core/arrangement.py
SMALL_GROUP_THRESHOLD = 10
DEFAULT_MAX_STUDENTS_PER_ROOM = 42
```

**统一命名**: 代码用英文，注释可用中文

**添加类型注解**: 使用 Python 3.9+ 风格

---

## 五、验证策略

### 5.1 每阶段验证

**第一阶段完成后**:
- 运行 `cd frontend && npm run dev`
- 手动测试所有功能（科目管理、监考编排、考场编排、打印）
- 检查浏览器控制台无错误
- 长时间运行（30分钟）检查内存使用

**第二阶段完成后**:
- 运行系统，测试所有功能
- 检查状态保存和备份功能
- 验证错误处理（故意触发错误，检查返回格式）

**第三阶段完成后**:
- 运行 `cd backend && pytest -v`，确保所有测试通过
- 代码覆盖率检查：`pytest --cov=backend --cov-report=html`
- 性能测试：导入大数据集（1000+ 学生）

### 5.2 回归测试清单

- [ ] 科目管理：导入、编辑、导出
- [ ] 监考编排：导入教师、生成排班、交换、优化
- [ ] 考场编排：三种模式（顺序、随机、选科）
- [ ] 打印功能：桌贴、准考证、考场角纸、学生信息表
- [ ] AI 助手：对话功能
- [ ] 授权管理：激活、验证

---

## 六、风险评估与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 重构引入新 bug | 中 | 高 | 每阶段完成后充分测试，保留回滚点 |
| 测试覆盖不足 | 中 | 中 | 优先测试核心算法（考场编排、监考分配） |
| 时间超预算 | 中 | 低 | 可以在第二阶段后暂停，已获得主要收益 |
| 依赖注入复杂度 | 低 | 低 | 使用简单的手动注入，不引入 DI 框架 |

---

## 七、成功标准

### 7.1 技术指标

- [ ] 所有🔴严重问题已修复
- [ ] 核心业务逻辑测试覆盖率 > 80%
- [ ] 单个函数不超过 50 行
- [ ] 圈复杂度 < 10
- [ ] 无内存泄漏（长时间运行内存稳定）
- [ ] 类型安全（前端 RPC 调用有类型检查）

### 7.2 业务指标

- [ ] 所有现有功能正常工作
- [ ] 性能无明显下降（大数据集处理时间 < 10秒）
- [ ] 错误信息友好（用户能理解）

### 7.3 可维护性指标

- [ ] 新增功能时只需修改 1-2 个文件
- [ ] 单元测试可以独立运行（不依赖文件系统）
- [ ] 代码审查时能快速理解业务逻辑

---

## 八、后续优化方向

重构完成后，可以考虑的进一步优化：

1. **前端状态管理**: 引入 Pinia composables，减少组件复杂度
2. **API 文档**: 使用 TypeDoc 生成 RPC API 文档
3. **性能监控**: 添加关键操作的性能日志
4. **国际化**: 支持多语言（如果需要）
5. **CI/CD**: 配置自动化测试和构建流程

---

**文档版本**: 1.0
**最后更新**: 2026-03-01
