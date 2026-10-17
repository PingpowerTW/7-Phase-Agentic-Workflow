---
name: Quick Fix Patterns
description: 常見問題快速修復模式。收集開發中常遇到的錯誤訊息和對應解法，提供錯誤碼到解決方案的快速查詢。
---

# Quick Fix Patterns - 常見問題速查

## When to Use

- 需要使用 quick-fix-patterns 時

快速查詢常見錯誤的解決方案，避免重複調查同樣的問題。

## 使用方式

1. 遇到錯誤時，先在此 skill 中搜尋
2. 若找到匹配，直接套用解法
3. 若未找到，解決後將其新增到模式庫

---

## Firebase 相關

### `auth/user-not-found`

**症狀**: 用戶登入時報錯
**解法**:

```javascript
try {
  await signInWithEmailAndPassword(auth, email, password);
} catch (error) {
  if (error.code === "auth/user-not-found") {
    // 用戶不存在，提示註冊
    showMessage("帳號不存在，請先註冊");
  }
}
```

### `permission-denied` (Firestore)

**症狀**: 讀寫 Firestore 時被拒絕
**檢查清單**:

1. 檢查 Firebase Rules 是否允許該操作
2. 確認用戶已登入 (`auth.currentUser` 不為 null)
3. 確認文件路徑正確
4. 檢查規則中的條件是否滿足

**常見修復**:

```javascript
// 確保有認證狀態再操作
if (!auth.currentUser) {
  throw new Error("請先登入");
}
```

### `auth.currentUser` 為 null

**症狀**: 頁面載入時 `auth.currentUser` 是 null
**原因**: Firebase Auth 狀態尚未初始化
**解法**:

```javascript
import { onAuthStateChanged } from "firebase/auth";

onAuthStateChanged(auth, (user) => {
  if (user) {
    // 現在可以安全使用 user
  }
});
```

---

## React 相關

### `Cannot read property 'X' of undefined`

**症狀**: 訪問物件屬性時報錯
**解法**:

```javascript
// 使用 optional chaining
const value = data?.property?.nested;

// 或提供預設值
const value = data?.property ?? "default";
```

### `Too many re-renders`

**症狀**: 無限重新渲染
**常見原因**:

```javascript
// ❌ 錯誤：在 render 中直接 setState
const [state, setState] = useState(0);
setState(1); // 會觸發無限循環

// ✅ 正確：在 useEffect 或 event handler 中
useEffect(() => {
  setState(1);
}, []);
```

### `useEffect` 依賴警告

**症狀**: ESLint 警告 missing dependency
**解法**:

```javascript
// 方案 1: 加入依賴
useEffect(() => {
  doSomething(value);
}, [value]);

// 方案 2: 使用 useCallback 包裝函數
const doSomething = useCallback(() => {
  // ...
}, [dependency]);

// 方案 3: 使用 ref 避免依賴
const valueRef = useRef(value);
valueRef.current = value;
```

### React Fast Refresh 警告

**症狀**: "Fast Refresh only works when a file only exports components"
**解法**: 將 context/hooks 分離到獨立檔案

```
// ❌ 混在一起
components/
  Auth.tsx  // 包含 AuthContext + AuthProvider + useAuth

// ✅ 分離
contexts/
  AuthContext.ts
components/
  AuthProvider.tsx
hooks/
  useAuth.ts
```

---

## TypeScript 相關

### `Type 'X' is not assignable to type 'Y'`

**診斷步驟**:

1. 檢查兩個類型的差異
2. 確認是否需要類型斷言
3. 考慮使用 union type

**常見修復**:

```typescript
// 類型斷言 (確定時使用)
const value = data as ExpectedType;

// 類型守衛 (更安全)
if (isExpectedType(data)) {
  // data 現在是 ExpectedType
}
```

### `any` 類型消除

**模式**:

```typescript
// ❌ 使用 any
function process(data: any) {}

// ✅ 使用 unknown + 類型守衛
function process(data: unknown) {
  if (typeof data === "string") {
    // data 是 string
  }
}

// ✅ 使用泛型
function process<T>(data: T): T {
  return data;
}
```

---

## Node.js / npm 相關

### `EACCES permission denied`

**解法**:

```bash
# 修復 npm 權限
sudo chown -R $(whoami) ~/.npm

# 或使用 nvm 管理 Node
```

### `Cannot find module`

**檢查清單**:

1. 確認套件已安裝: `npm install`
2. 檢查 import 路徑是否正確
3. 清除快取: `rm -rf node_modules && npm install`

### `ERESOLVE unable to resolve dependency tree`

**解法**:

```bash
# 使用 legacy peer deps
npm install --legacy-peer-deps

# 或強制安裝
npm install --force
```

### `The module 'xxx.node' was compiled against a different Node.js version` (Node ABI Mismatch)

**症狀**: 執行 `npm start` 或載入含有 C++ 原生模組（如 `better-sqlite3`, `bcrypt`, `canvas`）時後端直接 Crash：
```text
The module '.../better_sqlite3.node' was compiled against a different Node.js version using
NODE_MODULE_VERSION 127. This version of Node.js requires
NODE_MODULE_VERSION 137. Please try re-compiling or re-installing the module.
```
**原因**: 目前運行的 Node.js 版本（例如 Node 24，ABI 137）與 `node_modules` 中預先編譯好的 Native Addon（例如 Node 22，ABI 127）ABI 不相容。
**診斷與解法**:
1. 先檢查版本與 ABI：
   ```bash
   node --version
   node -p "process.versions.modules"
   ```
2. 切換至專案目標 Node 版本（例如使用 nvm 切換至 Node 22.x，ABI 127）：
   ```powershell
   nvm list
   nvm use 22.21.1
   ```
3. 在**正確的 Node 版本下**重新安裝或重新編譯依賴：
   ```powershell
   npm ci
   # 若預編譯二進制檔不符，才在對齊的 Node 版本下執行 rebuild:
   npm rebuild <module_name>
   ```
4. **嚴格禁止**在未切換的 Node 版本下執行 `npm rebuild`，否則會破壞其他環境的相容性。

---

### 服務無法連線 / 啟動失敗 診斷 SOP（避免層級誤判）

**原則**: **先查運行環境（Runtime / Port / Process / ABI），再查業務邏輯（Business Logic）**。
1. **檢查進程與連線埠**: 確認服務是否有 Crash？埠號是否被佔用？
   ```powershell
   Get-NetTCPConnection -LocalPort 3001 -State Listen
   ```
2. **區分預期業務阻擋 vs 系統崩潰**:
   - `HTTP 402 Payment Required` 或 `401 Unauthorized`：通常是商業邏輯/付費/權限控制在正常運作，**不可**把業務閘門當作 Bug 暴力繞過或修改資料庫。
   - `Connection Refused` / `Process Crash`：是系統/網路/ABI 層問題，應檢查終端日誌與 Native Module。

---

## 通用模式

### 防禦性編程

```javascript
// 常用防禦模式
function safeGet(obj, key, defaultValue = null) {
  return obj?.[key] ?? defaultValue;
}

// userId 驗證
if (!userId || typeof userId !== "string") {
  throw new Error("Invalid userId");
}
```

### 非同步錯誤處理

```javascript
// 統一錯誤處理
async function safeAsync(fn) {
  try {
    return [await fn(), null];
  } catch (error) {
    return [null, error];
  }
}

// 使用
const [data, error] = await safeAsync(() => fetchData());
if (error) handleError(error);
```

---

## 新增模式

當解決了一個新的常見問題，使用以下格式新增：

```markdown
### [錯誤訊息/症狀]

**症狀**: [用戶看到什麼]
**原因**: [為什麼發生]
**解法**:
\`\`\`javascript
// 修復代碼
\`\`\`
**相關**: [相關的其他問題]
```
