# 🐘 PHP 8.4+ & Laravel 13+ 專用架構與編碼規範

> 本分冊為動態按需載入規則。當專案包含 `composer.json` 或涉及 Laravel / PHP 開發時載入。

---

## 1. 核心鐵律與靜態門禁 (Level 0.5 Local Guard)

- **`declare(strict_types=1);`**：每個 PHP 檔案頂部第一行強制宣告，嚴禁遺漏。
- **Eloquent Property Shadowing Guard**：
  - 嚴禁在 Eloquent Model 直接宣告與資料庫欄位同名的類別屬性（例如 `public private(set) string $title;`）。
  - 這會遮蔽 Eloquent 動態屬性注水 (`$attributes`)、Dirty 追蹤與關聯。
  - Asymmetric Visibility (`public private(set)`) 僅可用於 DTO、Value Object 或 Action。
  - Model 欄位一律使用 PHPDoc `@property` 註解。
- **Eloquent Casts 方法宣告**：
  - Laravel 13 強制採用方法宣告 `protected function casts(): array { return [...]; }`，嚴禁使用舊版 `$casts` 屬性。
- **Mass Assignment 資安防護**：
  - 嚴禁使用 `protected $guarded = [];` 開放全欄位寫入。
  - 強制使用 `protected $fillable = [...]` 明確宣告白名單。
- **Thin Controller, Fat Action**：
  - Controller 嚴禁超過 120 行，且不得包含裸 DB 查詢 (`DB::table / whereHas / join`)。
  - 所有商業邏輯與複雜查詢抽離至 `app/Actions/` 下的 Invokable Action 或 Service。

---

## 2. PHP 8.4 現代特性標準

- 使用 Property Hooks 處理欄位虛擬計算與存取攔截。
- 使用 Backed Enums 取代字串常數與 Magic Numbers。
- 覆寫方法強制標記 `#[\Override]`。
- 測試採用 Pest PHP 3+，搭配 `RefreshDatabase` 與 `Http::fake()`。
