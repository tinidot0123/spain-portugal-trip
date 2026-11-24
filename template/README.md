# 旅行網頁＋票券夾 底板

## 內容
- `site/`：行程網頁（單檔 `index.html` + PWA）。目前內容是 2027 西葡之旅，當作完整範例。
- `vault/build_vault.py`：票券夾 PDF 產生器；`vault.example.json` 是資料格式範例。

## 新旅行：網頁要換哪裡（都在 `site/index.html`）
1. `TRIP_CFG`（約 L828）：年份、儲存鍵前綴、第一天／最後一天（含當地時區偏移）、當地時區與國旗。時區可放 1~3 個，會顯示在右上角時鐘。
2. `<title>`、導覽列品牌字、首頁標題與 `.kicker` 日期、倒數標籤（搜尋「西葡」找殘留）。
3. 資料區塊：`TRIP_START`、`FLIGHTS`、`STAYS`、`MAPQ`（地圖搜尋字，以時間字串為鍵）、`CITY`、`DAYS`（每日行程）、`TAGS`、`DAYLOC`、`TRAVEL`、`PACK`、`BOOK`（待訂）、`RESV`（已訂記錄）。
4. 城市專屬素材：`BANNERS`（各城市橫幅 SVG）、`ROUTES`＋`Q(day,'時間')`（路線地圖）、`WX_DAY`／`WX_LOC`／`WXN`（天氣地點，Open-Meteo）。
5. `manifest.webmanifest` 名稱、icon 三張、`sw.js` 的快取版本 `V`（每趟旅行改名）。
6. 時間鍵要一致：行程項目、`MAPQ` 的鍵、`Q(day,'…')` 三處要同步。
7. 旗標字串：`must`、`booked`、`reserve:`、`plan:`、`pay:`、`ns:`（值不可含逗號）。

## 測試
```
mkdir t && cp site/* t/ && python3 -m http.server 8765 -d t &
```
用 `?now=2027-02-05T15:00:00+00:00`（要帶時區）模擬當地時間，確認右上角時鐘、「行程」跳轉、無 console error；320／360／390px 寬都看一次。

## 票券夾 PDF
```
pip install pillow pypdf playwright --break-system-packages
python3 vault/build_vault.py vault.json 票券夾.pdf
```
- `vault.json`：`title`、`subtitle`、`dates`（日期→城市）、`entries`（日期、時間、標題、`images`: `{path,type}`，type = `qr`／`ticket`／`shot`）。
- 第一頁＝標題＋目錄，點項目跳到票／QR；每頁右上「↑ 目錄」；有書籤；QR／票面排最前；超長截圖自動切段。
- QR 圖務必實際在手機上掃一次。**票券 PDF 與 vault.json、票券圖不要放進公開 repo。**
