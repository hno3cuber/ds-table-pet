# 妗屽疇 路 绯荤粺鐩戞帶灏忕瀹?瀹炵幇璁″垝

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 鍦?Windows 妗岄潰瀹炵幇涓€鍙€忔槑鑳屾櫙銆佸彲鎷栨嫿銆佸彲 PPT 寮忕缉鏀俱€佹偓鍋滄樉绀?CPU/GPU 鍗犵敤鐜囩殑瑙掕壊妗屽疇锛屼笖鏋舵瀯鎻掍欢鍖栦互渚垮悗缁墿灞曘€?
**Architecture:** 涓夊眰锛歎I 灞傦紙PetWindow/ActorWidget/HudPanel锛夆啋 鎻掍欢灞傦紙PluginManager + SystemMonitorPlugin锛夆啋 閲囬泦灞傦紙CpuGpuCollector 鐙珛绾跨▼锛宲sutil/pynvml锛夈€傛彃浠跺疄鐜?`poll()`锛堟暟鎹揩鐓э級+ `panel()`锛堟偓鍋滈潰鏉挎帶浠讹級涓や釜鎺ュ彛锛屾柊鍔熻兘 = 鏂版彃浠剁洰褰?+ config 鐧昏銆?
**Tech Stack:** Python 3.14.5銆丳ySide6銆乸sutil銆乸ynvml銆乸ytest锛堟祴璇曪紝offscreen 骞冲彴璺?GUI 鍐掔儫锛?
**Spec:** `docs/superpowers/specs/2026-08-14-desktop-pet-system-monitor-design.md`

## Global Constraints

- 骞冲彴锛歐indows 10锛涙樉鍗?NVIDIA GTX 1650锛堜粎 N 鍗?GPU 鐩戞帶锛宲ynvml锛?- 渚濊禆浠呴檺锛歅ySide6銆乸sutil銆乸ynvml銆乸ytest锛坉ev锛?- 涓嶅仛寮€鏈鸿嚜鍚€佷笉鎵撳寘 exe锛涘惎鍔ㄦ柟寮?`python main.py`
- 绐楀彛蹇呴』锛氭棤杈规 + 缃《 + `WA_TranslucentBackground` 鐪熼€忔槑
- 缂╂斁閿佸楂樻瘮锛堟寜 ds.png 鍘熷姣斾緥锛夛紝鏈€灏?30%
- 缂╂斁灏哄涓庣獥鍙ｄ綅缃啓鍏?`config.json`锛岄噸鍚仮澶?- 鍏ㄩ儴 GUI 娴嬭瘯浠?`QT_QPA_PLATFORM=offscreen` 杩愯锛屼笉寮圭湡瀹炵獥鍙?- 姣忎釜浠诲姟缁撴潫鏃惰繍琛屽叾娴嬭瘯骞舵彁浜わ紙git 浠撳簱锛孴ask 1 鍒濆鍖栵級

---

### Task 11: 鍏ㄩ噺楠屾敹涓庢敹灏?
**Files:**
- Modify: `docs/superpowers/plans/2026-08-14-desktop-pet-system-monitor.md`锛堟湰鏂囦欢锛岄獙鏀剁粨鏋滃嬀閫夊悗鏇存柊锛?
**Interfaces:**
- 鏃犳柊鎺ュ彛锛涜繍琛屽畬鏁撮獙鏀舵竻鍗?
- [ ] **Step 1: 鍏ㄩ噺娴嬭瘯**

Run: `pytest`
Expected: 鍏ㄩ儴閫氳繃锛坈onfig 4 + geometry 5 + plugins 5 + collector 5 + system_monitor 6 + actor 5 + hud 4 + window 5 + main 4 = 43 passed锛?
- [ ] **Step 2: 鎸夎璁℃枃妗ｇ 11 鑺傛墽琛?8 鏉￠獙鏀?*

Run: `python main.py` 閫愭潯鏍稿锛?1. 閫忔槑搴曟纭樉绀猴紝鏃犻粦/鐧藉簳鍧?鉁?鉂?2. 鎷栨嫿绉诲姩璺熼殢 鉁?鉂?3. 鎮仠闈㈡澘娣″叆锛孋PU%/GPU% 姣忕鍒锋柊锛岀Щ寮€娣″嚭 鉁?鉂?4. 鍙抽敭鑿滃崟涓夐」榻愬叏锛涙殏鍋滃悗鏁板瓧鍋滄鍒锋柊锛涙仮澶嶇户缁?鉁?鉂?5. 璋冩暣澶у皬锛氳鐐规鍑虹幇锛岄攣姣斾緥缂╂斁锛屾澗鎵嬬敓鏁?鉁?鉂?6. 閲嶅惎鍚庡昂瀵镐笌浣嶇疆淇濇寔 鉁?鉂?7. 鏀瑰潖 config.json 瀛楁鍊煎悗鍚姩涓嶅穿婧冿紝榛樿鍊煎厹搴?鉁?鉂?8. GPU 璇讳笉鍒版椂涓嶅穿婧冿紝鏄剧ず銆孏PU 涓嶅彲鐢ㄣ€嶁渽/鉂岋紙鍙复鏃舵敼 `read_gpu` 鎶涘紓甯搁獙璇侊級

- [ ] **Step 3: 淇楠屾敹涓彂鐜扮殑闂骞堕噸璺戝搴旀祴璇?*

- [ ] **Step 4: 鏈€缁堟彁浜?*

```bash
git add -A
git commit -m "docs: plan completion and acceptance record"
```

