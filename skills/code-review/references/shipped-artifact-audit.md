# 出貨產物稽核 (Shipped Artifact Audit)

> 吸收自 REA (morluto/rea) 的「攻擊者視角」：**源碼 ≠ 出貨物**。打包、tree-shaking、依賴解析會讓產物偏離源碼，此清單只審產物，補源碼審查盲區。
> 觸發時機：Phase 5 發佈前 / 全域掃描矩陣最後一關。全部為本機指令，只回傳命中行（≈0 LLM Token），**禁止把整包 bundle 讀進上下文**。

## 1. 密鑰外洩 (CRITICAL)
```powershell
# Web / Electron 產物（dist、build、out、.next/static 依專案調整）
Get-ChildItem dist -Recurse -File -Include *.js,*.html,*.json,*.map |
  Select-String -Pattern 'sk-[A-Za-z0-9_-]{20,}','ghp_[A-Za-z0-9]{36}','-----BEGIN [A-Z ]*PRIVATE KEY','service_account','SUPABASE_SERVICE_ROLE' |
  Select-Object Path, LineNumber -First 20
```
- ⚠️ Firebase Web `apiKey` (`AIza...`) 設計上可公開，**不算外洩**；命中時改驗 Security Rules / API 金鑰 HTTP referrer 限制。
- `service_role`、私鑰、`sk-` 出現在前端產物 = 🔴 直接阻斷發佈。

## 2. Source Map 與除錯殘留 (HIGH)
```powershell
Get-ChildItem dist -Recurse -Filter *.map | Measure-Object        # 期望 0（或僅上傳至錯誤追蹤服務）
Get-ChildItem dist -Recurse -Include *.js | Select-String 'sourceMappingURL|debugger;|localhost:\d+' | Select-Object Path, LineNumber -First 20
```

## 3. 打包組成 (MEDIUM)
- 最大的 5 個檔：`Get-ChildItem dist -Recurse -File | Sort-Object Length -Desc | Select-Object -First 5 Name, Length`
- 被意外打包的 dev 依賴 / 死碼：在產物 grep 測試或開發套件名（如 `msw`、`@faker-js`、`storybook`）。命中 = tree-shaking 或 import 邊界錯誤。

## 4. 依賴實際清單 (SBOM)
- Go：`go version -m <binary>`（Go 工具鏈原生，列出實際編入的 module 與版本）
- Rust：`cargo audit bin <binary>`（需以 `cargo auditable build` 建置）
- Node：以 lockfile 為準，`npm audit --omit=dev`

## 5. Android APK
- 權限：`aapt2 dump permissions app.apk`（SDK build-tools 已附）
- 密鑰：APK 為 zip，`mkdir tmp_apk; tar -xf app.apk -C tmp_apk`（`Expand-Archive` 拒收 `.apk` 副檔名），再對 `classes*.dex`、`resources.arsc`、`assets/` 套用第 1 節 pattern（`res/values/*.xml` 已編譯進 `resources.arsc`，不會以原檔存在）。

## 6. 部署偏移 (Deploy Drift)
```powershell
# 線上檔與本地產物雜湊比對，不一致 = 部署非當前 commit
Invoke-WebRequest -UseBasicParsing https://<site>/assets/<file>.js -OutFile tmp_remote.js   # 原始位元組；勿用 Out-File（PS5 會加 BOM/CRLF 致雜湊必不符）
(Get-FileHash tmp_remote.js).Hash -eq (Get-FileHash dist/assets/<file>.js).Hash
```

> 需要深度逆向（閉源依賴、native binary）時，才單次執行 `npx rea-agents@latest <command> --json`，**不執行 `setup`**（不註冊常駐 MCP、不裝全域 Skill）。
