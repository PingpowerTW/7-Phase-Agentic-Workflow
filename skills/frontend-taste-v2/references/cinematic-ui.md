---
name: cinematic-ui
description: 電影級敘事視覺與氛圍光影設計引擎。借鑑導演鏡頭語法（諾蘭幾何感、魏斯安德森對稱、維勒納夫巨構巨景、賽博龐克光暈），提供電影寬螢幕佈局、景深光照與沉浸式敘事 UI。
---

# cinematic-ui: 電影級敘事視覺與氛圍光影引擎

> 專為品牌形象官網、旗艦產品發表、遊戲/娛樂特頁與展覽型網站設計。
> 核心思維：**將網頁視為電影分鏡 (Storyboarding)，以光影氛圍 (Ambient Lighting)、畫幅比例 (Cinematic Aspect Ratio) 與景深層次 (Depth of Field) 創造沉浸感。**

---

## 🎯 When to Use

- 打造極具視覺震撼力與故事感的 Landing Page 或形象官網。
- 擺脫平庸 SaaS 模板，營造高級奢華、硬派科技、暗黑賽博或極簡巨構風格。
- 整合視差滾動、氛圍聚光燈 (Spotlight) 與微顆粒質感 (Film Grain)。

---

## 🎬 4 大導演視覺美學體系 (Director Archetypes)

| 導演風格 | 視覺特徵 | 適用場景 | 核心樣式手法 |
|---|---|---|---|
| **Christopher Nolan (諾蘭風格)** | 單色冷調、精密幾何網格、強烈時間感、高張力排版 | 頂級金融、資安防護、高階 AI 模型、時間序列工具 | 極黑 (`#0a0a0c`) + 冷銀灰 + 細緻等寬刻度 + 銳角冷光 |
| **Denis Villeneuve (維勒納夫巨構)** | 沙漠/煙霧氛圍、大尺度留白巨像、沉穩單色調、呼吸感 | 航太科技、深科技 (DeepTech)、綠能巨構、硬核硬體 | 大面積環境霧氣、單色巨型標題、超微小數據註釋對比 |
| **Wes Anderson (安德森對稱)** | 嚴格中軸對稱、復古粉彩/暖色系、平面框景、趣味細節 | 獨立創作者品牌、文創電商、咖啡/精緻餐飲、藝術活動 | 雙欄極致對稱、暖駝色 (`#f5efe6`) + 橄欖綠 + 雙線復古邊框 |
| **Neo-Tokyo Cyberpunk (賽博龐克)** | 霓虹逆光、暗黑玻璃透光、微弱光暈擴散、光學透鏡眩光 | 遊戲官網、Web3 / 加密產品、硬體周邊、夜間極客應用 | 聚光燈徑向漸層 (`radial-gradient`) + 背面光暈 + 透鏡光斑 |

---

## 💡 氛圍光影與景深技術標準 (Lighting & Depth)

### 1. 聚光燈背景 (Ambient Spotlight CSS)
```css
/* 電影感環境聚光燈 */
.cinematic-spotlight {
  background: radial-gradient(
    600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(255, 255, 255, 0.06),
    transparent 40%
  );
}

/* 暗黑賽博微弱光暈 */
.cinematic-ambient-glow {
  position: absolute;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 800px;
  height: 400px;
  background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.15), transparent 70%);
  filter: blur(80px);
  pointer-events: none;
}
```

### 2. 電影膠卷顆粒感 (Film Grain Overlay)
```tsx
export function FilmGrain() {
  return (
    <div 
      className="pointer-events-none fixed inset-0 z-50 opacity-[0.035] mix-blend-overlay"
      style={{
        backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E\")"
      }}
    />
  );
}
```

### 3. 電影畫幅排版 (2.39:1 Anamorphic Header)
```tsx
export function CinematicHero() {
  return (
    <section className="relative w-full min-h-screen bg-[#070709] text-white flex flex-col justify-between p-8 md:p-16 overflow-hidden">
      {/* 頂部電影時間碼 / 註釋 */}
      <div className="flex justify-between text-xs tracking-widest text-white/40 uppercase font-mono">
        <span>SCENE 01 // OVERVIEW</span>
        <span>REC [●] 24.00 FPS</span>
      </div>

      {/* 核心巨幕標題 */}
      <div className="max-w-5xl my-auto">
        <p className="text-sm uppercase tracking-[0.3em] text-cyan-400 mb-4 font-mono">NEXT GENERATION PLATFORM</p>
        <h1 className="text-5xl md:text-8xl font-black tracking-tighter uppercase leading-[0.9] text-transparent bg-clip-text bg-gradient-to-b from-white via-white/90 to-white/30">
          The Architecture <br /> of Tomorrow
        </h1>
      </div>

      {/* 底部導引 */}
      <div className="flex justify-between items-end border-t border-white/10 pt-6">
        <p className="text-xs text-white/50 max-w-sm">
          Engineered with uncompromising precision. Experience cinematic fidelity in every pixel.
        </p>
        <button className="min-h-[44px] px-8 py-3 bg-white text-black font-semibold rounded-none tracking-widest uppercase text-xs hover:bg-cyan-400 transition-colors">
          Explore Prototype
        </button>
      </div>
    </section>
  );
}
```

---

## 🚫 電影感反模式 (Cinematic Anti-Patterns)
- ❌ **為了氛圍犧牲字體可讀性**：將內文設為極淡暗灰（對比度低於 4.5:1）。
- ❌ **過多全螢幕 Blur 疊加**：每屏超過 2 個大面積模糊圖層導致手機端掉幀。
- ❌ **無節制自動播放音效**：嚴禁未經用戶點擊直接自動外播背景音效。
