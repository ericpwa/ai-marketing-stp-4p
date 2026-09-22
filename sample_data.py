"""
預設案例與示範資料模組 (Sample Data & Presets)
符合教學規格規範，提供「協作台 B2B SaaS 平台」與「微光精品冷萃咖啡」兩組完整案例。
"""

SAMPLE_CASES = {
    "collaboration_hub": {
        "case": {
            "id": "CASE-SIM-01",
            "workspace_id": "G01",
            "name": "「協作台」跨部門專案協同平台",
            "is_simulated": True,
            "analysis_unit": "enterprise",
            "scope": "中型成長型企業之跨部門協同與知識管理市場",
            "material_version": "stage05_v1"
        },
        "persona": {
            "id": "PER-01",
            "name": "張經理 David Chang",
            "work_role": "營運總監 / 專案 PM 主管",
            "context": "管理 50-100 人跨職能團隊，目前使用散落的通訊軟體與試算表追蹤進度，跨部門資訊脫節嚴重。",
            "needs": [
                "自動化追蹤跨部門專案里程碑與阻礙",
                "降低每週重複彙整進度會議的時間成本",
                "建立可溯源的決策紀錄與交接知識庫"
            ],
            "current_practice": "每週耗時 4 小時手動向各部門要 Excel 更新，並在 Slack 與 LINE 零散溝通催件。",
            "users": ["各部門專案成員", "基層專案經理", "協作工程師"],
            "influencers": ["IT 資安主管", "財務主管"],
            "decision_makers": "營運副總 / 執行長",
            "purchase_constraints": [
                "單一專案工具預算需在每月 5 萬元以內",
                "必須通過基本資料安全與權限隔離審查",
                "導入週期不得超過 2 週以免影響現有專案排程"
            ],
            "source_ids": ["SRC-01", "SRC-02"],
            "not_generalizable": "此 Persona 僅代表 50-200 人規模的成長型軟體/數位科技企業，不涵蓋製造業傳統產線。",
            "gaps": ["尚不清楚實際採購審核流程是否需要法務簽核"],
            "unmapped_fields": {}
        },
        "segments": [
            {
                "id": "S1",
                "name": "遠距混合型軟體新創 (30-80人)",
                "dimension": "團隊工作型態與數位成熟度",
                "inclusion": "全員遠距或每週 2 天以上遠距辦公、使用 Slack/GitHub、扁平化決策。",
                "exclusion": "傳統非數位行業、外包派遣公司。",
                "needs_context": "團隊分處不同時區與地點，非同步溝通與透明進度看板為剛性需求。",
                "buying_roles": "CTO 或 COO 兼具直接採購權，決策週期 1-2 週。",
                "contact_path": "Product Hunt、Twitter/X 科技社群、線上試用自主轉化。",
                "source_ids": ["SRC-01"],
                "claim_ids": ["CLM-01"],
                "overlap_gaps": "與 S2 在 50 人左右規模可能有部分重疊，但 S1 重視非同步協作。"
            },
            {
                "id": "S2",
                "name": "轉型中電商品牌團隊 (50-150人)",
                "dimension": "跨部門業務複雜度與活動節奏",
                "inclusion": "行銷、營運、客服、倉儲多部門協同，檔期活動頻繁。",
                "exclusion": "單一店面傳統零售商。",
                "needs_context": "雙11等大促檔期跨部門工作交接常掉球，極需跨組依賴關係自動提醒。",
                "buying_roles": "營運總監發起，需經總經理批准，採購週期約 1 個月。",
                "contact_path": "電商產業年會、專業顧問推薦、專屬業務拜訪展示。",
                "source_ids": ["SRC-02"],
                "claim_ids": ["CLM-02"],
                "overlap_gaps": "對客製化需求較高，導入成本若過高容易延遲驗證。"
            },
            {
                "id": "S3",
                "name": "專業顧問與品牌行銷代操代理商 (20-60人)",
                "dimension": "多客戶並行專案管理需求",
                "inclusion": "同仁同時負擔 3-5 個不同客戶專案，需要對外客戶透明視圖。",
                "exclusion": "無對外專案協作需求的單一企業內部單位。",
                "needs_context": "需向外部甲方客戶展示進度，同時保證不同客戶間資料絕對隔離。",
                "buying_roles": "執行長或創辦人直接裁定，在意是否能提升客戶專業形象。",
                "contact_path": "業界口碑介紹、代理商同業社群、官網案例研究下載。",
                "source_ids": ["SRC-03"],
                "claim_ids": ["CLM-03"],
                "overlap_gaps": "價格敏感度稍高，偏好按專案計費或客戶席位計費模式。"
            }
        ],
        "criteria": [
            {
                "id": "C1",
                "name": "市場規模與成長潛力",
                "standard": "該客群企業數量、成長率及年度付費意願上限",
                "weight": 30.0,
                "weight_reason": "確保產品進入之市場有足夠營收空間以支撐長期運營。"
            },
            {
                "id": "C2",
                "name": "痛點急迫性與不可替代性",
                "standard": "現有解法痛苦指數，是否每週發生且急需解方",
                "weight": 25.0,
                "weight_reason": "痛點不痛則付費意願薄弱，導入意願低。"
            },
            {
                "id": "C3",
                "name": "競爭優勢與進入門檻",
                "standard": "對抗通用工具（如 Notion, Trello, Jira）的特色差異門檻",
                "weight": 25.0,
                "weight_reason": "通用工具競爭激烈，必須有針對特定場景的不可替代殺手級功能。"
            },
            {
                "id": "C4",
                "name": "獲客難易度與接觸成本",
                "standard": "客群聚集程度、決策鏈長度與銷售週期",
                "weight": 20.0,
                "weight_reason": "初期資源有限，長銷售週期容易耗盡團隊早期現金流。"
            }
        ],
        "ratings": [
            {"segment_id": "S1", "criterion_id": "C1", "score": 4, "reason": "遠距新創數量穩定增長，但單一公司人頭數擴張較受限", "source_ids": ["SRC-01"]},
            {"segment_id": "S1", "criterion_id": "C2", "score": 5, "reason": "非同步協作是日常生死關鍵，痛點極為急迫", "source_ids": ["SRC-01"]},
            {"segment_id": "S1", "criterion_id": "C3", "score": 3, "reason": "市場有 ClickUp 與 Linear 等強大既有競品，競爭激烈", "source_ids": ["SRC-01"]},
            {"segment_id": "S1", "criterion_id": "C4", "score": 5, "reason": "科技社群傳播極快，線上自助試用轉換率高", "source_ids": ["SRC-01"]},

            {"segment_id": "S2", "criterion_id": "C1", "score": 5, "reason": "電商企業營收大，且隨著品牌出海預算充足", "source_ids": ["SRC-02"]},
            {"segment_id": "S2", "criterion_id": "C2", "score": 4, "reason": "檔期專案繁多掉球代價極高，但平時依賴既有溝通習慣", "source_ids": ["SRC-02"]},
            {"segment_id": "S2", "criterion_id": "C3", "score": 4, "reason": "通用工具缺乏電商檔期範本與行銷專案特定整合，我方具客製優勢", "source_ids": ["SRC-02"]},
            {"segment_id": "S2", "criterion_id": "C4", "score": 3, "reason": "傳統電商老闆需要業務親訪與展示，銷售週期約 3-6 週", "source_ids": ["SRC-02"]},

            {"segment_id": "S3", "criterion_id": "C1", "score": 3, "reason": "代理商多為中小微型，付費總額相對有限", "source_ids": ["SRC-03"]},
            {"segment_id": "S3", "criterion_id": "C2", "score": 4, "reason": "向客戶交代進度與產出的專業形象非常關鍵", "source_ids": ["SRC-03"]},
            {"segment_id": "S3", "criterion_id": "C3", "score": 4, "reason": "具備「客戶專用視角與安全隔離」能打中代理商心坎", "source_ids": ["SRC-03"]},
            {"segment_id": "S3", "criterion_id": "C4", "score": 4, "reason": "代理商同業圈小，口碑與作品推薦傳播效益高", "source_ids": ["SRC-03"]}
        ],
        "target_decision": {
            "id": "TGT-01",
            "selected_segment_id": "S1",
            "mode": "complete",
            "reason": "S1 遠距混合型軟體新創在獲客容易度 (Score 5) 與痛點急迫度 (Score 5) 均為最高分，能以最低獲客成本快速驗證產品核心價值並累積早期鐵粉。",
            "tradeoffs": "放棄 S2 電商客群較高的單客付費上限，優先爭取 S1 的快速回饋與產品迭代速度。",
            "change_condition": "若 3 個月內遠距新創付費轉換率低於 3%，或自然增長停滯，則轉向洽談 S2 電商品牌之年約方案。",
            "next_check": "首月上線 Product Hunt 觀察自發性註冊數與第 14 天團隊活躍留存率。",
            "human_confirmed": True,
            "claim_ids": ["CLM-04"],
            "ranking": [
                {"segment_id": "S1", "segment_name": "遠距混合型軟體新創", "weighted_score": 4.25, "rank": 1},
                {"segment_id": "S2", "segment_name": "轉型中電商品牌團隊", "weighted_score": 4.10, "rank": 2},
                {"segment_id": "S3", "segment_name": "專業顧問與品牌行銷代操代理商", "weighted_score": 3.70, "rank": 3}
            ]
        },
        "positioning": {
            "id": "POS-01",
            "segment_id": "S1",
            "need": "跨時區非同步協同、減少無效進度會議並自動化彙總里程碑",
            "product_name": "協作台 SyncDeck",
            "value": "以 AI 自動統整專案上下文與非同步待辦，讓工程與商務無縫同步，省下每週 60% 進度彙報時間",
            "statement": "對於追求高效率運作的遠距軟體新創團隊（目標客群），面臨非同步跨部門協同資訊斷層與冗長會議（核心痛點），「協作台 SyncDeck」是一款專為數位團隊設計的 AI 智能專案協同與決策追蹤平台（產品類別）。不同於通用型專案工具（Asana/Notion）缺乏主動脈絡整理，我們提供即時 AI 自動生成進度摘要與跨部門阻礙自動預警（核心差異化優勢），讓團隊隨時掌握全貌且決策可追溯。",
            "alternatives": [
                {
                    "id": "ALT-01",
                    "name": "Notion / Trello 通用型筆記看板",
                    "same_need_solution": "團隊各自開頁面記錄進度與卡片看板",
                    "proposed_difference": "通用工具需要大量人工手動維護頁面連結與狀態，SyncDeck 透過 AI 主動從日常動態提取進度，免除維護負擔",
                    "source_ids": ["SRC-01"],
                    "claim_id": "CLM-05",
                    "to_verify": "使用者是否真的願意停止手動整理 Notion 而信任 AI 的自動彙整"
                },
                {
                    "id": "ALT-02",
                    "name": "每日 Standup 線上開會催進度",
                    "same_need_solution": "每天早上召集 30 分鐘 Zoom 會議逐一報告",
                    "proposed_difference": "耗費全員專注時間與跨時區負擔，SyncDeck 提供全非同步簽到與智慧彙整，節省 80% 開會時間",
                    "source_ids": ["SRC-01"],
                    "claim_id": "CLM-05",
                    "to_verify": "團隊主管在沒有開口面對面時，對專案掌控度是否感到安心"
                }
            ],
            "claim_ids": ["CLM-05"],
            "human_confirmed": True,
            "needs_review": False
        },
        "marketing_4p": {
            "product": {
                "core_features": "AI 非同步進度脈絡自動生成、Git & Slack 雙向智能同步、跨部門依賴看板、決策可溯源台帳。",
                "packaging_spec": "雲端 SaaS Web 應用，支援桌面瀏覽器、行動端閱讀、Slack Bot 機器人整合。",
                "brand_tone": "專業敏捷、俐落科技感、值得信賴、注重工程師與 PM 的心智負擔。",
                "usp": "市面上唯一「免手動填報」就能主動彙整跨部門進度與阻礙的 AI 專案助手。"
            },
            "price": {
                "pricing_model": "Freemium 免費增值制 + 席位訂閱制 (Per Seat / Month)",
                "price_tier": "Starter: 5人以內免費；Pro: 每人每月 $12 美元；Business: 每人每月 $24 美元 (含 AI 進階分析)。",
                "discount_strategy": "年繳享受 8 折優惠；開放新創加速器（如 AppWorks / YC）團隊前 6 個月半價支援。",
                "value_anchor": "相較於每週因無效溝通浪費每位工程師 3 小時工時 (價值超過 $150 美元)，每月僅需花費 $12 美元。"
            },
            "place": {
                "channels": "官方網站線上即開即用、Slack App Directory、GitHub Marketplace、Google Workspace Marketplace。",
                "onboarding_path": "Google/GitHub 一鍵註冊 -> 3 分鐘引導匯入專案範本 -> 自動邀請團隊成員試用。",
                "partnerships": "與遠距社群（如 Remote Taiwan、Nomad List）、雲端開發工具進行技術同盟與聯名推廣。"
            },
            "promotion": {
                "slogan": "「少開一次無效會議，多寫十行漂亮程式」—— 協作台 SyncDeck",
                "content_strategy": "在 Medium 與 X 發表「遠距團隊非同步協作指南」與「50人軟體團隊如何消滅週會」實戰深度文章。",
                "growth_hooks": "「進度週報一鍵產出」免費線上生成工具，免註冊即可體驗 AI 整理效益，結尾導流回產品。",
                "community": "建立 Discord 敏捷專案管理交流社群，定期舉辦非同步管理線上工作坊。"
            }
        },
        "bmc_summary": {
            "target_segment_id": "S1",
            "target_decision_id": "TGT-01",
            "customer_segments": "30-80 人遠距混合型軟體新創之營運主管 (COO) 與工程主管 (CTO)",
            "positioning_claim_id": "CLM-05",
            "value_proposition": "免去手動維護負擔的 AI 智能非同步專案彙整與決策溯源平台，節省 60% 開會時間",
            "other_impacts": "需高度整合 Slack/GitHub API 作為核心關鍵夥伴；主要成本結構為雲端運算與 LLM API 推論支出。",
            "needs_review": False
        },
        "verification_actions": [
            {
                "id": "VER-01",
                "priority": 1,
                "claim_id": "CLM-05",
                "decision_impact": "若非同步 AI 整理無法取得主管信任，則需增加半手動審核與標註介面",
                "method": "針對 10 位遠距新創 PM 主管進行 1 對 1 深度訪談與原型概念點擊測試",
                "audience": "30-80 人遠距軟體新創之 PM / 營運主管",
                "data_to_collect": "主管對 AI 摘要的準確度滿意分數 (1-5) 與願用意願",
                "threshold": "80% 以上受訪主管評分達 4 分以上，且願意導入自身團隊試用",
                "threshold_reason": "此為價值主張核心，若滿意度不足 4 分代表 AI 摘要仍有幻覺或不符實務",
                "owner": "David Chang (PO)",
                "due": "2026-10-15",
                "if_false": "退回半自動模式，由 PM 手動確認勾選後才推送進度，不強推全自動"
            },
            {
                "id": "VER-02",
                "priority": 2,
                "claim_id": "CLM-01",
                "decision_impact": "若自主註冊轉換極差，需評估是否需改以業務陌生拜訪 (Cold Outreach) 或改選 S2 客群",
                "method": "建置專屬 Landing Page 並投放 $500 美元社群廣告與 Product Hunt 試發布",
                "audience": "台灣與北美遠距軟體開發者與專案管理者",
                "data_to_collect": "網站訪客造訪到點擊「免費試用」的轉換率 (CVR)",
                "threshold": "訪客到試用註冊轉換率高於 5%",
                "threshold_reason": "SaaS 業界標準訪客註冊門檻通常在 3-5%，高於 5% 證明價值主張文案具強烈吸引力",
                "owner": "行銷實習生 Emily",
                "due": "2026-10-30",
                "if_false": "全面改寫 Landing Page 價值主張文案，聚焦於『消滅冗長會議』切角再次測試"
            },
            {
                "id": "VER-03",
                "priority": 3,
                "claim_id": "CLM-04",
                "decision_impact": "若團隊試用後留存低於門檻，代表產品體驗無法形成日常習慣",
                "method": "追蹤前 20 組試用團隊第 14 天團隊成員持續造訪比例",
                "audience": "已完成導入設定之新創試用團隊全員",
                "data_to_collect": "第 14 天活躍使用率 (Day 14 Team Retention)",
                "threshold": "第 14 天團隊活躍比例大於 40%",
                "threshold_reason": "協同軟體需要團隊半數以上維持使用才能產生網絡效益",
                "owner": "技術主管 Kevin",
                "due": "2026-11-15",
                "if_false": "加強新人導入引導流程 (Onboarding Wizard) 與 Slack 每日智慧提醒互動頻率"
            }
        ],
        "sources": [
            {
                "id": "SRC-01",
                "title": "遠距工作團隊痛點調查報告 (台灣軟體社群)",
                "locator": "2026 Q1 問卷調查報告第 14-18 頁",
                "date": "2026-03-15",
                "date_note": "社群問卷調查，樣本數 N=182，涵蓋台灣及遠距新創員工",
                "url": "https://example.com/survey-remote-2026",
                "scope_limit": "主要為科技與軟體新創領域，不可外推至非數位產業",
                "is_simulated": True
            },
            {
                "id": "SRC-02",
                "title": "台灣電商營運痛點訪談紀要 (5家成長型品牌)",
                "locator": "內部訪談逐字稿整理第 4-9 頁",
                "date": "2026-02-20",
                "date_note": "訪談 5 位年營收 3000-8000 萬台幣電商創辦人與營運主管",
                "url": None,
                "scope_limit": "樣本數較少，僅反映電商檔期大促期間之協同痛點",
                "is_simulated": True
            },
            {
                "id": "SRC-03",
                "title": "行銷代操與數位顧問公會收費生態調查",
                "locator": "產業白皮書專題報告 2025 第 3 章",
                "date": "2025-11-10",
                "date_note": "歷史參考資料，市場報價可能受通膨微調",
                "url": "https://example.com/agency-report-2025",
                "scope_limit": "主要針對台北地區 20-50 人中小型公關行銷代理商",
                "is_simulated": True
            }
        ],
        "claims": [
            {
                "id": "CLM-01",
                "text": "遠距軟體新創有 72% 團隊每週花費超過 4 小時在跨時區進度確認會議",
                "nature": "evidence",
                "verification_status": "checked",
                "verification_scope": "material_only",
                "is_simulated": True,
                "origin": "manual",
                "source_ids": ["SRC-01"],
                "human_reason": "經比對 SRC-01 問卷統計數據真實核對，但僅限於遠距軟體樣本"
            },
            {
                "id": "CLM-02",
                "text": "電商團隊在促銷檔期交接失誤率高達 35%，主因為不同部門工具未整合",
                "nature": "inference",
                "verification_status": "pending",
                "verification_scope": "material_only",
                "is_simulated": True,
                "origin": "manual",
                "source_ids": ["SRC-02"],
                "human_reason": "由 5 家訪談歸納之質性推論，尚未有大規模量化數據佐證"
            },
            {
                "id": "CLM-03",
                "text": "代理商客戶對即時透明專案看板有高度偏好，願意為專業視覺化額外付費",
                "nature": "assumption",
                "verification_status": "insufficient",
                "verification_scope": "material_only",
                "is_simulated": True,
                "origin": "manual",
                "source_ids": ["SRC-03"],
                "human_reason": "此為創辦團隊假設，目前缺乏具體願意加價購買的合約證據"
            },
            {
                "id": "CLM-04",
                "text": "S1 遠距新創市場能以最低獲客成本 (CAC) 取得高忠誠度早期用戶",
                "nature": "inference",
                "verification_status": "pending",
                "verification_scope": "material_only",
                "is_simulated": True,
                "origin": "manual",
                "source_ids": ["SRC-01"],
                "human_reason": "由社群自發傳播力推論而得，須經 Landing Page 實際廣告驗證"
            },
            {
                "id": "CLM-05",
                "text": "AI 自動脈絡整理能實質替代通用專案看板並為用戶節省 60% 開會時間",
                "nature": "assumption",
                "verification_status": "pending",
                "verification_scope": "material_only",
                "is_simulated": True,
                "origin": "manual",
                "source_ids": ["SRC-01"],
                "human_reason": "產品核心價值主張，已列入 W6 第一順位驗證行動"
            }
        ],
        "revision": {
            "proposal_id": "PROP-G01",
            "version": 1,
            "parent_version": None,
            "saved_at": "2026-09-23T06:00:00Z",
            "is_mock": True,
            "author_label": "第 1 組 (G01) 全體成員",
            "change_log": ["建立初始版本 v1，載入協作台 B2B SaaS 教學模擬案例"]
        }
    }
}
