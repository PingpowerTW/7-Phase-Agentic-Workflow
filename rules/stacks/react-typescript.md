# ⚛️ React 19 & TypeScript 專用架構與編碼規範

> 本分冊為動態按需載入規則。當專案包含 `package.json` 或涉及 React / TypeScript 開發時載入。

---

## 1. 核心鐵律與靜態門禁 (Level 0.5 AST Guard)

- **零 `any` 型別污染 (INV_TS_01)**：
  - 生產代碼中嚴禁使用 `: any`、`as any` 或 `<any>` 逃避型別檢查。
  - 必須改用明確介面、泛型或 `unknown` 搭配 Type Guard / Zod Schema。
- **組件規模上限 200 行 (INV_REACT_01)**：
  - 單一 `.tsx` / `.jsx` 組件嚴禁超過 200 行。
  - 超出規模時，強制將狀態與商業邏輯抽離至 Custom Hook，或將子區塊拆分為小組件。
- **GSAP StrictMode 生命週期安全 (INV_REACT_02)**：
  - 在 React 組件中使用 gsap 動畫時，強制使用 `@gsap/react` 的 `useGSAP()` 或 `gsap.context()`。
  - 嚴禁在裸 `useEffect` 中直接呼叫 `gsap.to / from / timeline`，防止 StrictMode 下動畫重複疊加與記憶體洩漏。
- **零生產接縫 (INV_VERIFY_03 / INV_VERIFY_04)**：
  - 非測試檔嚴禁 export 帶有 `_test_`, `mock`, `fake`, `stub` 前綴的識別碼，或在函式公開簽名中包含 mock 參數。

---

## 2. UI 設計基底與反罐頭規範 (Anti-Slop)

- **UI 基底首選 `shadcn/ui`**：
  - 採用 Radix UI Primitives + Tailwind CSS，原始碼直放 `src/components/ui/`，保持 100% 程式碼掌控權。
  - 嚴禁手造未經無障礙檢驗之複雜控制項（Dialog, Dropdown, Sheet）。
- **UX 量化指標 (ux-audit)**：
  - 最小點擊熱區：`min-h-[44px] min-w-[44px]`。
  - 禁用狀態清晰反饋：`opacity-40 cursor-not-allowed`。
  - 杜絕萬用紫藍漸層 (`#6366f1`) 與千篇一律的無趣白卡。
