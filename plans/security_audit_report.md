# 🔒 edu-flask 项目安全审计报告

**审计日期**: 2026-02-16  
**审计范围**: 代码库敏感信息泄露检查  
**风险等级**: 🔴 **严重 (Critical)**

---

## 🚨 发现的安全问题

### 1. 🔴 严重：用户密码硬编码

**文件**: [`app.py`](app.py:21-25)

```python
users = {
    'admin': 'admin123',
    'lily': 'lily2025',
    'edu': 'edu2025',
}
```

**风险**:
- 用户密码以明文形式直接写在代码中
- 已提交到 GitHub 公开仓库，任何人都可以看到
- 攻击者可以使用这些凭据登录系统

**建议**:
- 立即更改这些密码
- 使用环境变量或配置文件（不纳入版本控制）存储密码
- 考虑使用数据库存储用户凭据，并使用密码哈希（如 bcrypt）

---

### 2. 🔴 严重：外部系统登录凭据泄露

**文件**: [`get_excel_data_curr/config.json`](get_excel_data_curr/config.json:3-4)

```json
{
  "username": "27011228",
  "password": "123123",
  ...
}
```

**风险**:
- 天津科技大学公寓管理系统的登录凭据已泄露
- 攻击者可以访问该系统并获取学生数据
- 可能违反数据保护法规

**建议**:
- **立即更改该系统的密码**
- 将 config.json 添加到 .gitignore
- 使用环境变量存储敏感配置

---

### 3. 🔴 严重：Flask Secret Key 泄露

**文件**: [`app.py`](app.py:15)

```python
app.secret_key = 'your_secret_key'
```

**风险**:
- Flask session 加密密钥已公开
- 攻击者可以伪造用户会话
- 可以绕过登录验证

**建议**:
- 更换为强随机密钥
- 使用环境变量存储：`app.secret_key = os.environ.get('FLASK_SECRET_KEY')`

---

### 4. 🟠 高危：日志中记录密码

**文件**: [`app.py`](app.py:35)

```python
logging.debug(f"Received POST request with username: {username} and password: {password}")
```

**风险**:
- 用户密码被写入日志文件
- 日志文件可能被提交到 GitHub（当前没有 .gitignore）

**建议**:
- 移除日志中的密码记录
- 只记录用户名，不记录密码

---

### 5. 🟠 高危：缺少 .gitignore 文件

**问题**: 项目根目录没有 .gitignore 文件

**风险**:
- 日志文件（edu.log, nohup.out, out.log）可能被提交
- Excel 报表文件（result-files/）可能被提交，包含学生数据
- IDE 配置（.idea/）可能被提交

**建议**:
- 创建 .gitignore 文件

---

### 6. 🟡 中危：敏感 API ID 泄露

**文件**: [`get_excel_data_curr/config.json`](get_excel_data_curr/config.json:22-43)

```json
"bid_dict": {
  "1": "7d6716cae1ce1ce062af12d9ddbe7798",
  "2": "7e994f8176dbd4a52c25794b1c14a1f3",
  ...
}
```

**风险**:
- 楼栋 API ID 已公开
- 可能被用于未授权的数据访问

---

### 7. 🟡 中危：服务器路径信息泄露

**文件**: [`get_excel_data_curr/config.json`](get_excel_data_curr/config.json:8-9)

```json
"binary_location_prod": "/opt/google/chrome/chrome",
"driver_location_prod": "/usr/local/bin/chromedriver",
```

**风险**:
- 暴露服务器文件系统结构
- 可用于推断服务器配置

---

## ✅ 修复建议清单

### 立即执行（紧急）

- [ ] **更改所有已泄露的密码**
  - [ ] 公寓管理系统密码（27011228 账户）
  - [ ] admin、lily、edu 用户的登录密码
  
- [ ] **更换 Flask Secret Key**
  - 生成新的强随机密钥
  - 使用环境变量配置

- [ ] **创建 .gitignore 文件**
  ```
  # 敏感配置
  get_excel_data_curr/config.json
  
  # 日志文件
  *.log
  nohup.out
  
  # 生成的文件
  result-files/
  
  # IDE
  .idea/
  __pycache__/
  *.pyc
  
  # 环境变量
  .env
  ```

- [ ] **从 Git 历史中移除敏感文件**
  ```bash
  # 使用 git filter-branch 或 BFG Repo-Cleaner
  git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch get_excel_data_curr/config.json' \
    --prune-empty --tag-name-filter cat -- --all
  ```

### 后续改进

- [ ] **使用环境变量管理敏感配置**
  - 创建 `.env` 文件（不纳入版本控制）
  - 使用 `python-dotenv` 加载环境变量

- [ ] **移除日志中的密码记录**
  - 修改 [`app.py`](app.py:35) 中的日志代码

- [ ] **添加密码哈希**
  - 使用 `werkzeug.security` 或 `bcrypt`
  - 存储密码哈希而非明文

- [ ] **添加 requirements.txt**
  - 明确项目依赖

---

## 📋 推荐的 .gitignore 内容

```gitignore
# 敏感配置文件
get_excel_data_curr/config.json
.env
*.env

# 日志文件
*.log
nohup.out
out.log
edu.log

# 生成的报表文件
result-files/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db

# 备份文件
backup/
```

---

## 📝 推荐的环境变量配置

创建 `.env` 文件：

```env
# Flask 配置
FLASK_SECRET_KEY=your_very_long_random_secret_key_here_at_least_32_chars

# 用户凭据（建议后续迁移到数据库）
USER_ADMIN_PASSWORD=new_secure_password_here
USER_LILY_PASSWORD=new_secure_password_here
USER_EDU_PASSWORD=new_secure_password_here

# 外部系统凭据
TUST_USERNAME=27011228
TUST_PASSWORD=your_new_password_here

# Chrome 配置
CHROME_BINARY=/opt/google/chrome/chrome
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
```

---

## ⚠️ 重要提醒

1. **立即行动**: 已泄露的密码应立即更改，因为它们已经在 GitHub 上公开
2. **清理 Git 历史**: 仅仅删除文件不够，需要从 Git 历史中彻底移除
3. **通知相关方**: 如果这是生产系统，需要通知相关人员更改密码
4. **考虑仓库私有化**: 如果项目包含敏感信息，考虑将 GitHub 仓库设为私有

---

## 📊 风险等级总结

| 问题 | 风险等级 | 状态 |
|------|---------|------|
| 用户密码硬编码 | 🔴 严重 | 需立即修复 |
| 外部系统凭据泄露 | 🔴 严重 | 需立即修复 |
| Flask Secret Key 泄露 | 🔴 严重 | 需立即修复 |
| 日志记录密码 | 🟠 高危 | 需尽快修复 |
| 缺少 .gitignore | 🟠 高危 | 需尽快修复 |
| API ID 泄露 | 🟡 中危 | 建议修复 |
| 服务器路径泄露 | 🟡 中危 | 建议修复 |
