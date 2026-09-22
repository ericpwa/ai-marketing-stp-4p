"""
匯出小幫手模組 (Export Helpers)
負責將當前快照序列化為標準 Markdown 報告與標準 JSON，並計算一致的 SHA-256 雜湊校驗碼。
"""

import json
import hashlib
from datetime import datetime

def compute_sha256(data_str: str) -> str:
    """計算字串的 SHA-256 雜湊碼"""
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

def export_proposal_json(state_dict: dict) -> str:
    """
    將目前的提案完整狀態打包為標準 JSON 字串
    符合 Draft 2020-12 Schema 與資料契約
    """
    # 建立深度拷貝清理資料
    proposal = {
        "document_type": "proposal",
        "case": state_dict.get("case", {}),
        "persona": state_dict.get("persona", {}),
        "segments": state_dict.get("segments", []),
        "criteria": state_dict.get("criteria", []),
        "ratings": state_dict.get("ratings", []),
        "target_decision": state_dict.get("target_decision", {}),
        "positioning": state_dict.get("positioning", {}),
        "marketing_4p": state_dict.get("marketing_4p", {}),
        "bmc_summary": state_dict.get("bmc_summary", {}),
        "verification_actions": state_dict.get("verification_actions", []),
        "sources": state_dict.get("sources", []),
        "claims": state_dict.get("claims", []),
        "revision": state_dict.get("revision", {})
    }
    return json.dumps(proposal, ensure_ascii=False, indent=2)

def export_proposal_markdown(state_dict: dict) -> str:
    """
    將目前的提案狀態按照規格文件固定順序生成專業 Markdown 報告
    """
    case = state_dict.get("case", {})
    persona = state_dict.get("persona", {})
    segments = state_dict.get("segments", [])
    criteria = state_dict.get("criteria", [])
    ratings = state_dict.get("ratings", [])
    tgt = state_dict.get("target_decision", {})
    pos = state_dict.get("positioning", {})
    four_p = state_dict.get("marketing_4p", {})
    bmc = state_dict.get("bmc_summary", {})
    actions = state_dict.get("verification_actions", [])
    sources = state_dict.get("sources", [])
    claims = state_dict.get("claims", [])
    rev = state_dict.get("revision", {})

    # 先取得 JSON 用以計算指紋
    json_repr = export_proposal_json(state_dict)
    fingerprint = compute_sha256(json_repr)

    sim_badge = "【⚠️ 教學模擬案例 - 非市場真實保證】" if case.get("is_simulated", True) else "【真實市場案例】"

    md = f"""---
proposal_id: "{rev.get('proposal_id', 'PROP-001')}"
version: {rev.get('version', 1)}
saved_at: "{rev.get('saved_at', datetime.now().isoformat())}"
export_snapshot_sha256: "{fingerprint}"
is_simulated: {str(case.get('is_simulated', True)).lower()}
---

# 市場定位分析與行銷策略報告（STP & 4P）

> **案例名稱**：{case.get('name', '未命名案例')}  
> **組別工作區**：{case.get('workspace_id', 'G01')} ｜ **模擬標示**：{sim_badge}  
> **提案版本**：v{rev.get('version', 1)} ｜ **儲存時間**：{rev.get('saved_at', 'N/A')}  
> **快照 SHA-256 驗證指紋**：`{fingerprint}`

---

## ▍W1 目標人物誌 (Persona)

- **姓名/代表標籤**：{persona.get('name', '未命名')}
- **工作角色**：{persona.get('work_role', 'N/A')}
- **生活/工作情境**：{persona.get('context', 'N/A')}
- **核心需求與痛點**：
"""
    for n in persona.get("needs", []):
        md += f"  - {n}\n"

    md += f"""- **現行作法**：{persona.get('current_practice', 'N/A')}
- **決策與購買角色**：
  - 使用者 (Users)：{', '.join(persona.get('users', []))}
  - 影響者 (Influencers)：{', '.join(persona.get('influencers', []))}
  - 決策者 (Decision Makers)：{persona.get('decision_makers', 'N/A')}
- **採購與採用限制**：
"""
    for c in persona.get("purchase_constraints", []):
        md += f"  - {c}\n"

    md += f"""- **不可泛化邊界說明**：{persona.get('not_generalizable', 'N/A')}

---

## ▍W2 市場區隔 (Segmentation - S)

共劃分 {len(segments)} 個候選市場區隔：

"""
    for idx, s in enumerate(segments, 1):
        md += f"""### 區隔 {s.get('id', f'S{idx}')}：{s.get('name', '未命名區隔')}
- **區隔維度**：{s.get('dimension', 'N/A')}
- **納入條件 (Inclusion)**：{s.get('inclusion', 'N/A')}
- **排除條件 (Exclusion)**：{s.get('exclusion', 'N/A')}
- **核心需求情境**：{s.get('needs_context', 'N/A')}
- **購買角色與決策鏈**：{s.get('buying_roles', 'N/A')}
- **接觸路徑與獲客渠道**：{s.get('contact_path', 'N/A')}
- **重疊與缺口分析**：{s.get('overlap_gaps', 'N/A')}

"""

    md += """---

## ▍W3 目標市場評估與決策 (Targeting - T)

### 1. 四大評估標準與權重
| 條件代碼 | 評估條件名稱 | 評估標準 | 權重 (%) | 權重設定理由 |
| :--- | :--- | :--- | :---: | :--- |
"""
    for c in criteria:
        md += f"| {c.get('id')} | {c.get('name')} | {c.get('standard')} | {c.get('weight')}% | {c.get('weight_reason')} |\n"

    md += f"""
### 2. 客群評分矩陣
| 客群代碼 | 客群名稱 | """ + " | ".join([c.get('name') for c in criteria]) + " | 加權總分 | 排名 |\n"
    md += "| :--- | :--- | " + " | ".join([":---:" for _ in criteria]) + " | :---: | :---: |\n"

    ranking_map = {r.get("segment_id"): r for r in tgt.get("ranking", [])} if tgt.get("ranking") else {}

    for s in segments:
        sid = s.get("id")
        row_str = f"| {sid} | {s.get('name')} | "
        for c in criteria:
            cid = c.get("id")
            score_entry = next((r for r in ratings if r.get("segment_id") == sid and r.get("criterion_id") == cid), None)
            score_val = score_entry.get("score") if score_entry else "null"
            row_str += f"{score_val if score_val is not None else '資料不足'} | "
        
        rk_info = ranking_map.get(sid, {})
        w_score = f"{rk_info.get('weighted_score', 'N/A'):.2f}" if isinstance(rk_info.get('weighted_score'), (int, float)) else "條件式"
        rk = f"第 {rk_info.get('rank')} 名" if rk_info.get('rank') else "-"
        row_str += f"{w_score} | {rk} |\n"
        md += row_str

    sel_id = tgt.get("selected_segment_id")
    sel_name = next((s.get("name") for s in segments if s.get("id") == sel_id), sel_id)

    md += f"""
### 3. 目標市場人工決策結論
- **選定目標客群**：**{sel_id} - {sel_name}**
- **決策模式**：`{tgt.get('mode', 'complete')}`
- **決策理由**：{tgt.get('reason', 'N/A')}
- **未選客群之取捨代價 (Tradeoffs)**：{tgt.get('tradeoffs', 'N/A')}
- **改選/重新評估條件 (Change Condition)**：{tgt.get('change_condition', 'N/A')}
- **下一步檢驗點 (Next Check)**：{tgt.get('next_check', 'N/A')}
- **人工確認狀態**：{'✅ 已由團隊人工確認' if tgt.get('human_confirmed') else '⚠️ 尚未人工確認'}

---

## ▍W4 市場定位與價值主張 (Positioning - P)

- **目標客群引用**：{pos.get('segment_id', sel_id)}
- **核心滿足需求**：{pos.get('need', 'N/A')}
- **產品/服務名稱**：**{pos.get('product_name', 'N/A')}**
- **核心價值主張**：{pos.get('value', 'N/A')}

### ▍定位聲明 (Positioning Statement)
> {pos.get('statement', 'N/A')}

### ▍替代方案與差異化對比 (Alternatives)
"""
    for idx, alt in enumerate(pos.get("alternatives", []), 1):
        md += f"""#### 替代方案 {idx}：{alt.get('name', '未命名替代方案')}
- **現行相同需求解法**：{alt.get('same_need_solution', 'N/A')}
- **本產品提出之核心差異**：{alt.get('proposed_difference', 'N/A')}
- **驗證重點**：{alt.get('to_verify', 'N/A')}

"""

    md += f"""---

## ▍行銷 4P 組合策略 (Marketing 4P Mix)

### 1. 產品策略 (Product)
- **核心功能特色**：{four_p.get('product', {}).get('core_features', 'N/A')}
- **規格與交付形式**：{four_p.get('product', {}).get('packaging_spec', 'N/A')}
- **品牌調性**：{four_p.get('product', {}).get('brand_tone', 'N/A')}
- **獨特賣點 (USP)**：{four_p.get('product', {}).get('usp', 'N/A')}

### 2. 價格策略 (Price)
- **定價模式**：{four_p.get('price', {}).get('pricing_model', 'N/A')}
- **價格帶與方案**：{four_p.get('price', {}).get('price_tier', 'N/A')}
- **折讓與激勵策略**：{four_p.get('price', {}).get('discount_strategy', 'N/A')}
- **價值錨定比較**：{four_p.get('price', {}).get('value_anchor', 'N/A')}

### 3. 通路策略 (Place)
- **主要接觸通路**：{four_p.get('place', {}).get('channels', 'N/A')}
- **轉換與導入路徑**：{four_p.get('place', {}).get('onboarding_path', 'N/A')}
- **通路夥伴與生態**：{four_p.get('place', {}).get('partnerships', 'N/A')}

### 4. 推廣策略 (Promotion)
- **核心 Slogan / 傳播訊息**：{four_p.get('promotion', {}).get('slogan', 'N/A')}
- **內容行銷策略**：{four_p.get('promotion', {}).get('content_strategy', 'N/A')}
- **獲客誘餌與活動 (Hooks)**：{four_p.get('promotion', {}).get('growth_hooks', 'N/A')}
- **社群與口碑營造**：{four_p.get('promotion', {}).get('community', 'N/A')}

---

## ▍W5 商業模式圖 (BMC) 關鍵兩格摘要

- **目標客層 (Customer Segments)**：
  - 引用自：`{bmc.get('target_segment_id', sel_id)}`
  - 具體描述：{bmc.get('customer_segments', 'N/A')}
- **價值主張 (Value Proposition)**：
  - 引用主張：`{bmc.get('positioning_claim_id', 'N/A')}`
  - 具體承諾：{bmc.get('value_proposition', 'N/A')}
- **對商業模式其他格位之衍生影響**：{bmc.get('other_impacts', 'N/A')}

---

## ▍W6 關鍵假說驗證行動 (Verification Actions)

共規劃 {len(actions)} 項驗證行動（上限 3 項）：

| 優先序 | 驗證方法 | 目標對象 | 收集資料指標 | 成功門檻與理由 | 負責人 | 期限 | 不成立時之修正策略 |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
"""
    for a in actions:
        md += f"| {a.get('priority')} | {a.get('method')} | {a.get('audience')} | {a.get('data_to_collect')} | {a.get('threshold')}<br>({a.get('threshold_reason')}) | {a.get('owner')} | {a.get('due')} | {a.get('if_false')} |\n"

    md += """
---

## ▍主張台帳 (Claims Register)

| 主張 ID | 主張內容敘述 | 性質 (Nature) | 查核狀態 (Status) | 來源 ID | 人工理由與備註 |
| :--- | :--- | :---: | :---: | :---: | :--- |
"""
    for clm in claims:
        nat = clm.get("nature", "assumption")
        st = clm.get("verification_status", "pending")
        sids = ", ".join(clm.get("source_ids", []))
        md += f"| {clm.get('id')} | {clm.get('text')} | `{nat}` | `{st}` | {sids} | {clm.get('human_reason', '-')} |\n"

    md += """
---

## ▍來源台帳 (Sources Register)

| 來源 ID | 資料來源標題 | 定位點 (Locator) | 日期與備註 | 網址 / 檔案 | 模擬標示 |
| :--- | :--- | :--- | :--- | :--- | :---: |
"""
    for src in sources:
        sim = "教學模擬" if src.get("is_simulated") else "外部實證"
        url = f"[{src.get('url')}]({src.get('url')})" if src.get("url") else "-"
        md += f"| {src.get('id')} | {src.get('title')} | {src.get('locator')} | {src.get('date', '未知')} ({src.get('date_note', '-')}) | {url} | `{sim}` |\n"

    md += """
---

## ▍版本變更紀錄 (Revision Change Log)

"""
    for log in rev.get("change_log", []):
        md += f"- {log}\n"

    md += f"""
*(報告產出時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 由 AI 市場定位分析 Web App 自動輸出)*
"""
    return md
