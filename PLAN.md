# 金庸群俠傳 2 / 3 重製專案計畫（已核准，執行中）

> 起始決議（Q1–Q14）：包裝路線 / 雙 exe + 共用 save / Ruffle 主 + Projector 逃生 /
> 行為一致即還原 / 存檔格式調查後凍結 / 先出 PLAN.md。
> 下方為實測後更新，與初版不同處以此版為準。
> 遠端：https://github.com/lantieslin/jy23-remake（main；含包＋PLAN，不含存檔進度）。

## 1. 背景與目標（不變）

- 原作：半瓶神仙醋 Flash 小遊戲，全 SWF v8（AS2 時代，對 Ruffle 最友善）。
- jy2：單一 `金庸群俠傳2.swf`（24MB，CWS v8）。
- jy3：資產來源 **`jyqxzzjb_1840`（金庸群侠传3终极无敌版，自含 `root.swf`）**：
  `CG/map/UI/war/play/root.swf` + `skill/*.swf`×199 + `sound/*.swf`×55。
  官方入口為 `play.htm`→`play.swf`（640×480）。舊目錄「金庸群俠傳3」
  （加強版1.1，缺 root.swf）**已廢棄**，僅留當對照（其 CG/map/play/war
  與新包位元組相同，UI.swf 不同）。`Maxthon/`、`.url/.ico/.ini/loading*.gif`
  為發行站雜物，不進包。
- 目標：兩個 Windows 執行檔，內容完全還原（不改劇情、不改素材），jy3 開局可讀
  jy2 存檔繼承（自實現轉換橋，見 §6）。

## 2. 範圍

做：雙 exe 可攜包、共用 `./save/`、存檔橋接、jy2/jy3 修改器（CLI＋tkinter GUI）、
Python 工具 exe 化、jy3 字體克隆（本機 MS 版→發布 OFL 版）。
不做：重寫引擎、修劇情 bug、重繪素材、逐幀還原；第一階段無安裝程式、無 32-bit/XP。

## 3. 技術底座（M0 實測結論）

- 主力：**Ruffle desktop 0.7.1**（已驗：jy2 可玩可存；jy3 新包雙入口可進，
  包內 `jy3.bat` 可進）。
- 逃生門：**原 `jy3.exe` / Adobe Projector 32 SA**（T1 證實原 exe 在 Win10/11 跑得
  好好的；Ruffle 若再卡關，jy3 整包切 projector，不燒時間）。
- 引擎更新政策：**不做啟動時自動檢查更新**（pin 0.7.1 已驗；nightly 會回歸、
  自動換引擎等於每次開獎；且與「斷網玩」建議衝突；自動下載 exe 還要補簽章驗證，
  成本不成比例）。改版時機只看上游是否修了本專案卡點（如 IME #1778），
  屆時手動換引擎＋全回歸＋重 pin。手動更新法寫進遊戲說明（換
  `resource/engine/ruffle.exe` 即可）。
- 不用：Lightspark/Gnash（死）、Electron+PPAPI（死）、Haxe 重寫（月級）。
- 跨平台預留（Q10/Q12）：啟動器只用 Ruffle 設定 + 可攜目錄；轉接器/修改器只用
  Python 3（stdlib only，打包 exe 後使用者免裝 Python）。`--save-directory` 堪用；
  `--base` 已證實有害（坑#6），禁用。
- 舊 `jy3.exe`：Q9 原決議廢棄→**修正為保留當逃生門**，不進主包。
- exe 化：Python 工具以 PyInstaller 打包（GUI 用 windowed，CLI 用 console）。

## 4. 已知坑與解法（實測）

| # | 現象 | 根因 | 解法/狀態 |
|---|---|---|---|
| 1 | jy3 `play.swf` 曾卡 5/6 | 舊包（加強版1.1）天生缺 `root.swf`；`play.swf`實為官方正門（新包 `play.htm` 指認），缺檔時 Ruffle 乾等（另會去讀檔名叫 `0` 的檔，原 projector 靜默略過） | 新包（終極無敵版）自含 `root.swf`，此坑隨換包消失；已解決 |
| 2 | jy3 部分中文消失／只剩半形 | Ruffle 查設備字體精確比對，不認 `_GB2312`；`楷体_GB2312`/`仿宋_GB2312`無映射→fallback 到內嵌拉丁字（官方 issue #1616 同機制）；宋體有對上 SimSun 所以部分正常 | 改名克隆字體（族名=`楷体_GB2312`/`仿宋_GB2312`）；灰版測試通過，使用者驗收「字體問題已解決」 |
| 6 | `jy3.bat` 卡 1/6，拖曳同檔可跑 | `--base "%~dp0assets\jy3"` 是反斜線無 scheme 路徑，Ruffle 判為非法 base（cannot-be-a-base），子 SWF 相對載入全滅；jy2 單檔不受影響故沒爆 | 拿掉 `--base`（Ruffle 預設按影片 URL 解析相對路徑即可）；bat/sh 四檔已改，包內重驗可進 |
| 3 | rufflefonts4.swf（網站解法）桌機無用 | 那是 Ruffle **網頁版** `fontSources`+`defaultFonts` 機制；桌機源碼+CLI 雙重確認無此選項 | 桌機走克隆字體（等價）；結案 |
| 4 | jy2 中文打不出＋貼不上 | Ruffle 上游 issue #1778；桌機 `[ime] enabled=true` 已建，待測 | 待驗；不通就走修改器改名（GUI 已支援） |
| 5 | 字體授權 | 本機克隆源自微軟標楷體/正黑＋灰版測試字，不可散佈 | 發布用 OFL：楷體=方正楷体GBK改名（已備，22024字零缺字），仿宋=思源宋體(Noto Serif TC)改名；M5 一併做**子集化**（遊戲用字＋GB2312覆蓋，fonttools，保 hinting）後再改名；灰版不進包 |
| 7 | GUI 讀到舊存檔（`ss`） | jy2 GUI 只掃舊目錄，包內新存檔（林可/笑哈哈）看不見 | 改為**只讀包內固定位**（CLI＋GUI 同步）；已解決 |

## 5. 目錄結構（M5 新版，待批准）

```
jy23-remake/（根：5 檔＋3 資料夾）
  金庸群俠傳2.exe / 金庸群俠傳3.exe      # PyInstaller 小啟動器→resource/engine
  金庸群俠傳2修改器.exe / 金庸群俠傳3修改器.exe  # tkinter GUI（原 jy2/jy3-trainer）
  遊戲說明.txt                            # 玩法/修改器/字體/來源感謝
  fonts/                                  # 待安裝字體（OFL 可散佈版）
  save/                                   # 共用存檔（出貨為空架構；舊存檔遷移見 §8）
  resource/                               # 其餘：
    engine/ruffle.exe (+LICENSE)          # Ruffle 0.7.1
    assets/jy2/jy2.swf                    # 原樣
    assets/jy3/CG/map/UI/war/root/play.swf skill/ sound/  # 新包原樣
    tools/                                # CLI exe＋.py 源碼＋.sh(Phase2)
    fonts-ofl/                            # 發布軌字體源（kaiti_ofl＋待補仿宋OFL）
```
workspace: PLAN.md, tools/*.py(源碼), fonts/(克隆源+OFL備用),
jy23-remake.zip(交付物), *.rar/zip/swf(原始備份)。M5 前包內為舊結構（bat+engine直放）。

## 6. 存檔與修改器（實測規格）

- 包內存檔根：`jy23-remake/save/`（`--save-directory` 統一）；jy2 三槽
  `gamezly/gamelzy/gameylz.sol`（深層 `jy2.swf/` 下，工具用檔名掃，不怕深）；
  jy2 工具**只讀包內固定位**，舊目錄不再看。
- 存檔後須**退出遊戲**才寫檔（原機制）。
- `tools/trainer.py`（CLI）：`list/get/set/setname/diff`，224 鍵；回讀驗證+自動 `.bak`。
- `tools/gui_jy2.py`（tkinter 四頁籤）：基本（明文改名）/屬性（中英對照）/
  武功（中文下拉＋rrr）/開關（aaa）；存檔兩地→固定位修過；實機讀真檔自測。
- `tools/amf.py`（共用嵌套 AMF0 引擎）＋`tools/jy3ref.py`（m/物品335/武功/NPC247 對照表）。
- `tools/trainer3.py`（CLI）＋`tools/gui_jy3.py`（tkinter 六頁籤＋繼承區）：
  基本/屬性(m.14-37)/武功（系別中文下拉）/物品/經脈（全通＋0-199 下拉逐條）/
  隊友；`m.50` 數字→文字自動換型；`m.3` 經驗封頂字串自動轉型。
- `tools/sav_bridge.py inherit`（用戶核定原版規則）：基礎+10/+5/+1000、
  武功經驗+35（只加已存在）、龜息功134（入 u，x.134=1）、武器（木劍/菜刀/
  木棍/飛鏢100）、皮甲；預覽預設，`--yes` 寫入；**遊戲內四項全驗過**。
- `aaa`=左右互搏開關（slot2→slot3 差分定位）**待 T2 遊戲內驗證**。
- jy3 本體 `JY1.sol`（`/ `共享路徑，Ruffle 通用）；`JYbik*.sol` 小開關不管。
- 繼承 verdict（靜態實錘）：離線版從無讀 jy2 代碼（新包＋舊 exe 皆無 `gamezly`；
  UI `inherit` 是 StyleManager 假陽性），橋為數值轉換自實現；不設破關限制
  （標記不可考，文檔註明差異）。

## 7. 里程碑

- M0 調查：**完成**。M1 打包：**完成**（包結構自檢 ALL-OK；包內 bat 可進遊戲）。
- M2 繼承＋修改器：CLI×2、GUI×2、橋**全部完成**；橋已遊戲內四項驗收；
  待 T1（改名讀檔）/T2（`aaa`）/T3（血量）＋IME 測試。
- M3 GUI：**完成**（實機讀真檔＋中文標籤＋固定存檔位，包內同步）。
- M4 exe 化：**完成**（PyInstaller 6.22：`jy2/jy3-trainer.exe` windowed、
  `jy2/jy3-cli.exe`＋`jy23-bridge.exe` console；frozen 路徑、CLI 回傳碼、
  GUI 常駐三項皆驗；`jy23-remake.zip` 125MB 已產出；.py 留包內除錯用）。
- M5 結構重組＋中文 exe 名＋②子集化＋UPX：**完成**（5 檔＋3 資料夾；
  7 exe 全重編＋重驗；仿宋 OFL 改方正仿宋简体；子集 8141 字，
  26MB→7.5MB，cmap 機械驗證零回歸；UPX 對 onefile 僅 2.5% 且削弱 CFG＋
  惹防毒，已還原棄用；舊存檔已遷移；zip 127MB）。
  UPX/Rust/共享運行時結論：onefile 自帶 zlib，UPX 無效；Rust 最多再省 25MB
  全在工具層（斟酌中，未動）；onedir 共享運行時與根目錄結構衝突，未用。
- Phase 2（另案）：macOS/ARM-Windows/Linux。

## 8. 風險

- 版本線變更：jy3 加強版1.1→終極無敵版；繼承規則按用戶核定版實作，
  與原版體感差異已文檔註明（README＋橋說明）。
- 灰版測試字體**不可進發布包**；仿宋 OFL 待補（發布前）。
- Ruffle 小字 thin 是渲染器特性；`Allowscale`/tag 253 為已知無害日誌。
- `aaa` 若 T2 證偽，重做差分定位。bridge 只對新開局用一次（重複疊加，有備份）。
- 包搬家：存檔深層路徑含絕對路徑，整包搬可攜，零散拷存檔會孤兒化。
- M5 重組會改變素材路徑（assets/→resource/assets/），舊命名空間存檔失效；
  遷移方式：JY1.sol（根路徑，無影響）不動；jy2 三槽＋JYbik* 按新路徑拷貝。
  使用者舊進度由腳本自動搬，不手動。

## 9. 驗收清單

- [x] jy2 Ruffle 能開、能玩到存檔；包內 bat 存檔寫入 `save/`
- [x] jy3 新包雙入口＋包內 bat 可進遊戲；中文顯示正常（克隆字體，使用者驗收通過）
- [x] jy3 繼承橋遊戲內四項驗收（屬性/武功經驗95/龜息功/武器皮甲/金錢1050）
- [ ] T1 改名讀檔 / T2 `aaa` / T3 血量 / IME 中文輸入測試
- [x] exe 化後雙擊即用（5 exe 全驗：CLI 回傳碼/GUI 常駐/frozen 存檔路徑）
- [x] M5 新結構＋中文 exe＋子集化（7 exe 重編全驗；UPX 棄用見 §7）
- [ ] 使用者關鍵路徑真人遊玩無卡關級 bug
