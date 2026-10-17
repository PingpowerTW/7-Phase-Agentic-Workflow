---
name: design-taste-frontend
description: >
  Phase 3 & 4 反罐頭前端視覺、互動與 UX 設計總擎（整合 frontend-taste-v2、frontend-design、persona-frontend-expert，並內建 gsap-motion 動效、cinematic-ui 電影光影、landing-page-architect 高轉換落地頁與 ux-audit 量化審查按需參考庫）。
  觸發詞：frontend-taste-v2, frontend-design, gsap, cinematic-ui, landing-page, ux-audit, 前端設計, 落地頁, 網頁改版.
---

# 🎨 tasteskill: Anti-Slop Frontend & UX Engine (8-in-1 Modular Architecture)

> **Token Economy Notice**: 本技能採用分層按需載入架構（主檔控制在 9 KB 內）。核心執行迴圈與硬性規範見下方，深度領域模組存放於 `./references/`，僅在任務涉及該領域時按需讀取。

## 📚 Deep Reference Matrix (按需讀取，平時 0 Token 開銷)

| 參考模組 (`./references/`) | 涵蓋範圍 | 何時讀取 (When to Read) |
|---|---|---|
| [`references/dial-matrix.md`](references/dial-matrix.md) | 三大旋鈕 (Variance, Motion, Density) 1-10 級校準與預設集 | 需要微調視覺獨特性、動畫節奏或資訊密度時 |
| [`references/design-systems.md`](references/design-systems.md) | 官方設計系統映射 (M3, Fluent, Carbon, Polaris, Radix, shadcn) | 選擇或安裝企業級 UI 套件時 |
| [`references/engineering-directives.md`](references/engineering-directives.md) | 字體、色彩、材質、Sticky-Stack/橫向滾動骨架與深色模式 | 實作進階版面、滾動視差或主題鎖定時 |
| [`references/anti-slop-guide.md`](references/anti-slop-guide.md) | AI 罐頭特徵黑名單、Hallmark 5 維度評分與詞彙庫 | 執行視覺品質審查與 Anti-Slop 檢查時 |
| [`references/gsap-motion.md`](references/gsap-motion.md) | GSAP 3、ScrollTrigger、`useGSAP` 生命週期清理與 GPU 加速 | 實作複雜時間軸動畫或滾動視差時 |
| [`references/cinematic-ui.md`](references/cinematic-ui.md) | 電影級敘事光影（諾蘭幾何、魏斯安德森對稱、維勒納夫巨構） | 打造品牌敘事、作品集或沉浸式視覺頁時 |
| [`references/landing-page-cro.md`](references/landing-page-cro.md) | 高轉換落地頁 (CRO)：AIDA/PAS 文案、Hero、Social Proof、定價表 | 設計 SaaS / 產品行銷落地頁時 |
| [`references/ux-audit.md`](references/ux-audit.md) | 格式塔心理學、費茨定律、44px 熱區、40% Disabled Opacity 量化審查 | 執行 `/ui-check`、UX 易用性與無障礙審查時 |

---

## 0. BRIEF INFERENCE (動手前先讀懂場景與受眾)

1. **辨識 6 大訊號**：
   - **頁面類型**：Landing Page (SaaS/消費品/活動)、作品集、舊站改版 (保留品牌 vs 徹底翻新)、資料後台。
   - **風格關鍵字**：Minimalist / Linear-style / Editorial / Brutalist / Apple-y / Serious B2B。
   - **受眾與硬約束**：B2B 採購、一般消費者或法規/無障礙優先場景（無障礙與信任感優先於炫技）。
2. **先輸出一行「Design Read」與三大旋鈕設定**：
   > 格式：*"Reading this as: `<page kind>` for `<audience>`, with a `<vibe>` language, leaning toward `<design system/aesthetic>`. Dials: `VARIANCE=X, MOTION=Y, DENSITY=Z`."*
3. **模糊即問（限 1 題）**：若風格方向分歧，只問 1 個關鍵問題（附推薦選項）；若脈絡已清楚，直接宣告 Design Read 開工。

---

## 1. 預設技術棧與工程硬規範 (Default Architecture & Guardrails)

- **React / Next.js (RSC 優先)**：預設 Server Components；凡使用狀態、事件、Motion 或 GSAP 的互動節點，必須拆為獨立 Leaf Client Component (`'use client'`)。
- **Tailwind CSS + `shadcn/ui`**：優先使用語意化 CSS 變數 Token（`bg-surface-primary` 等），禁止隨意混用兩套 UI 庫。
- **原生與Ponytail 優先**：能用原生 HTML 表單與 CSS Grid (`grid-cols-1 md:grid-cols-3 gap-6`、`minmax()`、`clamp()`) 解決者，禁止手算 Flexbox 百分比或用 `useState` 追蹤連續滾動/滑鼠座標（改用 CSS 或 Motion `useMotionValue`）。
- **Viewport 與熱區穩定度**：
  - 全屏 Hero 強制使用 `min-h-[100dvh]`，**嚴禁使用 `h-screen`**（防手機瀏覽器網址列跳動）。
  - 所有可點擊按鈕/連結最小熱區 `min-h-[44px] min-w-[44px]`；Disabled 狀態統一 `opacity-40 cursor-not-allowed`。
- **Icon 與 Emoji 紀律**：單一專案只用一套圖示庫（優先 `@phosphor-icons/react`、`@radix-ui/react-icons`、`@tabler/icons-react`；僅在專案已安裝時才用 `lucide-react`），**嚴禁手刻 SVG Path，且預設禁止在標題與卡片亂塞 Emoji**。
- **依賴預檢**：引用任何第三方套件前先檢查 `package.json`，未安裝者先提示安裝指令。

---

## 2. 效能、無障礙與舊站改版守則 (Performance, A11y & Redesign)

1. **GPU 加速與 `prefers-reduced-motion`（強制）**：
   - 動畫僅限 `transform` 與 `opacity`，嚴禁對 `top/left/width/height` 做動畫；噪點濾鏡僅能掛在 `fixed inset-0 pointer-events-none` 層。
   - 凡 `MOTION_INTENSITY > 3` 必須支援 `prefers-reduced-motion`（以及 GSAP `useGSAP` / `useEffect` 卸載清理）。
2. **Core Web Vitals 與完整狀態**：
   - LCP < 2.5s、INP < 200ms、CLS < 0.1；任何動態資料區塊必須具備 **Loading Skeleton、Empty 空狀態與 Error 狀態**。
3. **舊站改版 (Redesign Protocol)**：
   - 動手前先盤點現有 Brand Tokens、路由結構與 SEO Meta。
   - **禁止靜默破壞**：未獲批准前，嚴禁更改 URL slug、主導覽列標籤、表單欄位 `name`（避免破壞既有 SEO 與分析埋點）。

---

## 3. FINAL PRE-FLIGHT CHECK (交付前 12 項必過門禁)

輸出代碼前逐一自檢，任一未過立即修正：
- [ ] **已宣告一行 Design Read 與三大旋鈕 (`VARIANCE / MOTION / DENSITY`)**？
- [ ] **零 AI 罐頭特徵 (Zero AI Slop)**：無 `#6366f1` 萬用紫藍漸層、無「三張等寬白卡+Emoji」、無捏造假數據 (`99.9% uptime`, `10k+ users`, `Acme Corp`)？
- [ ] **零破折號濫用 (Zero Em-Dashes `—`)**：文案與標題無 AI 習慣性破折號？
- [ ] **主題與色彩一致性鎖定**：全頁單一主題（無中途突兀反轉黑白）、單一主強調色 (Accent 每屏 ≤ 2 處)、統一圓角系統？
- [ ] **對比度合規**：所有按鈕、文字與表單 Placeholder 符合 WCAG AA (4.5:1) 對比度，無白底白字或黑底暗字？
- [ ] **Hero 符合首屏紀律**：使用 `min-h-[100dvh]`、主標題 ≤ 2 行、副標 ≤ 20 字、CTA 首屏無需滾動即可見、最多 4 個文字元素？
- [ ] **版面節奏多樣化**：無連續 3 個區塊使用相同的左右圖文交替 (Zigzag) 版型；Bento Grid 格數與項目數精確吻合無空洞？
- [ ] **真實 API 與圖片**：無寫死假陣列冒充 API、無純 `div` 假截圖、無壓在圖片上的無意義標籤膠囊？
- [ ] **互動與無障礙完整**：點擊熱區 ≥ 44px、具備 Skeleton/Empty/Error 狀態、動畫支援 `prefers-reduced-motion` 與清理函式？
- [ ] **單一组件 ≤ 200 行**，且互動邏輯已隔離於 `'use client'` 葉節點？
