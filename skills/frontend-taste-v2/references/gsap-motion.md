---
name: gsap-motion
description: GSAP 3、ScrollTrigger 滾動視差、時間軸編排與 React/Next.js 動態互動設計規範。提供 GPU 加速、React 生命週期 Cleanup 防記憶體洩漏與無障礙降級指引。
---

# gsap-motion: 現代網頁動效與滾動編排引擎

> 專為高品質網頁動效、滾動視差 (ScrollTrigger)、時間軸 (Timeline) 編排與 React/Next.js 互動設計。
> 核心原則：**性能第一 (60fps)、動態有目的 (Motivated Motion)、生命週期安全 (Zero Leaks)、無障礙友善 (A11y)**。

---

## 🎯 When to Use

- 建立滾動驅動視差 (Scroll-Driven / ScrollTrigger) 與 Pin 釘選堆疊。
- 複雜多元素時間軸 (Timeline) 依序揭露 (Staggered Reveals)。
- 磁吸按鈕 (Magnetic Cursor / Physics Hover)。
- 文字逐字/逐行跳動 (SplitText / Kinetic Typography)。
- 頁面過場與 SVG 變形動畫 (MorphSVG / Flip)。

---

## ⚡ 核心技術棧與依賴規範

```bash
# 核心動效依賴
npm install gsap @gsap/react lenis motion
```

- **GSAP 3**: 處理時間軸、ScrollTrigger、Pin 釘選與複雜物理補間。
- **@gsap/react (`useGSAP`)**: 確保在 React 18/19 StrictMode 下自動註冊與清理動畫，杜絕重複觸發與記憶體洩漏。
- **Lenis**: 平滑滾動 (Smooth Scroll)，提供慣性滾動體驗並與 ScrollTrigger 完美同步。
- **Motion (`motion/react`)**: 搭配輕量級組件進入/離開 (AnimatePresence) 與 Layout 動畫。

---

## 🛡️ 4 大工程鐵律 (Critical Performance Guardrails)

### 1. React 生命週期安全清理 (StrictMode Safe)
在 React / Next.js 中，**嚴禁**在裸 `useEffect` 中直接宣告 `gsap.to()` 而未清理。必須使用 `useGSAP` 或 `gsap.context()`：

```tsx
"use client";
import { useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger);

export function HeroScrollSection() {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    // 所有的動畫與 ScrollTrigger 均會在此組件 unmount 時自動 revert()
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: containerRef.current,
        start: "top top",
        end: "+=150%",
        pin: true,
        scrub: 1,
      },
    });

    tl.from(".hero-title", { opacity: 0, y: 50, duration: 1 })
      .from(".hero-card", { scale: 0.8, opacity: 0, stagger: 0.2 }, "-=0.5");
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="min-h-screen relative">
      <h1 className="hero-title text-5xl font-bold tracking-tight">Kinetic Experience</h1>
      <div className="hero-card mt-8 p-6 bg-white/5 border border-white/10 rounded-2xl">...</div>
    </div>
  );
}
```

### 2. GPU 硬體加速 (Hardware Acceleration)
- **只對** `transform` (`x, y, scale, rotation`) 與 `opacity` (或 `autoAlpha`) 進行補間動畫。
- **嚴禁**對 `width`, `height`, `top`, `left`, `margin`, `padding` 進行動畫，避免引發瀏覽器 Reflow (重排)。
- 對密集動畫元素宣告 `will-change: transform, opacity`，並於動畫結束後清除。

### 3. 無障礙降級 (Accessibility & Reduced Motion)
所有動效必須檢測使用者的動態偏好，並於偏好減少動態時自動跳過或降級為淡入：

```tsx
useGSAP(() => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (prefersReducedMotion) {
    gsap.set(".animated-item", { opacity: 1, y: 0 });
    return;
  }

  // 正常動效邏輯
  gsap.from(".animated-item", { opacity: 0, y: 40, duration: 0.8, ease: "power3.out" });
}, { scope: containerRef });
```

### 4. 滾動防抖與 Lenis 平滑滾動整合
整合 Lenis 時，必須將 Lenis 的滾動更新事件綁定至 ScrollTrigger：

```ts
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export function initSmoothScroll() {
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  });

  lenis.on("scroll", ScrollTrigger.update);

  gsap.ticker.add((time) => {
    lenis.raf(time * 1000);
  });

  gsap.ticker.lagSmoothing(0);
  return lenis;
}
```

---

## 🎨 經典動效代碼範本 (Motion Recipes)

### 1. 磁吸懸停 (Magnetic Hover Physics)
```tsx
"use client";
import { useRef } from "react";
import gsap from "gsap";

export function MagneticButton({ children }: { children: React.ReactNode }) {
  const btnRef = useRef<HTMLButtonElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    const { clientX, clientY } = e;
    const { left, top, width, height } = btnRef.current!.getBoundingClientRect();
    const x = (clientX - (left + width / 2)) * 0.35;
    const y = (clientY - (top + height / 2)) * 0.35;

    gsap.to(btnRef.current, { x, y, duration: 0.3, ease: "power2.out" });
  };

  const handleMouseLeave = () => {
    gsap.to(btnRef.current, { x: 0, y: 0, duration: 0.6, ease: "elastic.out(1, 0.3)" });
  };

  return (
    <button
      ref={btnRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="min-h-[44px] px-6 py-3 bg-white text-black font-semibold rounded-full shadow-lg"
    >
      {children}
    </button>
  );
}
```

### 2. 卡片視差層疊 (Sticky Scroll Card Stack)
```tsx
useGSAP(() => {
  const cards = gsap.utils.toArray<HTMLElement>(".stack-card");
  cards.forEach((card, index) => {
    if (index === cards.length - 1) return;
    gsap.to(card, {
      scale: 0.9 - (cards.length - index) * 0.03,
      opacity: 0.4,
      scrollTrigger: {
        trigger: card,
        start: "top top+=100",
        end: "bottom top+=100",
        scrub: true,
      },
    });
  });
}, { scope: containerRef });
```

---

## 🚫 動效反模式 (Anti-Patterns)
- ❌ **無意義的 Loop 晃動**：按鈕無故一直上下跳動（像 2000 年代 Flash 廣告）。
- ❌ **全站無節制 Scrub**：連一般文字段落都綁定 scrub 滾動，導致閱讀困難。
- ❌ **未處理動態加載高度**：圖片異步載入後未執行 `ScrollTrigger.refresh()`，導致觸發點錯位。
