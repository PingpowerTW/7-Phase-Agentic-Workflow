---
name: landing-page-architect
description: 高轉換率 (CRO) 落地頁架構與文案整合引擎。結合 AIDA/PAS 文案心理學模型、Hero 焦點轉換區、Social Proof 信任牆、Bento Grid 特色矩陣與定價/FAQ 轉化組件。
---

# landing-page-architect: 高轉換落地頁 (CRO) 架構引擎

> 專為 SaaS 產品、AI 應用、數位服務與行銷活動打造高轉換率 (Conversion Rate Optimization, CRO) 落地頁。
> 核心法則：**文案驅動設計 (Copy-First)、降低認知摩擦 (Frictionless)、多維信任錨點 (Social Proof)、明確單一行動 (Clear CTA)**。

---

## 🎯 When to Use

- 開發高轉換的產品首頁、SaaS 落地頁、行銷活動推廣頁。
- 需要從零編排具備商業說服力與心理學結構的頁面佈局。
- 整合文案（價值主張、痛點挖掘）與 UI 組件（Bento Grid、Pricing Table、FAQ）。

---

## 🧠 3 大高轉換文案心理學架構 (CRO Frameworks)

### 1. AIDA 模型 (預設標準)
1. **Attention (注意力)**: Hero 區塊 5 秒抓住眼球（強有力價值主張 + 痛點大標）。
2. **Interest (興趣)**: Bento Grid 呈現核心亮點與差異化。
3. **Desire (渴望)**: 客戶證言、實測數據、Before vs. After 對比。
4. **Action (行動)**: 零摩擦免費試用 / 一鍵預約 Demo。

### 2. PAS 模型 (痛點破局型)
1. **Problem (問題)**: 戳中現狀痛點（例如「手動整理資料每天浪費 2 小時？」）。
2. **Agitation (焦慮/代價)**: 放大痛點代價（錯誤率增加、錯過商機）。
3. **Solution (解法)**: 推出產品作為唯一且優雅的終極解法。

---

## 📐 8 大標準高轉換落地頁區塊 (Section Blueprint)

```
1. [Sticky Nav Bar]        -> 品牌 Logo + 核心功能錨點 + 右上 Primary CTA
2. [Hero Section]          -> Eyebrow + 10字大標 + 價值副標 + 主/副 CTA + 信任徽章
3. [Social Proof Strip]    -> 5+ 家知名企業 Logo 牆 + 量化數據 (e.g. 10k+ 活躍用戶)
4. [Bento Feature Matrix]  -> 1 個主打旗艦功能 (大卡片) + 3 個輔助功能 (小卡片)
5. [How It Works (3 Steps)]-> Step 1-2-3 清晰視覺引導，說明如何快速上手
6. [Interactive Pricing]   -> 月/年繳 Toggle (附 20% OFF 徽章) + "Most Popular" 推薦卡
7. [FAQ Accordion]         -> 排解 5~7 個最常見購買/使用疑慮 (消除最後猶豫)
8. [Final CTA & Footer]    -> 底部強烈召喚 + 隱私條款/聯絡資訊
```

---

## 🧩 經典高轉換組件範本 (CRO Component Templates)

### 1. 殺手級 Hero Section (SaaS / AI)
```tsx
export function ConversionHero() {
  return (
    <section className="relative pt-24 pb-16 px-4 max-w-5xl mx-auto text-center">
      {/* 1. 產品發布微標籤 */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-6">
        <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
        v2.0 全新上線 — 立即體驗 10 倍效率提升
      </div>

      {/* 2. 價值主張大標題 (10 字內清晰有感) */}
      <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-white mb-6 leading-tight">
        不再為雜務加班，<br />
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
          讓 AI 替你完成 80% 例行開發
        </span>
      </h1>

      {/* 3. 痛點副標 (≤ 25 字，點出具體產出) */}
      <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-8">
        全自動架構規劃、代碼審查與測試生成。專為獨立開發者與敏捷團隊打造的智能工作流。
      </p>

      {/* 4. 雙 CTA 按鈕 (主行動 + 次行動) */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
        <button className="min-h-[48px] px-8 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold rounded-xl shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all">
          免費開始使用 →
        </button>
        <button className="min-h-[48px] px-8 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-xl border border-slate-700 transition-all">
          觀看 2 分鐘演示
        </button>
      </div>

      {/* 5. 零摩擦信任承諾 */}
      <div className="mt-4 flex items-center justify-center gap-4 text-xs text-slate-500">
        <span>✓ 免綁信用卡</span>
        <span>✓ 14 天完整體驗</span>
        <span>✓ 隨時取消</span>
      </div>
    </section>
  );
}
```

### 2. 轉換率定價卡片 (Pricing Tier)
```tsx
export function PricingCard({ 
  name, price, period, description, features, isPopular, ctaText 
}: {
  name: string; price: string; period: string; description: string; features: string[]; isPopular?: boolean; ctaText: string;
}) {
  return (
    <div className={`relative p-8 rounded-2xl border flex flex-col justify-between ${
      isPopular 
        ? "bg-slate-900 border-cyan-500 shadow-xl shadow-cyan-500/10 ring-1 ring-cyan-500" 
        : "bg-slate-950 border-slate-800"
    }`}>
      {isPopular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-cyan-500 text-black text-xs font-bold uppercase rounded-full">
          最受歡迎
        </span>
      )}
      <div>
        <h3 className="text-xl font-bold text-white mb-2">{name}</h3>
        <p className="text-sm text-slate-400 mb-6">{description}</p>
        <div className="flex items-baseline gap-1 mb-6">
          <span className="text-4xl font-extrabold text-white">{price}</span>
          <span className="text-sm text-slate-400">/{period}</span>
        </div>
        <ul className="space-y-3 mb-8 text-sm text-slate-300">
          {features.map((f, i) => (
            <li key={i} className="flex items-center gap-2">
              <span className="text-cyan-400">✓</span> {f}
            </li>
          ))}
        </ul>
      </div>
      <button className={`w-full min-h-[44px] py-3 rounded-xl font-semibold transition-all ${
        isPopular 
          ? "bg-cyan-500 text-black hover:bg-cyan-400 shadow-md" 
          : "bg-slate-800 text-white hover:bg-slate-700"
      }`}>
        {ctaText}
      </button>
    </div>
  );
}
```

---

## 🚫 落地頁反模式 (CRO Anti-Patterns)
- ❌ **雙重主 CTA 衝突**：在同一屏放「立即購買」和「聯絡業務」，讓使用者不知所措。
- ❌ **虛假/模糊的證言**：「這是我用過最好的產品」- John D.（缺乏真實姓名、頭像或公司職稱）。
- ❌ **隱藏定價細節**：不標明幣別或隱藏綁約條件，導致結帳步驟跳出率暴增。
