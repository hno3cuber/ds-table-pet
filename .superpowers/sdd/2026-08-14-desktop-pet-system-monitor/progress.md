# SDD ledger â€” plan: docs/superpowers/plans/2026-08-14-desktop-pet-system-monitor.md

## Setup notes
- ç›®å½•é git ä»“åº“ï¼ŒTask 1 å†… `git init`ï¼ˆä¸»å·¥ä½œå°ç›´æ¥å¼€å‘ï¼Œæ—  worktreeï¼›ç”¨æˆ·ä¸»å·¥ä½œå°å³æ­¤ç›®å½•ï¼‰
- æ²™ç›’æ— æ³•è¿è¡Œ bash è¾…åŠ©è„šæœ¬ï¼Œcontroller ç”¨ PowerShell æ‰‹åŠ¨å®Œæˆï¼štask brief æå–ã€review package ç”Ÿæˆ
- æ— å¯ç”¨å­ä»£ç† rosterï¼Œimplementer/reviewer å‡ç”¨ä¼šè¯é»˜è®¤æ¨¡å‹

## Preflight scan (interfaces shared across tasks)
| Task pair | Produces â†’ Consumes | Finding |
|---|---|---|
| T2 â†’ T9/T10 | Config.get/set/save â†’ çª—å£å°ºå¯¸ä½ç½®/æ’ä»¶è£…é… | clean |
| T3 â†’ T7/T9 | scaled_size/scale_from_drag â†’ ActorWidget/PetWindow | clean |
| T4 â†’ T6/T10 | Plugin/PluginManager(factory) â†’ SystemMonitorPlugin(interval_ms)/install_plugins | clean |
| T5 â†’ T6 | CpuGpuCollector â†’ poll() | clean |
| T7 â†’ T9 | ActorWidget(handle_at/set_resize_mode/current_scale) â†’ PetWindow | clean |
| T8 â†’ T9 | HudPanel(add_block/set_scale/fade_in/out/show_paused) â†’ PetWindow | clean |
| T9 â†’ T10 | PetWindow(install_plugin/set_paused/current_pos/current_scale) â†’ main.py | clean |
| T1 â†’ all | conftest qapp fixture â†’ GUI æµ‹è¯• | clean |
- è®¡åˆ’æ–‡æœ¬å†…éƒ¨è‡ªæ´½ï¼ˆæ¯ä»»åŠ¡æµ‹è¯•ä¸å…¶ä»£ç ä¸€è‡´ï¼‰ï¼›æ— å†²çªéœ€è£å®š

## Task log
Task 1: implementer DONE (commits b4a9fb2..b252e5c, root + report) ¡ª 1 passed
  Concerns (observational): 1) pip Ö±½Ó°²×°ÔÚ±¾É³ºĞËÀÂ·£¨PEP 714 metadata ÏÂÔØ±»ÎÄ¼ş¹ıÂË¾Ü£©£¬ÒÑÓÃ PyPI JSON API À­ wheel + --no-index ÀëÏß°²×°ÈÆ¹ı£¬·½°¸¼ÇÂ¼ÔÚ task-1-report.md£»ºóĞøÈÎÎñÈô¼ÓÒÀÀµ±ØĞëÑØÓÃ¡£2) pynvml 13.0.1 Îª¹ı¶É°ü£¬½¨Òé nvidia-ml-py£¨ÒÑ×°£¬Ä£¿éÃûÍ¬Îª pynvml£©£»²»Ó°Ïì±¾ÈÎÎñ£¬Task 5 ÊµÏÖÊ±ÁôÒâ¡£3) pytest »º´æĞ´Èë±»É³ºĞ¾Ü£¬ÎŞº¦¡£4) 5 ¸öÉ³ºĞËøËÀµÄ¿ÕÄ¿Â¼£¬git ²»¸ú×Ù£¬ÎŞº¦¡£
Task 1: review pending
Task 1: review clean (spec ?, Approved; no Critical/Important)
Task 1: minor (deferred): root commit »ìÈë .superpowers/docs/picture£¨brief Ö¸Ê¾ git add -A ËùÖÂ£¬ÊµÏÖÕßÎŞÔğ£»ºóĞø commit ÓÃ¾«×¼ add£©
Task 1: minor (deferred): test_smoke ¶ÏÑÔÆ«ĞÎÊ½£¨brief Ô­ÎÄ£»ºóĞøÈÎÎñ²âÊÔĞèÕæÊµ¶ÏÑÔ£©
Task 1: minor (deferred): .superpowers ÎÄµµÔÚ git diff ÖĞ GBK/UTF-8 ÂÒÂë£¬²»Ó°Ïì½»¸¶Îï
Task 1: minor (deferred): pynvml 13.0.1 ¹ı¶É°ü£¬Task 5 ¾ö²ßÊÇ·ñ»» nvidia-ml-py
Task 1: complete (commits b4a9fb2..b252e5c, review clean)
Task 2: implementer DONE (commits b252e5c..7982ae5: a14111a config + 7982ae5 conftest env patch) ¡ª 4 passed config, 5 passed full
  Concerns: 1) tmp_path É³ºĞ¿ÓÒÑĞŞ¸´£ºconftest patch os.mkdir Ç¿ÖÆ 0o777£¨Windows mode ÎŞÒâÒå£¬µÈÍ¬Æ½Ì¨Ä¬ÈÏ£©£»ºóĞøÈÎÎñÅÜ²âÊÔÑØÓÃ task-2-report ÃüÁîÄ£°å£¨--basetemp ¹¤×÷ÇøÎ¨Ò»Â·¾¶ + -p no:cacheprovider£©¡£2) st_mode ¶ÔÄ¿Â¼ºã±¨ 0o40777 ²»¿ÉĞÅ£¨Õï¶Ï½ÌÑµ£©¡£3) ²ĞÁô 0o700 ¿ÕÄ¿Â¼É¾²»µô£¬ÎŞº¦¡£4) ´úÂëÓë brief Öğ×ÖÒ»ÖÂ¡£
Task 2: review pending
Task 2: review clean (spec ?, Approved)
Task 2: minor (deferred): ºÏ·¨ JSON µ«¶¥²ã·Ç¶ÔÏó£¨Èç [1,2,3]£©Ê± _deep_merge ±À AttributeError£¬²»¶µµ×£¨brief ÊµÏÖÍ¬ÓĞ´Ëµã£¬·Ç¹æ¸ñÆ«²î£»Ò»ĞĞĞŞ¸´ if not isinstance(loaded, dict)£©£»final review triage
Task 2: minor (deferred): set ×²·Ç dict ÖĞ¼ä½Úµã£¨window: 5.0£©Ê± TypeError£»º±¼ûÊäÈë
Task 2: minor (deferred): conftest os.mkdir patch ½ø³Ì¼¶È«¾Ö£»½¨Òé¼Ó"½öÏŞ Windows É³ºĞ"×¢ÊÍ·À Linux CI Îó¶Á£»final review triage
Task 2: minor (deferred): ¶µµ×Â·¾¶£¨¿ÕÎÄ¼ş/Ëğ»µ JSON/get default£©ÎŞ²âÊÔ±£»¤£»¿ÉÑ¡Ïî
Task 2: complete (commits b252e5c..7982ae5, review clean)
Task 3: implementer DONE (commit b19d895) ¡ª 5 passed geometry, 10 passed full
  Concerns (env): python -m pytest ¶ø·Ç pytest Èë¿Ú£»git -C ¹æ±ÜÖĞÎÄÂ·¾¶ cd ¿Ó£»¾«È· add ¹æ±Ü²ĞÁôÄ¿Â¼È¨ÏŞ¾¯¸æ£»LF¡úCRLF ÌáÊ¾ÎŞº¦¡£
Task 3: review pending
Task 3: review clean (spec ?, Approved)
Task 3: minor (deferred): round() ÒøĞĞ¼ÒÉáÈë vs ÖĞÎÄ"ËÄÉáÎåÈë"ÓïÒåÎ´Ëø¶¨£»brief ÊµÏÖÈç´Ë£¬max(1,¡¤) ÎüÊÕ²îÒì£¬Ó°ÏìµÍ
Task 3: minor (deferred): orig_w==0 ³ıÁãÎ´·À»¤£»½çÃæ orig_w À´×Ô ds.png Ô­Ê¼¿í²»Îª 0
Task 3: minor (deferred): Éó²é°ü git log ¶ÎÎª¿Õ£¨´ò°ü²ãÃæ£©£»ÏÂ´ÎÉú³ÉÑéÖ¤
Task 3: complete (commit b19d895, review clean)
Task 4: implementer DONE (commit a4cc2fd) ¡ª 5 passed, 15 full
  Concerns: brief ÎÄ¼ş mojibake£¨×Ó´úÀí°´ GBK Îó¶Á UTF-8£¬ÒÑ»¹Ô­"¼Ù²å¼ş"£©£»brief Step 4 Expected Ğ´ 4 passed ÊµÎª 5 ¸ö²âÊÔ£¨controller ¼Æ»®ÊèÂ©£¬°´´úÂëÖ´ĞĞÎª×¼£©¡£
Task 4: review pending
Task 4: review: spec ?, Approved; 1 Important (non-blocking): spec.loader.exec_module ÎŞÒì³£±£»¤£¬»µ²å¼ş£¨Óï·¨´íÎó£©Ê¹Õû¸ö discover() ±ÀÀ£
Task 4: Ruling: exec_module ¸ôÀë ¡ª finding ³ÉÁ¢£»ËäÎª brief Ô­Ñù´úÂë£¨plan-mandated£©£¬µ« spec Èİ´í¾«Éñ£¨ÑéÊÕÇåµ¥µÚ 8 Ìõ£©Ö§³Ö»µ²å¼ş²»ÍÏ¿åÈ«Ìå£»ĞŞ¸´³É±¾ 3 ĞĞ£¬ÏÖÔÚĞŞÓÅÓÚÁô¸ø Task 6/10£»³É±¾Èô´í£º¶àÒ»ÂÖ fix Ñ­»·
Task 4: minor (deferred): issubclass ¾Ü¾ø·ÖÖ§ÎŞ²âÊÔÊØ»¤£»test_enabled_filter Ä¿Â¼ÃûÓë²å¼ş id Í¬Ãû£¨²âÊÔ¸ôÀëĞÔ£©£»plugins_dir ²»´æÔÚÊ± FileNotFoundError£»Ä£¿éÎ´×¢²á sys.modules ÖØ¸´ discover ÖØÅÜ¸±×÷ÓÃ
Task 4: fix round 1 pending
Task 4: fix round 1/5 (1 addressed, 0 open; commit 3a8b32b; re-review ADDRESSED, no new breakage)
Task 4: complete (commits b19d895..3a8b32b, review clean)
Task 5: implementer DONE (commit 321ac7f) ¡ª 5 passed, 21 full
Task 5: Ruling: stop() Ïß³ÌÒıÓÃ±£Áô vs ÖÃ None ¡ª ¼Æ»®ÄÚ²¿Ã¬¶Ü£¨brief ²âÊÔ¶ÏÑÔ _thread is not None£¬brief ÊµÏÖÖÃ None£¬²»¿ÉÍ¬Ê±³ÉÁ¢£©£»ÊµÏÖÕß°´ TDD ÆõÔ¼ÒÔ²âÊÔÎªÑéÊÕ±ê×¼£¬±£Áô²âÊÔÔ­ÎÄ¡¢ÊµÏÖÈ¥µôÖÃ None£¨¹¦ÄÜµÈ¼Û£ºstart ÒÔ is_alive() ÖØ½¨Ïß³Ì£©£»²Ã¶¨Î¬³Ö´ËÆ«Àë£¬reviewer ÈôÌá³ö¸Ä»Ø brief ÊµÏÖ£¬ÒÔ±¾ Ruling ²µ»Ø£»³É±¾Èô´í£ºÓïÒåÍêÈ«µÈ¼Û£¬ÎŞ·çÏÕ
  Concerns: pynvml FutureWarning£¨ÒÑÖª£¬Task 5 ¾ö²ßµãÈÔÎª"Î¬³Ö pynvml"£©£»PowerShell ÎŞ && ÓÃ ; ´®Áª
Task 5: review pending
Task 5: review clean (spec ?, Approved; no Critical/Important)
Task 5: minor (deferred): report ĞĞÊı±ÊÎó£¨+70/+37 vs Êµ¼Ê 57/50£¬×ÜÊıÅöÇÉÒ»ÖÂ£©£»ÖÕÉóÊ±ÈçË³ÊÖ¿ÉĞŞÕı±¨¸æ
Task 5: minor (deferred): read_gpu ¶èĞÔ init ÎŞËø£¬µ±Ç°µ¥Ïß³Ì¼ÙÉè³ÉÁ¢£»ÈôÎ´À´ GUI Ïß³ÌÇ¿ÖÆË¢ĞÂĞè¼ÓËø»ò×¢ÊÍ
Task 5: complete (commit 321ac7f, review clean)
Task 6: implementer DONE (commit 0d29812) ¡ª 6 passed, 27 full
Task 6: Ruling: panel widget ³ÖÓĞÒıÓÃ ¡ª ¼Æ»®È±Ïİ£¨brief ²âÊÔ¶ªÆú panel(None) ·µ»ØÖµ + brief ÊµÏÖ²»³ÖÓĞ widget ¡ú ¶¥²ã QWidget ±» GC£¬set_paused Å× C++ object already deleted£©£»ÊµÏÖÕß¼Ó self._widget ³ÖÓĞ£¬×îĞ¡ĞŞ¸´Ê¹ brief ×ÔÉí²âÊÔÍ¨¹ı£»²Ã¶¨½ÓÊÜ£»Éú²úÂ·¾¶£¨PetWindow ³ÖÓĞ£©±¾¾Í°²È«£¬´ËĞŞ¸´Ë«±£ÏÕ
  Concerns: set_paused(False) »Ö¸´Ê± QTimer.start(1000) ¹Ì¶¨Öµ£¬·ÇÄ¬ÈÏ interval_ms ¹¹ÔìµÄ²å¼şÔİÍ£»Ö¸´ºóÆ¯ÒÆ£¨brief Ô­ÎÄ£©£»´ı reviewer ÅĞ¶Ï
Task 6: review pending
Task 6: review: spec ?, quality Needs work ¡ª 1 Important: set_paused(False) »Ö¸´Ê± QTimer.start(1000) ¹Ì¶¨Öµ£¬Óë interval_ms ¹«¿ªÆõÔ¼Æ¯ÒÆ£¨Á½ÌõÆô¶¯Â·¾¶ĞĞÎªÃ¬¶Ü£¬¾²Ä¬ÉúĞ§£©£»ĞŞ¸´£ºstart(self.interval_ms)
Task 6: minor (deferred): _PANEL_STYLE È±ÉîÉ«°ëÍ¸Ã÷µ×+Ô²½Ç£¨brief Ä£°åÔ­Ñù£»ÈôÉÏ²ã HUD Í³Ò»´¦Àí¿ÉºöÂÔ£¬Task 8 ºó triage£©
Task 6: minor (deferred): test_pause_shows_paused_state Î´¶ÏÑÔ±êÇ©ÎÄ±¾Óë timer ×´Ì¬£»¿ÉË³ÊÖ²¹
Task 6: fix round 1 pending
Task 6: fix round 1/5 (1 addressed, 0 open; commit daa0e84; re-review ADDRESSED, no new breakage)
Task 6: complete (commits 321ac7f..daa0e84, review clean)
Task 7: implementer DONE (commit 27f026c) ¡ª 5 passed, 32 full
Task 7: Ruling: ActorWidget ¹¹ÔìÊ± resize µ½ pixmap scaled ³ß´ç ¡ª ¼Æ»®È±Ïİ£¨brief ²âÊÔ½Çµã×ø±ê°´ pixmap ³ß´çÉè¼Æ£¬brief ÊµÏÖ²»Éè¼¸ºÎ£¬offscreen Ä¬ÈÏ 640¡Á480 Ê¹ÃüÖĞ²âÊÔ±Ø¹Ò£©£»ÊµÏÖÕß¼ÓÒ»ĞĞ self.resize(*scaled_size(...))£¬²âÊÔÎ´¶¯£»set_scale ÈÔ²» resize ´°¿Ú£¨ÆõÔ¼±£³Ö£©£¬PetWindow layout ½Ó¹ÜÎŞ³åÍ»£»²Ã¶¨½ÓÊÜ
Task 7: review pending
Task 7: review: spec ?, Approved
Task 7: Ruling: I1 paintEvent Ã¿Ö¡·ÖÅäÖĞ¼ä QPixmap£¨Important, ·Ç×è¶Ï, brief Ô­Ñù´úÂë£©¡ª Ôİ»º²»ĞŞ£ºĞŞ¸´ĞèÖØĞ´»æÖÆÂß¼­£¬offscreen ÎŞ·¨ÑéÖ¤ºôÎüËõ·ÅÊÓ¾õĞ§¹û£¬¸Ä´í·çÏÕ>ÊÕÒæ£»µ±Ç° pixmap ³ß´ç¿ªÏúÎ¢Ãë¼¶¿ÉºöÂÔ£»Task 11 Õæ»úÑéÊÕÊ±¹Û²ì£¬¿¨¶ÙÔòĞŞ£»³É±¾Èô´í£ºĞÔÄÜÓÅ»¯ÍÆ³Ù£¬ÎŞ¹¦ÄÜÓ°Ïì
Task 7: minor (deferred): M1 paintEvent ËÀ´úÂë target = self.rect().size() Ò»ĞĞ£»M2 ÊÖ±ú 9px/ÃüÖĞ 13px ²î 1px£¨QRect Ë«µã°üº¬ÓïÒå£¬Öğ×Ö¼Ì³Ğ brief£¬½»»¥ÎŞÓ°Ïì£©£»M3 ²âÊÔ·ÃÎÊË½ÓĞ³ÉÔ±ÇÒÎ´ÕæÑéÖØ»æ£¨brief Ô­ÎÄ£©£»M4 ºôÎüÃªµãÔÚ×óÉÏ·Ç¾ÓÖĞ£¨+2% ÓÒÏÂ±»²Ã£¬cosmetic£¬Õæ»ú¿´Ğ§¹û£©
Task 7: note: ºôÎü¶¯»­ __init__ ÎŞÌõ¼ş start£»Task 9 PetWindow °´ config breathing_animation µ÷ set_breathing ÏÔÊ½¿ØÖÆ£¨¼Æ»®ÄÚÒÑ¸²¸Ç£©
Task 7: complete (commit 27f026c, review clean, 1 Important parked)
Task 8: implementer DONE (commit 829ffb8) ¡ª 4 passed, 36 full
  Adaptations: WA_TranslucentBackground ÓÃ Qt. Ç°×º£¨PySide6 ÎŞÊµÀıÊôĞÔ£©£»¡¸ÒÑÔİÍ£¡¹»¹Ô­ UTF-8£»brief ²âÊÔ count ¶ÏÑÔ 1¡ú2£¨paused ±êÇ©ÔÚÄ©Î²¡¢add_block ²åÆäÇ°£¬½á¹¹ÒÀÀµ£¬ÊµÏÖ±£³Ö brief Ô­ÎÄ£©
Task 8: review pending
Task 8: review clean (spec ?, Approved; no Critical/Important)
Task 8: minor (deferred): Ãæ°å¿É¼ûÊ±¶¯Ì¬ add_block µÄĞÂ¿é³õÊ¼Òş²Ø£¨ÕæÊµÖ÷Á÷³ÌÏÈ¹Ò¿éºóÏÔÊ¾²»ÊÜÓ°Ïì£©£»¼¯³ÉÌáĞÑ£ºPetWindow ¿É¼ûÆÚ¼ä¹Ò¿éĞèÊÖ¶¯ show
Task 8: minor (deferred): show_paused Ç¿Éè¿é¿É¼ûĞÔ£¬¸²¸Ç²å¼ş×ÔÖ÷¿ØÖÆ£¨¹æ¸ñ·¶Î§ÄÚ£©
Task 8: minor (deferred): windowOpacity Îª´°¿Ú¼¶ÊôĞÔ£¬HudPanel µ­Èëµ­³ö¿ÉÄÜÁ¬´ø PetWindow ÕûÁ´Í¸Ã÷¶È£¨½ÇÉ«¸ú×Å±äÍ¸Ã÷£©£»Task 9 ¼¯³ÉÊ±ÑéÖ¤£¬ÈôÓ°Ïì¹Û¸Ğ¸ÄÓÃ QGraphicsOpacityEffect
Task 8: complete (commit 829ffb8, review clean)
Task 9: implementer DONE (commit fe5549f) ¡ª 5 passed, 41 full; offscreen Ã°ÑÌ: 910x941 (ds.png Ô­Ê¼±ÈÀı), ºôÎü Running, HUD Òş²Ø
  Concerns: windowOpacity Á¬´øÍ¸Ã÷¶È£¨°´ÌáĞÑÎ´¸Ä HudPanel£¬Task 10 Õæ»úÆÀ¹À£©£»offscreen ÑéÖ¤²»ÁË½»»¥¹Û¸Ğ£»QCursor Î´Ê¹ÓÃ import£¨brief Ô­ÎÄ£©£»Ëõ·ÅË®Æ½Î»ÒÆ·½Ïò¸Ğ£¨Éè¼ÆÔ¼¶¨£©
Task 9: review pending
Task 9: review: spec ?, quality Needs work ¡ª 1 Critical: Ëõ·ÅÍÏ×§Ê§¿Ø
  Critical ÏêÇé: _apply_resize µÄ drag_dx = globalPosition().x() - self.x() ÊÇ¹â±ê¾à´°¿Ú×óÔµ¾ø¶Ô¾àÀë£¬¶ø scale_from_drag ÆõÔ¼ÊÇÒÆ¶¯ÔöÁ¿£¨test_geometry: scale_from_drag(100,50,1.0)==1.5£©£»°´ÏÂË²¼ä drag_dx ÒÑ=´°¿Ú¿í£¬Ê×´Î move ·­±¶¡¢Ã¿ÏñËØ scale+~1.0 Ö¸ÊıÊ§¿Ø£»±¨¸æ"·ûºÏÆõÔ¼"ÅĞ¶¨´íÎó£»test_window_min_scale Ö±½Óµ÷ _apply_resize(-200) ÈÆ¹ıÕæÊµÊÂ¼şÂ·¾¶ÇÒ -200 ÔÚÕæÊµÂ·¾¶²»¿ÉÄÜ³öÏÖ£¬Ç¯ÖÆ¶ÏÑÔÑÚ¸ÇÁËÊıÑ§´íÎó
  Minor (deferred): Esc ²»ÇåÀíÔÚÍ¾ _drag_offset£¨Ëõ·ÅÄ£Ê½ÍÏ×§ÖĞ°´ Esc ¼«¶ËÇé¿ö£©£»globalPos() ÆúÓÃ API£»QCursor ËÀµ¼Èë£»HUD ĞüÍ£µ­³ö¾ºÕùÓëÊ×´Î fade_in ÎŞĞ§£¨Òş²ØÌ¬ opacity=1.0 ÎŞµ­ÈëĞ§¹û£©£»ÎŞ×î´ó scale ÉÏÏŞ£»Task 10 Õæ»ú¹Û²ì
Task 9: fix round 1 pending
Task 9: fix round 1/5 (1 addressed, 0 open; commit 004ece3; re-review ADDRESSED, no new breakage; ·´Ö¤ÊµÑéÈ·ÈÏ²âÊÔËøËÀÔöÁ¿ÓïÒå)
Task 9: complete (commits 829ffb8..004ece3, review clean)
Task 10: implementer DONE (commit 35aa2ba) ¡ª 4 passed, 46 full; Ã°ÑÌÊµÖ¤·¢ÏÖÆõÔ¼³åÍ»
Task 10: Ruling: ²å¼şµ¼³öÆõÔ¼³åÍ»£¨PluginClass vs SystemMonitorPlugin£©¡ª ¼Æ»®È±Ïİ£ºTask 4 PluginManager Ô¼¶¨Ä£¿éµ¼³ö PluginClass£¨²âÊÔÒÑËø¶¨£©£¬Task 6 ÀàÃû SystemMonitorPlugin£¨spec ÃüÃû£©£¬¼Æ»®²ãÃæÎ´¶ÔÆë£»Ã°ÑÌÊµÖ¤ discover ·µ»Ø¿Õ¡¢HUD ¹Ò²»ÉÏÊı¾İ¿é£»ĞŞ·¨£ºplugins/system_monitor/plugin.py ¼ÓÒ»ĞĞ PluginClass = SystemMonitorPlugin£¨±ğÃû£¬×îĞ¡¡¢Óë¼ÈÓĞ²âÊÔ¼æÈİ£©£¬ÁíÔÚ tests/test_plugins.py ×·¼ÓÕæÊµ²å¼şÄ¿Â¼·¢ÏÖ²âÊÔ£»³É±¾Èô´í£º±ğÃû·½Ê½ÒıÈëË«ÀàÃûÇáÎ¢ÈßÓà£¬µ«ÁãĞĞÎª·çÏÕ
  Also: test_main_loads_pixmap ²¹ qapp ²ÎÊı£¨QPixmap ÎŞ QApplication Ê± fail-fast 0xC0000409£¬ÒÑ×îĞ¡¸´ÏÖ£¬ºÏÀíĞŞÕı£©
Task 10: review pending£¨º¬ÆõÔ¼³åÍ» finding£¬´ı reviewer ¶ÀÁ¢È·ÈÏ£©
Task 10: review: spec ?, Approved; finding ¶ÀÁ¢È·ÈÏ£º²å¼şµ¼³öÆõÔ¼³åÍ» = Critical£¨¶Ô Task 11 ÑéÊÕ£¬µÚ 3/4 ÌõÖ±½ÓÒÀÀµ discover£©£»±ğÃû·½°¸»ñÉó²éÕßÈÏ¿É£¨ÓÅÓÚ¸Ä discover£¬ÆÆ»µÒÑËø¶¨ÆõÔ¼£©£»½¨ÒéÕæÊµ²å¼ş·¢ÏÖ²âÊÔÖ±½Óµ÷ main.install_plugins£¨Í¬Ê±²¹ Important ÌáÊ¾µÄ×°Åäº¯Êıµ¥²âÈ±¿Ú£©
Task 10: Important (deferred after fix): main.install_plugins ±¾ÌåÎŞµ¥²â´¥´ï£¨brief ²âÊÔÄÚÁªÖØĞ´ factory£©£»ÕæÊµ²å¼ş·¢ÏÖ²âÊÔ½«¸²¸Ç
Task 10: minor (deferred): _StateSaver ÎŞ Python ÒıÓÃÁô´æ£¨PySide6 ±£ÁôÒÑ×°¹ıÂËÆ÷ + aboutToQuit ¶µµ×£¬ÎŞÊµ¼Ê·çÏÕ£©£»load_pixmap Ê§°ÜÂ·¾¶ÎŞ¸ºÏò²âÊÔ£»²âÊÔÄÚÎ´Ê¹ÓÃ import£¨brief Ô­ÎÄ£©
Task 10: fix round 1 pending
Task 10: fix round 1/5 (1 addressed, 0 open; commit 994e8f1; re-review ADDRESSED, no new breakage; Ã°ÑÌ¶ÔÕÕ discovered [] ¡ú ['system_monitor'])
Task 10: complete (commits 004ece3..994e8f1, review clean)
Task 11: implementer DONE (commit 352ebb9) ¡ª 54 passed (47 + 7 new regression), exit 0
  Step 3 fixes: 1) pet/config.py _sanitize/_value_ok£º´íÎóÀàĞÍ×Ö¶ÎÖµ£¨scale=abc¡¢pos=oops¡¢interval=-5¡¢enabled=null¡¢¶¥²ã·Ç¶ÔÏó£©°´Ä¬ÈÏÅäÖÃÀàĞÍĞ£Ñé»ØÍË£¨ĞŞ¸´ÑéÊÕµÚ 7 Ìõ·¢ÏÖ£©£»2) collector._update() ¸ø read_gpu ¼Ó try/except£¬Òì³£±ê¼Ç gpu_ok=False Ïß³Ì²»ËÀ£¨ĞŞ¸´ÑéÊÕµÚ 8 Ìõ·¢ÏÖ£©
  ÑéÊÕµÚ 1-6 Ìõ£¨Õæ»ú£©ÈçÊµ±ê×¢´ıÓÃ»§ÑéÊÕ£»µÚ 7/8 ÌõÉ³ºĞÃ°ÑÌ PASS£¨ĞŞ¸´Ç°ÄÃµ½³ÏÊµÊ§°ÜÖ¤¾İ£©
  Note: ¼Æ»®ÎÄµµÕıÎÄ"¶µµ×"ÔøÎó´ò"¶Òµ×"£¬ÒÑË³ÊÖĞŞÕı
Task 11: review pending
Task 11: review clean (spec ?, Approved; 2 Minor: _sanitize dict ·ÖÖ§¶ªÆúÎ´Öª¼ü£¨ĞĞÎª±ä»¯Î´ÅûÂ¶£¬Ó°ÏìĞ¡£©£»pynvml ÔëÒô£©
Task 11: complete (commit 352ebb9, review clean)
ALL TASKS COMPLETE. Final whole-branch review pending.
FINAL REVIEW: verdict No (With fixes) ¡ª 54 passed but two blind spots: µ¥´Î move ÑÚ¸Ç C1 ÀÛ¼ÆÓïÒå£»offscreen ÎŞ·¨äÖÈ¾ÑÚ¸Ç C2 ²Ã¼ô/fade Ê§Ğ§
FINAL C1 (Critical): Ëõ·ÅË«ÖØÀÛ¼Æ ¡ª _apply_resize °ÑÏà¶Ô press ÆğµãµÄ×ÜÎ»ÒÆ drag_dx ¼Óµ½ÒÑ¸üĞÂµÄ self._scale£¨scale_from_drag=current+drag/orig_w£©£¬Á¬Ğø move ·´¸´µş¼ÓÖ¸Êı·Å´ó¡¢»ØÍÏ·´Ïò·Å´ó£»Ì½Õë: move2 ÆÚÍû1.6ÊµµÃ2.1£¬»ØÍÏÆÚÍû1.1ÊµµÃ2.2£»T9 ĞŞ¸´Ö»¸Ä»ù×¼Î´¸Äµş¼ÓÓïÒå£»ĞŞ·¨: press ¼Ç _resize_start_scale£¬_apply_resize ÃİµÈ scale=clamp(start+drag/orig_w)£¬²¹Á½´Î move QTest
FINAL C2 (Critical): HUD ÕûÌåÊ§Ğ§ ¡ª HudPanel ×Ó¿Ø¼şÖÃÓÚ¸¸´°¿Ú±ß½çÍâ£¨x=width+6£©£¬child widget »æÖÆ±»²Ã¼ôµ½¶¥¼¶´°¿ÚÄÚ ¡ú Ò»ÏñËØ»­²»³ö£»windowOpacity ½ö¶¥²ã´°¿ÚÓĞĞ§ ¡ú fade ²»·¢ÉúÇÒ fade_out ºó finished »Øµ÷ hide() ÓÀ²»´¥·¢£¨opacity ²»±ä£©¡ú ÓÀ²»ÏûÊ§£»ĞŞ·¨: HudPanel ¶¥²ã´°¿Ú»¯£¨Qt.Tool|Frameless|StaysOnTop + WA_TranslucentBackground£©£¬PetWindow moveEvent/resizeEvent/showEvent Í¬²½È«¾ÖÎ»ÖÃ£¬¶¥²ãÉÏ fade ÓĞĞ§£»²¹²âÊÔ£¨isWindow/flags/Î»ÖÃ¸úËæ/fade ºó hide£©
FINAL I1 (Important): Æô¶¯ scale Î´Ç¯ 0.3£¨_sanitize Ö»±£Ö¤ >0£¬config scale=0.05 Æô¶¯³ö 45px ´°¿Ú£¬Á½Â·¾¶ÓïÒå²»Ò»ÖÂ£©£»ĞŞ·¨ max(0.3, ...)
FINAL I2 (Important): ÍË³öÁ´Â·ÎŞ stop_all()£¬²å¼ş stop ÓïÒå´ÓÎ´ÔÚÕæÊµÉúÃüÖÜÆÚĞĞÊ¹£»ĞŞ·¨ main() ³ÖÓĞ mgr£¬aboutToQuit Àï mgr.stop_all()
FINAL I3 (Important): enabled ¹ıÂËÔÚ factory ÊµÀı»¯Ö®ºó£¬±»½û²å¼şÒ²±»¹¹Ôì£»ĞŞ·¨ÓÃ plugin_class.id ÏÈ¹ıÂËÔÙ factory
FINAL minors for fix wave: Esc Çå _drag_offset£»globalPos()¡úglobalPosition()£»É¾ QCursor ËÀ import£»load_pixmap ¸ºÏò²âÊÔ£»issubclass ¾Ü¾øÓÃÀı£»£¨¿ÉÑ¡£©.gitignore ²¹²ĞÁôÄ¿Â¼Ä£Ê½
FINAL deferred keep: T2 set ×²·Ç dict£»T3 ÉáÈë/³ıÁã£»T4 ¹ıÂË¸ôÀë/plugins_dir ²»´æÔÚ£»T5 ¶èĞÔ init ×¢ÊÍ£»T7 parked£¨Õæ»ú¹Û²ì£©£»T8 ¶¯Ì¬¹Ò¿é£»T9 ÎŞ×î´óÉÏÏŞ£¨Éè¼Æ 8.3 Ã÷È·£©£»T10 _StateSaver£»T11 Î´Öª¼ü¶ªÆú£»pynvml¡únvidia-ml-py£¨Áã¸Ä¶¯£¬ºóĞø£©
FINAL fix wave: pending (ONE dispatch)
FINAL fix wave re-review: ALL ADDRESSED (2C+3I+minors), 60 passed, ¿ÉºÏÈë
Final: complete. All tasks done. HEAD=b482a2a
