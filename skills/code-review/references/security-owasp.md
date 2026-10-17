---
name: security-best-practices
description: 程式碼安全審查、OWASP 指南、常見漏洞防護
---

# 安全最佳實踐

## When to Use

- 需要使用 security-best-practices 時

保護應用程式免受常見安全威脅。

## OWASP Top 10 防護

### 1. 注入攻擊 (Injection)

```javascript
// ❌ SQL 注入風險
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ 使用參數化查詢
const query = "SELECT * FROM users WHERE id = ?";
db.query(query, [userId]);

// ✅ ORM
const user = await User.findById(userId);
```

### 2. XSS (跨站腳本攻擊)

```javascript
// ❌ 直接插入 HTML
element.innerHTML = userInput;

// ✅ 使用 textContent
element.textContent = userInput;

// ✅ React 自動轉義
<div>{userInput}</div>;

// ⚠️ dangerouslySetInnerHTML 需要消毒
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />;
```

### 3. CSRF (跨站請求偽造)

```javascript
// 使用 CSRF Token
app.use(csrf());

// 在表單中包含 token
<input type="hidden" name="_csrf" value={csrfToken} />;

// 同源政策
res.setHeader("X-Frame-Options", "DENY");
res.setHeader("Content-Security-Policy", "frame-ancestors 'none'");
```

### 4. 敏感資料保護

```javascript
// ❌ 明文儲存密碼
const user = { password: "plaintext123" };

// ✅ 加密儲存
import bcrypt from "bcrypt";
const hashedPassword = await bcrypt.hash(password, 12);

// ❌ 回傳敏感資料
res.json(user);

// ✅ 過濾敏感欄位
const { password, ...safeUser } = user;
res.json(safeUser);
```

## 認證與授權

### JWT 最佳實踐

```javascript
// 使用短期 token
const token = jwt.sign(payload, secret, { expiresIn: "15m" });

// 使用 refresh token
const refreshToken = jwt.sign({ userId }, refreshSecret, { expiresIn: "7d" });

// 在 httpOnly cookie 中儲存
res.cookie("token", token, {
  httpOnly: true,
  secure: true,
  sameSite: "strict",
});
```

### Firebase Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 使用者只能存取自己的資料
    match /users/{userId} {
      allow read, write: if request.auth != null
                         && request.auth.uid == userId;
    }

    // 驗證資料格式
    match /orders/{orderId} {
      allow create: if request.auth != null
                    && request.resource.data.userId == request.auth.uid
                    && request.resource.data.total is number
                    && request.resource.data.total > 0;
    }
  }
}
```

## 環境變數安全

```bash
# ❌ 不要在程式碼中硬編碼
const apiKey = 'sk-1234567890';

# ✅ 使用環境變數
const apiKey = process.env.API_KEY;

# .env 不應該提交到版控
echo ".env" >> .gitignore
```

## 安全檢查清單

- [ ] 所有使用者輸入都已驗證
- [ ] 密碼使用 bcrypt 加密
- [ ] API 使用 HTTPS
- [ ] 敏感資料不在日誌中
- [ ] CORS 設定正確
- [ ] Rate limiting 已實作
- [ ] 依賴套件無已知漏洞 (`npm audit`)

## Security Response Protocol

> 發現安全問題時的 SOP — 不要繼續寫 code，先處理安全。

```
🚨 發現安全問題
      │
      ▼
1. STOP — 停止所有其他工作
      │
      ▼
2. 分類嚴重度
   🔴 CRITICAL（secrets 外洩、SQL injection）→ 立即修復
   🟡 HIGH（XSS、CSRF）→ 當次修復
   🟢 MEDIUM（缺少 rate limit）→ 加入 backlog
      │
      ▼
3. 修復 🔴 CRITICAL
   - 修復漏洞
   - 輪替任何可能外洩的 secrets
   - 確認 .env / .gitignore 設定
      │
      ▼
4. 全域掃描
   - grep 整個 codebase 找類似問題
   - 檢查 git history 是否有 secrets 殘留
   - npm audit / pip audit
      │
      ▼
5. 驗證 & 記錄
   - 跑 /verify 確認修復沒壞其他東西
   - 記錄到 QA_RECORD.md
```
