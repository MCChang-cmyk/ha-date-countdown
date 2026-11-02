# Date Countdown 日期倒數

Home Assistant 自訂整合，用於濾心、耗材、保固及保存期限。每個項目可在介面設定，不必另外建立 input_datetime 或 template sensor。

## 透過 HACS 安裝（建議）

1. 在 HA 開啟 HACS，右上角選單選「自訂儲存庫」。
2. 儲存庫輸入：`https://github.com/MCChang-cmyk/ha-date-countdown`。
3. 類型選「整合（Integration）」，新增後搜尋 **Date Countdown** 並下載。
4. 重新啟動 Home Assistant。
5. 前往「設定 → 裝置與服務 → 新增整合」，搜尋 **Date Countdown** 並設定項目。

需要先安裝 [HACS](https://www.hacs.xyz/docs/use/download/download/)。程式會從 GitHub 下載並在你的 HA 本機運作，不需要把濾心資料送到雲端。目前使用預設分支版本，尚未發布正式 release。

## 手動安裝

1. 將本專案的 `custom_components/date_countdown` 整個資料夾複製到 HA 的 `/config/custom_components/date_countdown`。
2. 重新啟動 Home Assistant。
3. 前往「設定 → 裝置與服務 → 新增整合」，搜尋 **Date Countdown**。
4. 輸入名稱、更換日期、使用期限及單位（天／月／年）。
5. 每個濾心重複新增一個整合項目；可在項目的選項中調整期限。

這是供測試的 0.1.0 初版，尚未於實際 HA 執行環境驗證安裝、介面流程或重新啟動；目前已驗證 Python 語法、翻譯 JSON 與日期運算。提供 HACS 自訂儲存庫安裝設定，尚未列入 HACS 預設清單，也不會自動遷移既有 helper。

## 產生的實體

每個項目會歸在一個裝置下：

| 實體 | 用途 |
| --- | --- |
| 更換日期（date） | 可直接在 HA 介面選擇日期 |
| 今天已更換（button） | 將更換日期設成 HA 當地今天，立即重新計算 |
| 剩餘天數（sensor） | 到期日為 0，逾期為負數 |
| 剩餘壽命（sensor） | 0–100%，適合進度條 |
| 到期日期（sensor） | 日期型態 |
| 已到更換日期（binary_sensor） | 到期當天及逾期為開啟，可用於通知自動化 |

日期變更會儲存在 HA 的整合設定中；重新啟動後重新計算。每日依 HA 時區在午夜更新，不需 sensor.date。未來的更換日期也可輸入，剩餘百分比上限為 100%。

月份及年份按日曆計算，月底縮至目標月份最後一天，例如 1/31 加一個月為 2/28，2024/2/29 加一年為 2025/2/28。

**與既有算法的差異：** 2026/9/2 加 24 個月為 2028/9/2，2026/11/2 剩 670 天；固定 730 天算法則為 669 天。若需完全維持原算法，可選「天」並輸入 730。

## 儀表板

不需要 bar-card 就能用內建 Entities 卡顯示與操作。以下所有實體 ID 都是範例，請在裝置頁查看並換成實際 ID（名稱及介面語系會影響產生的 ID）。

```yaml
type: entities
title: 後置濾心
entities:
  - entity: sensor.filter_post_days_remaining
  - entity: sensor.filter_post_remaining_percentage
  - entity: sensor.filter_post_due_date
  - entity: date.filter_post_start_date
  - entity: button.filter_post_replace_today
```

若已安裝 [bar-card](https://github.com/custom-cards/bar-card)，使用剩餘百分比即可統一最大值，不必為每個濾心維護不同天數上限：

```yaml
type: custom:bar-card
title: 濾心壽命
min: 0
max: 100
entities:
  - entity: sensor.filter_post_remaining_percentage
    name: 後置濾心
severity:
  - from: 0
    to: 10
    color: "#e53935"
  - from: 10.1
    to: 25
    color: "#fb8c00"
  - from: 25.1
    to: 100
    color: "#03a9f4"
```

此範例顯示百分比；若要與截圖一樣同時呈現進度條及剩餘天數，需要另行配置卡片。整合目前不包含自訂前端卡片。

## 從現有設定移轉

1. 保留原有 helper 與範本，先新增一個 Date Countdown 項目。
2. 將原 input_datetime 的日期填入更換日期，依需求選擇日曆月或固定天數。
3. 確認新實體計算符合預期後，更新儀表板及自動化使用的實體。
4. 最後再自行刪除不再使用的舊 helper／範本。此整合不會修改它們。

## 本地驗證

```sh
python3 -m unittest discover -s tests -v
```

日期計算測試不依賴 Home Assistant。實際整合仍需在測試用 HA 驗證新增多個項目、修改日期／選項、按鈕更新、午夜更新、卸載及重啟持久化。

實作參照 [HA Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)、[Options Flow](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) 與 [Date Entity](https://github.com/home-assistant/core/blob/dev/homeassistant/components/date/__init__.py)。
