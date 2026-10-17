---
name: Defensive Coding Checker
description: 防禦性編程檢查技能。檢查代碼中潛在的 undefined、null、邊界條件問題，確保代碼的健壯性。
---

# Defensive Coding Checker - 防禦性編程檢查

## When to Use

- 需要使用 defensive-coding-checker 時

識別並修復代碼中可能導致 runtime 錯誤的潛在問題。

## 檢查範圍

1. **Undefined/Null 存取**
2. **陣列邊界**
3. **物件屬性存取**
4. **函數參數驗證**
5. **非同步操作錯誤處理**

---

## 檢查清單

### 1️⃣ 變數可能為 undefined/null

#### 問題模式

```javascript
// ❌ 危險：未檢查 undefined
const name = user.name;

// ❌ 危險：解構可能失敗
const { data } = response;
```

#### 修復模式

```javascript
// ✅ 安全：使用 optional chaining
const name = user?.name ?? "Unknown";

// ✅ 安全：提供預設值
const { data = {} } = response ?? {};

// ✅ 安全：明確檢查
if (!user) {
  throw new Error("User is required");
}
```

---

### 2️⃣ 函數參數驗證

#### 問題模式

```javascript
// ❌ 危險：未驗證參數
async function getUser(userId) {
  return await db.collection("users").doc(userId).get();
}
```

#### 修復模式

```javascript
// ✅ 安全：參數驗證
async function getUser(userId) {
  if (!userId || typeof userId !== 'string') {
    throw new Error('Valid userId is required');
  }
  return await db.collection('users').doc(userId).get();
}

// ✅ 使用 TypeScript 限制
function getUser(userId: string): Promise<User> {
  // TypeScript 會在編譯時檢查
}
```

---

### 3️⃣ 陣列操作

#### 問題模式

```javascript
// ❌ 危險：假設陣列有元素
const first = items[0];

// ❌ 危險：未檢查陣列
items.map((item) => item.name);
```

#### 修復模式

```javascript
// ✅ 安全：檢查陣列
const first = items?.[0] ?? null;

// ✅ 安全：確保是陣列
const names = (items ?? []).map((item) => item?.name);

// ✅ 安全：明確檢查
if (!Array.isArray(items) || items.length === 0) {
  return [];
}
```

---

### 4️⃣ 非同步錯誤處理

#### 問題模式

```javascript
// ❌ 危險：未處理 Promise rejection
const data = await fetchData();

// ❌ 危險：未處理錯誤
fetch("/api/data").then((res) => res.json());
```

#### 修復模式

```javascript
// ✅ 安全：try-catch
try {
  const data = await fetchData();
} catch (error) {
  console.error('Failed to fetch:', error);
  // 處理錯誤或重新拋出
}

// ✅ 安全：Promise chain 錯誤處理
fetch('/api/data')
  .then(res => res.json())
  .catch(error => {
    console.error('Fetch failed:', error);
    return null;
  });

// ✅ 安全：wrapper 函數
async function safeAsync<T>(fn: () => Promise<T>): Promise<[T | null, Error | null]> {
  try {
    return [await fn(), null];
  } catch (error) {
    return [null, error as Error];
  }
}
```

---

### 5️⃣ Auth 狀態驗證

#### 問題模式

```javascript
// ❌ 危險：假設用戶已登入
const userId = auth.currentUser.uid;

// ❌ 危險：未等待 auth 初始化
useEffect(() => {
  const user = auth.currentUser; // 可能是 null
}, []);
```

#### 修復模式

```javascript
// ✅ 安全：檢查認證狀態
const user = auth.currentUser;
if (!user) {
  throw new Error("User not authenticated");
}
const userId = user.uid;

// ✅ 安全：使用 onAuthStateChanged
useEffect(() => {
  const unsubscribe = onAuthStateChanged(auth, (user) => {
    if (user) {
      // 現在可以安全使用
    }
  });
  return unsubscribe;
}, []);
```

---

## 常用防禦工具函數

```typescript
// utils/defensive.ts

/**
 * 確保值不是 null 或 undefined
 */
export function assertDefined<T>(
  value: T | null | undefined,
  message = "Value is required",
): T {
  if (value === null || value === undefined) {
    throw new Error(message);
  }
  return value;
}

/**
 * 安全地獲取物件屬性
 */
export function safeGet<T>(
  obj: Record<string, any> | null | undefined,
  key: string,
  defaultValue: T,
): T {
  return obj?.[key] ?? defaultValue;
}

/**
 * 確保是有效的陣列
 */
export function ensureArray<T>(value: T | T[] | null | undefined): T[] {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}

/**
 * 安全的 JSON parse
 */
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json) as T;
  } catch {
    return fallback;
  }
}

/**
 * 驗證 userId
 */
export function validateUserId(userId: unknown): string {
  if (!userId || typeof userId !== "string" || userId.trim() === "") {
    throw new Error("Invalid userId");
  }
  return userId.trim();
}
```

---

## 自動檢查腳本

```bash
#!/bin/bash
# defensive-check.sh

echo "檢查防禦性編程問題..."

# 檢查未處理的 optional chaining
echo "🔍 檢查潛在的 undefined 存取..."
grep -rn "\.\w\+\.\w\+" --include="*.ts" --include="*.tsx" src/ | \
  grep -v "?." | \
  grep -v "//" | \
  head -20

# 檢查未包裝的 async/await
echo "🔍 檢查未包裝的 async 操作..."
grep -rn "await " --include="*.ts" --include="*.tsx" src/ | \
  grep -v "try" | \
  grep -v "catch" | \
  head -20
```

---

## ESLint 規則建議

```json
{
  "rules": {
    "@typescript-eslint/no-non-null-assertion": "error",
    "@typescript-eslint/strict-boolean-expressions": "warn",
    "@typescript-eslint/no-floating-promises": "error",
    "@typescript-eslint/no-unsafe-member-access": "warn",
    "@typescript-eslint/no-unsafe-call": "warn"
  }
}
```

---

## 檢查報告模板

```markdown
## 防禦性編程檢查報告

**檢查日期**: [YYYY-MM-DD]
**檢查範圍**: [檔案/目錄]

### 🔴 高風險問題

| 檔案    | 行號 | 問題            | 建議修復                |
| ------- | ---- | --------------- | ----------------------- |
| auth.ts | 45   | `userId` 未驗證 | 加入 `validateUserId()` |

### 🟡 中風險問題

| 檔案    | 行號 | 問題            | 建議修復               |
| ------- | ---- | --------------- | ---------------------- |
| user.ts | 23   | 缺少 null check | 使用 optional chaining |

### 統計

- 高風險: X 個
- 中風險: X 個
- 已修復: X 個
```
