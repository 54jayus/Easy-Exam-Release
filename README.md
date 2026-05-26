# Easy Exam Release

这个仓库是 **Easy Exam** 的公开发布仓库，用于：

- 存放客户端自动更新所需的元数据
- 通过 GitHub Releases 发布 Windows 安装包
- 提供公开可访问的更新说明与下载地址

这个仓库 **不包含源码**，只用于发布。

## 仓库结构

```text
update/
└─ win/
   └─ latest.json
```

## 更新元数据地址

客户端建议读取：

```text
https://raw.githubusercontent.com/54jayus/Easy-Exam-Release/main/update/win/latest.json
```

## 安装包命名建议

与主项目当前打包规则保持一致：

```text
EasyExam-Setup-<version>.exe
```

例如：

```text
EasyExam-Setup-3.4.0422.exe
```

## 推荐发布流程

1. 在主项目中构建新的安装包
2. 在本仓库创建对应版本的 GitHub Release，例如 `v3.4.0422`
3. 上传安装包 `EasyExam-Setup-3.4.0422.exe`
4. 更新 `update/win/latest.json`
5. 提交并推送本仓库

## latest.json 字段说明

- `enabled`
  - 是否启用自动更新元数据
- `version`
  - 最新版本号
- `releaseDate`
  - 发布时间
- `notes`
  - 更新说明数组
- `mandatory`
  - 是否强制更新
- `url`
  - 安装包公开下载地址
- `sha256`
  - 安装包哈希值
- `size`
  - 安装包大小，单位字节

