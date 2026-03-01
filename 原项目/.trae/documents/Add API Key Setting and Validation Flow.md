
# 计划：新增 API 设置入口与校验流程

## 1. 修改许可证验证逻辑
**文件:** `client_license.py`
- 更新 `_verify_cert_file` 方法，使其严格只读取 `license.cert` 的**第一行**内容进行验证。这将确保在第二行追加 API KEY 信息后，不会破坏原有的许可证签名校验。

## 2. 更新 API Key 加载逻辑
**文件:** `ui/ai/zhipu_client.py`
- 修改 `load_api_key` 函数，优先或增加检查 `license.cert` 文件。
- **逻辑:** 读取 `license.cert`，如果第二行以 `API_KEY:` 开头，则提取并返回该 Key。

## 3. 创建 API 设置对话框
**文件:** `ui/page/api_setting_dialog.py` (新文件)
- 创建 `ApiSettingDialog` 类。
- **UI 组件:**
  - 厂商标签: "智谱清言" (只读)
  - 模型标签: "GLM-4.6V-Flash" (只读)
  - API KEY 输入框: `QLineEdit`
  - 获取链接: 可点击的链接 `https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys`
  - 按钮: "验证并保存"
- **逻辑:**
  - 点击验证时，使用输入的 Key 初始化 `ZhipuChatClient` 并尝试发送简单请求。
  - **失败:** 弹出错误提示（Toast 或 弹窗），并停留在设置界面。
  - **成功:** 
    - 读取 `license.cert` 内容。
    - 将 `API_KEY: <key>` 写入或更新至文件的第二行（保留第一行证书）。
    - 保存文件并关闭对话框，返回成功信号。

## 4. 集成到主窗口
**文件:** `ui/main_window.py`
- 修改 `open_ai_assistant` 方法。
- **新逻辑:**
  - 检查 `license.cert` 第二行是否存在有效的 API KEY。
  - **如果不存在:**
    - 实例化并显示 `ApiSettingDialog`。
    - 仅当设置对话框验证成功并关闭后，才继续打开 `AiAssistantDialog`。
  - **如果存在:**
    - 直接打开 `AiAssistantDialog`（此时 `zhipu_client` 会自动读取到 Key）。

## 5. 验证
- **场景 1 (无 Key):** 清除或备份现有 Key，点击“AI助手”，确认弹出设置界面。
- **场景 2 (无效 Key):** 输入错误 Key，确认提示错误且不进入助手。
- **场景 3 (有效 Key):** 输入正确 Key，确认验证通过，写入文件，并自动打开助手。
- **场景 4 (持久化):** 重启软件，确认能自动读取 Key 并直接打开助手。
