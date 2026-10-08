import streamlit as st
import json
import os
import re
import urllib.parse
from datetime import datetime

# 引入自訂模組
from sample_data import SAMPLE_CASES
from export_helpers import export_proposal_json, export_proposal_markdown, compute_sha256

# ==========================================
# 頁面基本配置 (Page Config)
# ==========================================
st.set_page_config(
    page_title="AI 市場定位分析師 (STP & 4P) | 品牌策略工作台",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 輔助函式：乾淨渲染 HTML
# ==========================================
def render_html(html_str):
    if not html_str:
        return
    lines = [line.strip() for line in html_str.split("\n") if line.strip()]
    cleaned_html = "\n".join(lines)
    st.markdown(cleaned_html, unsafe_allow_html=True)

# 載入自訂 CSS 樣式
def load_css(file_name="style.css"):
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# 清理模型回傳的 Markdown 代碼塊
def clean_json_string(text):
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text

# ==========================================
# 初始化 Session State 狀態變數
# ==========================================
default_sample = SAMPLE_CASES["collaboration_hub"]

session_defaults = {
    "step": 1,
    "api_key": "",
    "api_key_valid": False,
    "model_name": "gemini-2.0-flash",
    "available_models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-flash"],
    "api_error": None,
    "case": dict(default_sample["case"]),
    "persona": dict(default_sample["persona"]),
    "segments": [dict(s) for s in default_sample["segments"]],
    "criteria": [dict(c) for c in default_sample["criteria"]],
    "ratings": [dict(r) for r in default_sample["ratings"]],
    "target_decision": dict(default_sample["target_decision"]),
    "positioning": dict(default_sample["positioning"]),
    "marketing_4p": dict(default_sample["marketing_4p"]),
    "bmc_summary": dict(default_sample["bmc_summary"]),
    "verification_actions": [dict(a) for a in default_sample["verification_actions"]],
    "sources": [dict(src) for src in default_sample["sources"]],
    "claims": [dict(clm) for clm in default_sample["claims"]],
    "revision": dict(default_sample["revision"]),
    "active_avatar_seed": default_sample["persona"]["name"]
}

for k, v in session_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==========================================
# Google GenAI 客戶端與多模型自動備援 (BYOK)
# ==========================================
def get_gemini_client(api_key):
    try:
        from google import genai
        clean_key = api_key.strip().strip("'").strip('"')
        return genai.Client(api_key=clean_key)
    except Exception as e:
        st.session_state.api_error = "無法初始化 Google GenAI SDK，請確認金鑰與執行環境。原始錯誤內容不顯示。"
        return None

def validate_api_key(api_key):
    if not api_key:
        return False
    clean_key = api_key.strip().strip("'").strip('"')
    if not clean_key:
        st.session_state.api_error = "金鑰不可為空白"
        return False

    client = get_gemini_client(clean_key)
    if not client:
        return False

    test_models = [
        st.session_state.model_name,
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-flash"
    ]
    unique_models = []
    for m in test_models:
        if m not in unique_models:
            unique_models.append(m)

    last_err = None
    for model in unique_models:
        try:
            client.models.generate_content(
                model=model,
                contents="PING"
            )
            st.session_state.model_name = model
            st.session_state.api_error = None
            return True
        except Exception as e:
            last_err = e
            continue

    err_str = str(last_err)
    if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
        st.session_state.api_error = "API Key 無效，請檢查是否複製完整或包含多餘空格。"
    elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
        st.session_state.api_error = "此 API Key 配額已滿或觸發頻率限制，請稍候重試。"
    else:
        st.session_state.api_error = "金鑰驗證失敗，請檢查權限、模型可用性與網路連線。原始錯誤內容不顯示。"
    return False

def generate_content_with_fallback(prompt, system_instruction=None, json_mode=False):
    client = get_gemini_client(st.session_state.api_key)
    if not client:
        raise Exception("Gemini Client 初始化失敗，請檢查金鑰")

    from google.genai import types
    config_args = {}
    if system_instruction:
        config_args["system_instruction"] = system_instruction
    if json_mode:
        config_args["response_mime_type"] = "application/json"
    
    config = types.GenerateContentConfig(**config_args) if config_args else None

    models_to_try = [
        st.session_state.model_name,
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-flash"
    ]
    unique_models = []
    for m in models_to_try:
        if m not in unique_models:
            unique_models.append(m)

    last_error = None
    for model in unique_models:
        try:
            kwargs = {"model": model, "contents": prompt}
            if config:
                kwargs["config"] = config
            response = client.models.generate_content(**kwargs)
            st.session_state.model_name = model
            return response.text
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError("所有備援模型均無法連線，請檢查權限、配額與網路。原始錯誤內容不顯示。") from None

# ==========================================
# 頂部 Header 與 標題
# ==========================================
render_html("<h1 class='main-title'>🎯 AI 市場定位分析師 (STP & 4P)</h1>")
render_html("<p class='sub-title'>專為行銷人、產品經理與創業團隊打造的智能定位工作台。從目標人物誌出發，科學推演 STP 市場定位與 4P 行銷組合！</p>")

# ==========================================
# 側邊欄：伺服器端 BYOK 與控制面板
# ==========================================
with st.sidebar:
    st.markdown("### 🔑 金鑰與防護 (BYOK)")
    st.caption("金鑰會送至本 App 的 Streamlit 伺服器，保存在該會話的伺服器端記憶體，再由 Python 呼叫 Google；不是 Browser-only BYOK。請只在信任的部署輸入專用、受限制的 Key，不要貼進提案、人物姓名或上傳檔案。")
    st.caption("輸入或更換金鑰會自動驗證；驗證與模型備援可能產生多次 API 呼叫，消耗您的配額或費用。免費額度與資料使用條款依 Google 當時政策及帳戶而定。")
    with st.expander("金鑰與資料使用須知"):
        st.markdown("程式未主動將金鑰欄位寫入提案匯出；這不保證代管平台、SDK、代理或日誌系統不留存。清空金鑰欄位可移除 App 的目前金鑰值，但不保證記憶體副本立即抹除；疑似外洩請至 Google 撤銷金鑰。 Persona 姓名會用作 DiceBear 頭像網址的 seed，並載入 Google Fonts；請使用化名。")
    api_key_input = st.text_input(
        "輸入 Google Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="金鑰會送至本 App 的 Streamlit 伺服器，保存在該會話的伺服器端記憶體，再由 Python 呼叫 Google；不是 Browser-only BYOK。請只在信任的部署輸入專用、受限制的 Key，不要貼進提案、人物姓名或上傳檔案。"
    )

    clean_input = api_key_input.strip().strip("'").strip('"')
    if clean_input != st.session_state.api_key:
        st.session_state.api_key = clean_input
        st.session_state.api_error = None
        if clean_input:
            with st.spinner("連線驗證中..."):
                valid = validate_api_key(clean_input)
                st.session_state.api_key_valid = valid
                if valid:
                    st.success("✅ 金鑰驗證通過！")
                else:
                    st.error("❌ 金鑰驗證失敗")
        else:
            st.session_state.api_key_valid = False

    # 模型切換
    curr_idx = st.session_state.available_models.index(st.session_state.model_name) if st.session_state.model_name in st.session_state.available_models else 0
    selected_model = st.selectbox(
        "AI 核心模型 (多模型自動備援)",
        options=st.session_state.available_models,
        index=curr_idx,
        help="支援最新 gemini-2.0 / 2.5 / 1.5 系列。遇模型不可用時會自動切換備援。"
    )
    st.session_state.model_name = selected_model

    # 服務狀態
    if st.session_state.api_key_valid:
        render_html("<div style='color:#10b981; font-weight:bold; margin-bottom:12px;'>● 服務狀態：已啟用 (Active)</div>")
    else:
        render_html("<div style='color:#ef4444; font-weight:bold; margin-bottom:12px;'>● 服務狀態：未啟用 (Key Required)</div>")
        if st.session_state.api_error:
            render_html(f"<div style='background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.4); border-radius:8px; padding:10px; font-size:0.82rem; color:#fca5a5; margin-bottom:12px;'><b>原因：</b><br>{st.session_state.api_error}</div>")

    with st.expander("❓ 如何取得 Gemini API Key 與確認費用？"):
        st.markdown(
            """
            1. 前往 👉 [Google AI Studio](https://aistudio.google.com/)。
            2. 使用您的 **Google 帳號** 登入。
            3. 點擊 **"Get API Key"** -> **"Create API Key"**。
            4. 複製金鑰並貼於上方輸入框。
            
            *提示：免費額度、可用模型與費率依 Google 帳戶及最新政策而定；請先確認配額、預算與資料使用條款。*
            """
        )

    st.markdown("---")
    st.markdown("### 🏢 工作區與案例管理")
    st.session_state.case["workspace_id"] = st.text_input("組別工作區代號", value=st.session_state.case.get("workspace_id", "G01"))
    st.session_state.case["name"] = st.text_input("案例/產品名稱", value=st.session_state.case.get("name", "「協作台」跨部門專案協同平台"))
    st.session_state.case["is_simulated"] = st.checkbox("教學模擬案例 (is_simulated=true)", value=st.session_state.case.get("is_simulated", True))

    st.markdown("---")
    st.markdown("### ⚡ 快速體驗與重置")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("🔄 載入協作台範例", use_container_width=True):
            loaded = SAMPLE_CASES["collaboration_hub"]
            for k, val in loaded.items():
                if isinstance(val, list):
                    st.session_state[k] = [dict(item) if isinstance(item, dict) else item for item in val]
                elif isinstance(val, dict):
                    st.session_state[k] = dict(val)
                else:
                    st.session_state[k] = val
            st.session_state.active_avatar_seed = st.session_state.persona["name"]
            st.success("✅ 協作台示範案例已載入！")
            st.rerun()
    with col_sb2:
        if st.button("🗑️ 清空所有欄位", use_container_width=True):
            st.session_state.persona = {
                "id": "PER-01", "name": "", "work_role": "", "context": "", "needs": [], "current_practice": "",
                "users": [], "influencers": [], "decision_makers": "", "purchase_constraints": [],
                "source_ids": [], "not_generalizable": "", "gaps": [], "unmapped_fields": {}
            }
            st.session_state.segments = []
            st.session_state.target_decision = {"selected_segment_id": "", "mode": "conditional", "reason": "", "tradeoffs": "", "change_condition": "", "next_check": "", "human_confirmed": False, "ranking": None}
            st.session_state.positioning = {"need": "", "product_name": "", "value": "", "statement": "", "alternatives": [], "human_confirmed": False, "needs_review": False}
            st.session_state.marketing_4p = {"product": {}, "price": {}, "place": {}, "promotion": {}}
            st.session_state.bmc_summary = {"customer_segments": "", "value_proposition": "", "other_impacts": "", "needs_review": False}
            st.session_state.verification_actions = []
            st.info("已清空當前欄位")
            st.rerun()

    # JSON 快照備份還原
    uploaded_json = st.file_uploader("📂 還原先前儲存的 JSON 提案", type=["json"])
    if uploaded_json is not None:
        try:
            imported = json.load(uploaded_json)
            for k in ["case", "persona", "segments", "criteria", "ratings", "target_decision", "positioning", "marketing_4p", "bmc_summary", "verification_actions", "sources", "claims", "revision"]:
                if k in imported:
                    st.session_state[k] = imported[k]
            st.success("🎉 提案快照還原成功！")
            st.rerun()
        except Exception as e:
            st.error("還原失敗。請檢查輸入資料、金鑰權限與配額後重試；原始錯誤內容不顯示。")

# ==========================================
# 門禁檢查：未輸入有效金鑰時的主畫面提示
# ==========================================
if not st.session_state.api_key_valid:
    render_html(
        """
        <div class="glass-card">
            <h3 style="color:#a78bfa; margin-top:0;">👋 歡迎使用 AI 市場定位分析師 (STP & 4P)！</h3>
            <p style="color:#cbd5e1; font-size:1.05rem; line-height:1.6;">
                本工具支援行銷實戰與教學應用，具備 <b>目標人物誌 (Persona) ➔ 市場區隔 (S) ➔ 目標市場評估 (T) ➔ 市場定位與價值主張 (P) ➔ 行銷 4P 組合 ➔ BMC 商業模式與驗證行動</b> 完整閉環推演流程。
            </p>
            <div style="background:rgba(139,92,246,0.12); border-left:4px solid #8b5cf6; border-radius:10px; padding:16px; margin:20px 0;">
                <b style="color:#c084fc; font-size:1.05rem;">🔑 伺服器端 BYOK (Bring Your Own Key) 使用須知：</b><br>
                <span style="color:#cbd5e1; font-size:0.95rem;">
                金鑰會送至本 App 的 Streamlit 伺服器，保存在該會話的伺服器端記憶體，再由 Python 呼叫 Google；不是 Browser-only BYOK。請只在信任的部署輸入專用、受限制的 Key，不要貼進提案、人物姓名或上傳檔案。 輸入或更換金鑰會自動驗證；驗證與模型備援可能產生多次 API 呼叫，消耗您的配額或費用。免費額度與資料使用條款依 Google 當時政策及帳戶而定。
                </span>
            </div>
            <p style="color:#94a3b8;">👉 請至<b>左側選單</b>輸入您的 Google Gemini API Key。若無金鑰，可展開左側說明申請並確認配額與費用。</p>
        </div>
        """
    )
    st.stop()

# ==========================================
# 頂部 7 步驟 Wizard 導航線條與按鈕 (HTML + Streamlit)
# ==========================================
step_labels = ["1. Persona 畫像", "2. S 市場區隔", "3. T 目標決策", "4. P 市場定位", "5. 行銷 4P 組合", "6. BMC 與驗證", "7. 提案與匯出"]
active_step = st.session_state.step

wizard_cols = st.columns(7)
for i in range(1, 8):
    with wizard_cols[i-1]:
        is_active = (i == active_step)
        btn_style = "primary" if is_active else "secondary"
        if st.button(step_labels[i-1], key=f"nav_step_{i}", type=btn_style, use_container_width=True):
            st.session_state.step = i
            st.rerun()

render_html("<div style='height: 15px;'></div>")

# ==========================================
# STEP 1: 案例與 Persona 畫像
# ==========================================
if st.session_state.step == 1:
    render_html(
        """
        <div class="guide-alert">
            <div class="guide-title">💡 小白心法 1：好定位始於立體的人物誌 (Persona)</div>
            <p class="guide-content">
                不要對著空氣做行銷！先想像出一位活生生的目標人物。他的工作角色是什麼？日常面臨什麼煩惱與工作阻礙？手頭現有什麼簡陋作法？
                填寫簡單關鍵字後，點擊「✨ AI 幫我潤飾」即可將想法精煉成專業洞察。
            </p>
        </div>
        """
    )

    persona = st.session_state.persona

    # 左右兩欄：左邊表單，右邊視覺化卡片 + Lorelei 頭像
    col_input, col_preview = st.columns([3, 2])

    with col_input:
        st.markdown("#### 📝 目標人物基本輪廓")
        p_name = st.text_input("人物姓名 / 代表標籤", value=persona.get("name", "張經理 David Chang"), placeholder="例：林總監 Kevin, 自由設計師 Amy")
        p_role = st.text_input("工作角色 / 職稱", value=persona.get("work_role", ""), placeholder="例：成長型軟體團隊 PM 主管, 中小型餐飲店老闆")

        p_context = st.text_area(
            "生活 / 工作情境與痛點背景",
            value=persona.get("context", ""),
            placeholder="描述他的團隊規模、日常工作流程，以及跨部門協同或業務上的關鍵阻礙...",
            height=130
        )

        col_polish1, col_polish2 = st.columns([1, 1])
        with col_polish1:
            if st.button("✨ AI 幫我潤飾情境描述", use_container_width=True):
                if not p_context.strip():
                    st.warning("⚠️ 請先輸入幾句情境或痛點想法喔！")
                else:
                    with st.spinner("AI 文案大師正在精煉洞察中..."):
                        prompt = f"你是一位資深使用者研究員與品牌行銷顧問。請將以下這段使用者情境與痛點描述，擴充潤飾為一段專業、生動、具備具體商業痛點的人物誌情境背景（約 150 字，以繁體中文撰寫）。原始描述：'{p_context}'"
                        try:
                            res = generate_content_with_fallback(prompt)
                            persona["context"] = res.strip()
                            st.session_state.persona = persona
                            st.rerun()
                        except Exception as e:
                            st.error("潤飾失敗。請檢查輸入資料、金鑰權限與配額後重試；原始錯誤內容不顯示。")

        st.markdown("#### 🎯 核心需求與現行替代作法")
        needs_str = st.text_area(
            "核心需求 (每行一項)",
            value="\n".join(persona.get("needs", [])),
            placeholder="自動化追蹤跨部門進度\n減少每週重複彙整報表會議...",
            height=90
        )
        p_practice = st.text_area(
            "現行替代作法 (目前怎麼將就著過？)",
            value=persona.get("current_practice", ""),
            placeholder="例：每週手動向各部門索取 Excel 填報，散落在 LINE 與 Slack 催進度...",
            height=80
        )

        st.markdown("#### 👥 決策與購買限制 (B2B / B2C 適用)")
        col_dm1, col_dm2 = st.columns(2)
        with col_dm1:
            p_users = st.text_input("實際使用者 (Users)", value=", ".join(persona.get("users", [])), placeholder="各部門專案成員、工程師")
            p_influencers = st.text_input("內部影響者 (Influencers)", value=", ".join(persona.get("influencers", [])), placeholder="資安主管、財務主管")
        with col_dm2:
            p_decision = st.text_input("最終決策者 (Decision Maker)", value=persona.get("decision_makers", "營運副總 / 執行長"))
            p_constraints = st.text_input("採購與採用限制", value=", ".join(persona.get("purchase_constraints", [])), placeholder="預算每月 5 萬內、導入期 2 週內")

        p_not_gen = st.text_input("不可外推之邊界限制", value=persona.get("not_generalizable", "僅代表成長型軟體團隊，不可外推製造業"))

        # 更新狀態
        persona["name"] = p_name
        persona["work_role"] = p_role
        persona["context"] = p_context
        persona["needs"] = [n.strip() for n in needs_str.split("\n") if n.strip()]
        persona["current_practice"] = p_practice
        persona["users"] = [u.strip() for u in p_users.split(",") if u.strip()]
        persona["influencers"] = [i.strip() for i in p_influencers.split(",") if i.strip()]
        persona["decision_makers"] = p_decision
        persona["purchase_constraints"] = [c.strip() for c in p_constraints.split(",") if c.strip()]
        persona["not_generalizable"] = p_not_gen
        st.session_state.persona = persona
        st.session_state.active_avatar_seed = p_name if p_name else "user"

    with col_preview:
        st.markdown("#### 👤 人物誌視覺卡片預覽")
        avatar_seed = urllib.parse.quote(st.session_state.active_avatar_seed)
        avatar_url = f"https://api.dicebear.com/7.x/lorelei/svg?seed={avatar_seed}"
        fallback_avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={avatar_seed}"

        render_html(
            f"""
            <div class="persona-card">
                <div class="persona-header">
                    <div class="persona-avatar-wrapper">
                        <img src="{avatar_url}" alt="Lorelei Avatar" onerror="this.onerror=null; this.src='{fallback_avatar}';">
                    </div>
                    <div class="persona-meta">
                        <div class="persona-name-container">
                            <h3 class="persona-name">{persona.get('name', '未命名人物')}</h3>
                            <span class="persona-tag">{persona.get('work_role', '尚未設定角色')}</span>
                        </div>
                        <p class="persona-slogan">「{persona.get('context', '尚無情境描述')[:60]}...」</p>
                    </div>
                </div>
                <div class="demo-grid">
                    <div class="demo-item">
                        <div class="demo-label">決策角色</div>
                        <div class="demo-value">{persona.get('decision_makers', 'N/A')}</div>
                    </div>
                    <div class="demo-item">
                        <div class="demo-label">現行作法</div>
                        <div class="demo-value">{persona.get('current_practice', 'N/A')[:18]}..</div>
                    </div>
                    <div class="demo-item">
                        <div class="demo-label">不可外推</div>
                        <div class="demo-value">{persona.get('not_generalizable', '無')[:16]}..</div>
                    </div>
                </div>
                <div style="background:rgba(15,23,42,0.6); padding:14px; border-radius:12px; margin-top:10px;">
                    <b style="color:#c084fc; font-size:0.85rem;">📌 核心需求清單：</b>
                    <ul style="margin:6px 0 0 0; padding-left:18px; color:#e2e8f0; font-size:0.85rem;">
                        {''.join([f"<li>{n}</li>" for n in persona.get('needs', ['尚未設定需求'])])}
                    </ul>
                </div>
            </div>
            """
        )

        with st.expander("✨ AI 全自動引導：從簡短想法自動提煉 Persona"):
            quick_idea = st.text_area("輸入任何一句你的產品或商業想法：", placeholder="例如：我想做一款專為自由接案者設計的自動記帳報稅工具...")
            if st.button("🚀 一鍵自動提煉完整 Persona", use_container_width=True):
                if not quick_idea.strip():
                    st.warning("請先輸入您的想法關鍵字！")
                else:
                    with st.spinner("AI 正在提煉結構化 Persona 畫像..."):
                        p_prompt = f"""
                        根據以下產品或商業想法：'{quick_idea}'，推演出一個最關鍵的目標人物誌 (Persona)。
                        請以繁體中文撰寫，並輸出為一個合法的 JSON 物件，包含以下欄位：
                        - "name": 人物姓名與英文名
                        - "work_role": 具體職業或角色
                        - "context": 詳細工作/生活情境與痛點背景 (約 80 字)
                        - "needs": 核心需求陣列 (3 項)
                        - "current_practice": 現行將就替代作法
                        - "users": 實際使用者陣列
                        - "influencers": 影響者陣列
                        - "decision_makers": 決策者
                        - "purchase_constraints": 採購限制陣列 (2 項)
                        - "not_generalizable": 不可外推範圍說明
                        """
                        try:
                            res_json = generate_content_with_fallback(p_prompt, json_mode=True)
                            cleaned = clean_json_string(res_json)
                            extracted = json.loads(cleaned)
                            for k in ["name", "work_role", "context", "needs", "current_practice", "users", "influencers", "decision_makers", "purchase_constraints", "not_generalizable"]:
                                if k in extracted:
                                    st.session_state.persona[k] = extracted[k]
                            st.session_state.active_avatar_seed = extracted.get("name", "User")
                            st.success("🎉 Persona 提煉完成！已自動套用至上方表單！")
                            st.rerun()
                        except Exception as e:
                            st.error("提煉失敗。請檢查輸入資料、金鑰權限與配額後重試；原始錯誤內容不顯示。")

    col_btn_prev, col_btn_next = st.columns([1, 1])
    with col_btn_next:
        if st.button("下一步：市場區隔 (S) ➡️", type="primary", use_container_width=True):
            if not st.session_state.persona.get("name") or not st.session_state.persona.get("work_role"):
                st.warning("⚠️ 請至少填寫人物誌的「姓名」與「工作角色」喔！")
            else:
                st.session_state.step = 2
                st.rerun()

# ==========================================
# STEP 2: S 市場區隔 (Segmentation)
# ==========================================
elif st.session_state.step == 2:
    render_html(
        """
        <div class="guide-alert">
            <div class="guide-title">💡 小白心法 2：市場區隔 (Segmentation) —— 切得好，打得準</div>
            <p class="guide-content">
                市場不是鐵板一塊！即使面臨相似問題，不同規模、不同情境的客群，其購買決策與接觸路徑也大不相同。
                依照技術規範，我們至少要劃分 <b>3 個可比較的市場區隔 (S1, S2, S3)</b>，為下一步的決策評估做好準備。
            </p>
        </div>
        """
    )

    col_s_top1, col_s_top2 = st.columns([2, 1])
    with col_s_top1:
        st.markdown("### 📊 候選市場區隔 (至少三客群)")
    with col_s_top2:
        if st.button("✨ AI 智能推薦三客群草稿", type="primary", use_container_width=True):
            with st.spinner("AI 正在根據 Persona 與案例分析並衍生差異化客群..."):
                seg_prompt = f"""
                根據目標 Persona（角色：{st.session_state.persona.get('work_role')}，情境：{st.session_state.persona.get('context')}，需求：{', '.join(st.session_state.persona.get('needs', []))}）
                請為案例「{st.session_state.case.get('name')}」衍生出 3 個高度差異化、互補且具備可比性的候選市場區隔 (S1, S2, S3)。
                必須以繁體中文回應，並輸出為合法 JSON 陣列，每個元素包含：
                - "id": "S1", "S2", "S3"
                - "name": 客群名稱 (例如：遠距混合型軟體新創, 轉型中電商品牌團隊...)
                - "dimension": 區隔劃分維度
                - "inclusion": 納入條件 (什麼樣的特徵屬於這群)
                - "exclusion": 排除條件 (什麼樣的特徵不屬於這群)
                - "needs_context": 具體需求情境與痛點場景
                - "buying_roles": 決策角色與購買權重
                - "contact_path": 接觸路徑與獲客渠道
                - "overlap_gaps": 與其他客群之重疊或特有缺口
                """
                try:
                    res_raw = generate_content_with_fallback(seg_prompt, json_mode=True)
                    cleaned = clean_json_string(res_raw)
                    new_segs = json.loads(cleaned)
                    if isinstance(new_segs, list) and len(new_segs) >= 3:
                        st.session_state.segments = new_segs
                        # 同步加入主張台帳 (BR04: AI 生成標為 inference, pending)
                        for s in new_segs:
                            st.session_state.claims.append({
                                "id": f"CLM-GEN-{s.get('id')}",
                                "text": f"客群 {s.get('name')} 具備明確付費意願與接觸路徑",
                                "nature": "inference",
                                "verification_status": "pending",
                                "verification_scope": "material_only",
                                "is_simulated": st.session_state.case.get("is_simulated", True),
                                "origin": "ai_draft",
                                "source_ids": ["SRC-01"],
                                "human_reason": "AI 初步衍生草稿，待後續市調驗證"
                            })
                        st.success("🎉 3 組候選客群生成成功！請在下方進行人工檢視與微調。")
                        st.rerun()
                except Exception as e:
                    st.error("生成客群失敗。請檢查輸入資料、金鑰權限與配額後重試；原始錯誤內容不顯示。")

    # 渲染 S1, S2, S3 卡片與編輯器
    segments = st.session_state.segments
    if not segments:
        st.info("目前尚未建立客群區隔，您可以點擊右上角『✨ AI 智能推薦三客群草稿』，或點選下方手動新增。")

    for idx, s in enumerate(segments):
        sid = s.get("id", f"S{idx+1}")
        with st.expander(f"📌 區隔 {sid}：{s.get('name', '未命名區隔')}", expanded=True):
            col_seg1, col_seg2 = st.columns([1, 1])
            with col_seg1:
                s["id"] = st.text_input(f"客群編號 ({sid})", value=sid, key=f"s_id_{idx}")
                s["name"] = st.text_input(f"客群名稱 ({sid})", value=s.get("name", ""), key=f"s_name_{idx}")
                s["dimension"] = st.text_input(f"劃分維度 ({sid})", value=s.get("dimension", ""), key=f"s_dim_{idx}")
                s["inclusion"] = st.text_area(f"納入條件 Inclusion ({sid})", value=s.get("inclusion", ""), height=70, key=f"s_inc_{idx}")
                s["exclusion"] = st.text_area(f"排除條件 Exclusion ({sid})", value=s.get("exclusion", ""), height=70, key=f"s_exc_{idx}")
            with col_seg2:
                s["needs_context"] = st.text_area(f"核心需求情境 ({sid})", value=s.get("needs_context", ""), height=70, key=f"s_need_{idx}")
                s["buying_roles"] = st.text_input(f"購買與決策角色 ({sid})", value=s.get("buying_roles", ""), key=f"s_role_{idx}")
                s["contact_path"] = st.text_input(f"接觸路徑與行銷渠道 ({sid})", value=s.get("contact_path", ""), key=f"s_path_{idx}")
                s["overlap_gaps"] = st.text_input(f"重疊與缺口說明 ({sid})", value=s.get("overlap_gaps", ""), key=f"s_gap_{idx}")

    col_add_s, col_del_s = st.columns([1, 1])
    with col_add_s:
        if st.button("➕ 手動新增一個區隔"):
            new_id = f"S{len(segments)+1}"
            segments.append({
                "id": new_id, "name": f"新區隔 {new_id}", "dimension": "特徵維度", "inclusion": "符合資格",
                "exclusion": "排除特徵", "needs_context": "核心痛點情境", "buying_roles": "採購角色",
                "contact_path": "主要渠道", "overlap_gaps": "無"
            })
            st.session_state.segments = segments
            st.rerun()

    render_html("<div style='height: 25px;'></div>")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⬅️ 上一步：Persona 畫像", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_nav2:
        if st.button("下一步：目標市場評估與決策 (T) ➡️", type="primary", use_container_width=True):
            if len(st.session_state.segments) < 3:
                st.warning("⚠️ 依規格要求，至少需規劃 3 個可比較的市場區隔 (S1, S2, S3) 喔！")
            else:
                st.session_state.step = 3
                st.rerun()

# ==========================================
# STEP 3: T 目標市場評估與決策 (Targeting)
# ==========================================
elif st.session_state.step == 3:
    render_html(
        """
        <div class="guide-alert">
            <div class="guide-title">💡 小白心法 3：目標市場 (Targeting) —— 選擇比努力更重要！</div>
            <p class="guide-content">
                資源有限，你不可能同時取悅所有人。透過科學的 4 大評估條件與權重評分，選出最有爆發力、痛點最急迫的優先切入市場。
                <b>【嚴格業務規則防呆】</b>：權重總和必須嚴格等於 100%。若有任何一格「資料不足 (null)」，嚴禁機械排名，必須切換為「條件式決策 (conditional)」並寫明人工理由！
            </p>
        </div>
        """
    )

    criteria = st.session_state.criteria
    segments = st.session_state.segments
    ratings = st.session_state.ratings

    # 1. 權重檢查與調整
    st.markdown("#### ⚖️ 1. 四大條件標準與權重設定")
    w_sum = sum(c.get("weight", 0.0) for c in criteria)

    col_w_warn1, col_w_warn2 = st.columns([3, 1])
    with col_w_warn1:
        if abs(w_sum - 100.0) < 1e-4:
            st.success(f"✅ 權重總和正確：{w_sum:.1f}%")
        else:
            st.error(f"❌ 權重總和錯誤：目前合計 {w_sum:.1f}%，必須嚴格等於 100.0%！")
    with col_w_warn2:
        if st.button("🔄 一鍵校正為 100%"):
            eq_w = round(100.0 / len(criteria), 1)
            for c in criteria:
                c["weight"] = eq_w
            criteria[-1]["weight"] = 100.0 - eq_w * (len(criteria) - 1)
            st.session_state.criteria = criteria
            st.rerun()

    crit_cols = st.columns(len(criteria))
    for c_idx, c in enumerate(criteria):
        with crit_cols[c_idx]:
            render_html(f"<div style='background:rgba(30,41,59,0.7); border-radius:10px; padding:12px; border:1px solid rgba(255,255,255,0.08);'>")
            st.markdown(f"**{c.get('name')}**")
            c["weight"] = st.number_input(f"權重 % ({c.get('id')})", min_value=0.0, max_value=100.0, value=float(c.get("weight", 25.0)), step=5.0, key=f"crit_w_{c_idx}")
            c["standard"] = st.text_input(f"標準說明", value=c.get("standard", ""), key=f"crit_std_{c_idx}")
            render_html("</div>")

    st.markdown("---")
    st.markdown("#### 📋 2. 客群評分矩陣 (1~5 分 或 資料不足 null)")

    # 確保 ratings 矩陣覆蓋所有 segments x criteria
    existing_map = {(r["segment_id"], r["criterion_id"]): r for r in ratings}
    for s in segments:
        for c in criteria:
            key = (s["id"], c["id"])
            if key not in existing_map:
                ratings.append({"segment_id": s["id"], "criterion_id": c["id"], "score": 3, "reason": "預設評估", "source_ids": ["SRC-01"]})
    st.session_state.ratings = ratings

    # 矩陣評分表格
    has_null = False
    for s in segments:
        with st.expander(f"客群 {s.get('id')}：{s.get('name')} 評分", expanded=True):
            r_cols = st.columns(len(criteria))
            for idx, c in enumerate(criteria):
                with r_cols[idx]:
                    r_entry = next((r for r in ratings if r["segment_id"] == s["id"] and r["criterion_id"] == c["id"]), None)
                    curr_score = r_entry.get("score") if r_entry else 3

                    # 選項：5, 4, 3, 2, 1, 或 "資料不足 (null)"
                    score_opts = [5, 4, 3, 2, 1, "資料不足 (null)"]
                    opt_idx = score_opts.index(curr_score) if curr_score in score_opts else 5

                    selected_opt = st.selectbox(
                        f"{c.get('name')} ({c.get('weight')}%)",
                        options=score_opts,
                        index=opt_idx,
                        key=f"rating_sel_{s.get('id')}_{c.get('id')}"
                    )

                    if selected_opt == "資料不足 (null)":
                        r_entry["score"] = None
                        has_null = True
                    else:
                        r_entry["score"] = int(selected_opt)

    # 3. 計算加權總分與排名演算法 (BR06/BR07)
    st.markdown("---")
    st.markdown("#### 🏆 3. 加權排名與決策演算法")

    tgt = st.session_state.target_decision
    ranking_results = []

    if has_null:
        st.warning("⚠️ 檢測到部分評分格位為『資料不足 (null)』！依據 BR07 規則：禁止機械算總分排名，系統已自動切換為『條件式決策 (conditional)』模式。請在下方填寫有理由的選擇！")
        tgt["mode"] = "conditional"
        tgt["ranking"] = None
    elif abs(w_sum - 100.0) > 1e-4:
        st.error("⚠️ 權重總和不為 100%，無法計算科學排名！請先修正上方權重。")
        tgt["ranking"] = None
    else:
        # 全部有分數，計算加權和
        for s in segments:
            sid = s["id"]
            total_w_score = 0.0
            for c in criteria:
                cid = c["id"]
                rentry = next((r for r in ratings if r["segment_id"] == sid and r["criterion_id"] == cid), None)
                sc = rentry["score"] if rentry and rentry["score"] is not None else 0
                total_w_score += (c["weight"] / 100.0) * sc
            ranking_results.append({
                "segment_id": sid,
                "segment_name": s["name"],
                "weighted_score": round(total_w_score, 2)
            })
        # 排序
        ranking_results.sort(key=lambda x: x["weighted_score"], reverse=True)
        for rk_idx, rk in enumerate(ranking_results, 1):
            rk["rank"] = rk_idx
        tgt["mode"] = "complete"
        tgt["ranking"] = ranking_results

        # 呈現得分榜單
        col_ranks = st.columns(len(ranking_results))
        for idx, rk in enumerate(ranking_results):
            with col_ranks[idx]:
                render_html(
                    f"""
                    <div style="background:rgba(22,30,46,0.8); border:2px solid {'#ec4899' if rk['rank']==1 else '#334155'}; border-radius:14px; padding:16px; text-align:center;">
                        <span style="font-size:1.8rem;">{'🥇' if rk['rank']==1 else ('🥈' if rk['rank']==2 else '🥉')}</span>
                        <h4 style="margin:5px 0; color:#f8fafc;">{rk['segment_id']} - {rk['segment_name']}</h4>
                        <div style="font-size:1.5rem; font-weight:800; color:#c084fc;">{rk['weighted_score']} 分</div>
                        <div style="color:#94a3b8; font-size:0.8rem;">加權綜合排名第 {rk['rank']} 名</div>
                    </div>
                    """
                )

    # 4. 人工決策面板 (BR08/BR09)
    st.markdown("#### 🎯 4. 人工選定優先目標市場與決策依據")
    seg_options = [s["id"] for s in segments]
    curr_sel = tgt.get("selected_segment_id")
    sel_idx = seg_options.index(curr_sel) if curr_sel in seg_options else 0

    new_sel_id = st.selectbox(
        "最終選定的優先目標市場 (Target Segment)：",
        options=seg_options,
        index=sel_idx,
        format_func=lambda x: f"{x} - {next((s['name'] for s in segments if s['id'] == x), x)}"
    )

    # 檢測是否有改選客群，若有則觸發 BR08/09 下游重檢警示
    if new_sel_id != tgt.get("selected_segment_id"):
        st.session_state.positioning["needs_review"] = True
        st.session_state.bmc_summary["needs_review"] = True
        st.toast(f"🔔 已改選目標客群為 {new_sel_id}！已自動標記市場定位 (P) 與 BMC 需重新檢核！", icon="⚠️")

    tgt["selected_segment_id"] = new_sel_id

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        tgt["reason"] = st.text_area("選擇該客群之關鍵理由 (Decision Reason)：", value=tgt.get("reason", ""), height=80, placeholder="說明為什麼選他？有哪些痛點與獲客優勢？")
        tgt["tradeoffs"] = st.text_area("未選其他客群之取捨代價 (Tradeoffs)：", value=tgt.get("tradeoffs", ""), height=80, placeholder="放棄了什麼？（例如放棄較高的單客營收上限，先換取快速驗證速度）")
    with col_d2:
        tgt["change_condition"] = st.text_area("改選或重新評估條件 (Change Condition)：", value=tgt.get("change_condition", ""), height=80, placeholder="何種情況下會推翻本次決策？（如 3 個月內註冊轉換率低於 3%）")
        tgt["next_check"] = st.text_input("下一步查核點 (Next Check)：", value=tgt.get("next_check", ""), placeholder="上線 Product Hunt 觀察自發性註冊數")

    tgt["human_confirmed"] = st.checkbox("✅ 我已完整審閱上述評估理由，確認以該客群作為核心目標市場 (human_confirmed=true)", value=tgt.get("human_confirmed", True))
    st.session_state.target_decision = tgt

    render_html("<div style='height: 25px;'></div>")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⬅️ 上一步：S 市場區隔", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_nav2:
        if st.button("下一步：市場定位與價值主張 (P) ➡️", type="primary", use_container_width=True):
            if not tgt.get("selected_segment_id"):
                st.warning("⚠️ 請務必選定一個目標市場才能繼續喔！")
            else:
                st.session_state.step = 4
                st.rerun()

# ==========================================
# STEP 4: P 市場定位與替代方案 (Positioning)
# ==========================================
elif st.session_state.step == 4:
    render_html(
        """
        <div class="guide-alert">
            <div class="guide-title">💡 小白心法 4：市場定位 (Positioning) —— 在心智中佔據不可取代的席位</div>
            <p class="guide-content">
                定位不是你對產品做了什麼，而是<b>你在消費者心目中建立了什麼認知</b>！
                以經典定位句型出發：面對既有的替代解法，你的產品憑什麼勝出？有哪些無法被輕易複製的核心價值？
            </p>
        </div>
        """
    )

    pos = st.session_state.positioning
    tgt = st.session_state.target_decision
    sel_id = tgt.get("selected_segment_id", "S1")
    sel_segment = next((s for s in st.session_state.segments if s["id"] == sel_id), None)
    sel_name = sel_segment.get("name", sel_id) if sel_segment else sel_id

    # 檢查是否需要重檢
    if pos.get("needs_review"):
        st.warning("⚠️ 提醒：先前步驟曾變更目標客群，請重新檢核當前定位內容是否仍契合選定之客群，確認後請勾選下方『人工確認』以清除警示。")

    col_p_top1, col_p_top2 = st.columns([3, 1])
    with col_p_top1:
        st.markdown(f"### 🎯 當前鎖定目標客群：`{sel_id} - {sel_name}`")
    with col_p_top2:
        if st.button("✨ AI 產生定位草稿與替代品對比", type="primary", use_container_width=True):
            with st.spinner("AI 正在根據選定客群與痛點推演定位聲明與替代方案差異..."):
                p_prompt = f"""
                你是一位資深品牌策略長。請為以下案例產出精準的市場定位 (Positioning) 與兩種替代方案對比。
                案例名稱：{st.session_state.case.get('name')}
                目標客群：{sel_name} (特徵：{sel_segment.get('inclusion') if sel_segment else ''})
                核心痛點與情境：{sel_segment.get('needs_context') if sel_segment else ''}
                Persona 現行作法：{st.session_state.persona.get('current_practice')}
                
                請以繁體中文撰寫，輸出為合法 JSON 物件，包含：
                - "need": 核心滿足之剛性需求 (一句話)
                - "product_name": 產品或服務名稱
                - "value": 核心承諾價值 (一句話)
                - "statement": 經典定位聲明 (格式：對於...面臨...我們的產品是一款...不同於...我們提供...)
                - "alternatives": 包含 2 個替代方案陣列，每個元素含：
                  - "name": 替代品名稱 (例如通用工具或傳統開會)
                  - "same_need_solution": 現行解法方式
                  - "proposed_difference": 我方產品提出的根本差異化優勢
                  - "to_verify": 後續需驗證之核心假設
                """
                try:
                    res_raw = generate_content_with_fallback(p_prompt, json_mode=True)
                    cleaned = clean_json_string(res_raw)
                    p_data = json.loads(cleaned)
                    for k in ["need", "product_name", "value", "statement", "alternatives"]:
                        if k in p_data:
                            pos[k] = p_data[k]
                    pos["needs_review"] = False
                    st.session_state.positioning = pos
                    st.success("🎉 定位草稿與替代方案生成成功！")
                    st.rerun()
                except Exception as e:
                    st.error("生成定位失敗。請檢查輸入資料、金鑰權限與配額後重試；原始錯誤內容不顯示。")

    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        pos["product_name"] = st.text_input("產品 / 品牌名稱", value=pos.get("product_name", st.session_state.case.get("name", "")), placeholder="例：協作台 SyncDeck")
        pos["need"] = st.text_area("核心滿足需求 (Need)", value=pos.get("need", ""), height=70, placeholder="跨時區非同步協同、消滅冗長無效進度會議...")
        pos["value"] = st.text_area("核心價值主張 (Value Proposition)", value=pos.get("value", ""), height=70, placeholder="以 AI 自動統整專案脈絡，省下每週 60% 開會彙報時間...")
    with col_p2:
        st.markdown("#### 📣 定位聲明 (Positioning Statement)")
        pos["statement"] = st.text_area(
            "完整定位聲明句型",
            value=pos.get("statement", ""),
            height=165,
            placeholder="對於 [目標客群]，面臨 [核心痛點]，我們的 [產品名] 是一款 [產品類別]。不同於 [替代品]，我們提供 [獨特差異與效益]..."
        )

    render_html(
        f"""
        <div class="statement-card">
            <div style="font-size:0.85rem; color:#f472b6; font-weight:700; text-transform:uppercase; margin-bottom:6px;">✨ 定位核心宣言預覽</div>
            <p class="statement-text">「{pos.get('statement', '尚未產生定位聲明...')}」</p>
        </div>
        """
    )

    st.markdown("#### ⚔️ 現有替代方案與差異化對比 (Alternatives)")
    alts = pos.get("alternatives", [])
    if not alts:
        alts = [
            {"id": "ALT-01", "name": "替代品 A (如通用筆記看板)", "same_need_solution": "手動建立卡片與更新", "proposed_difference": "AI 主動彙整進度，省去手動維護", "to_verify": "使用者是否信任 AI 摘要"},
            {"id": "ALT-02", "name": "替代品 B (如每日線上晨會)", "same_need_solution": "全員開會逐一報告", "proposed_difference": "非同步智慧簽到，釋放專注工時", "to_verify": "主管在未開會時是否感到安心"}
        ]
        pos["alternatives"] = alts

    alt_cols = st.columns(len(alts))
    for a_idx, alt in enumerate(alts):
        with alt_cols[a_idx]:
            render_html(f"<div style='background:rgba(22,30,46,0.75); border-radius:12px; padding:16px; border:1px solid rgba(255,255,255,0.08);'>")
            st.markdown(f"**替代方案 {a_idx+1}：**")
            alt["name"] = st.text_input(f"競爭者/現行作法名稱", value=alt.get("name", ""), key=f"alt_n_{a_idx}")
            alt["same_need_solution"] = st.text_area(f"他的解法", value=alt.get("same_need_solution", ""), height=65, key=f"alt_sol_{a_idx}")
            alt["proposed_difference"] = st.text_area(f"我方提出之核心差異", value=alt.get("proposed_difference", ""), height=65, key=f"alt_diff_{a_idx}")
            alt["to_verify"] = st.text_input(f"後續驗證重點", value=alt.get("to_verify", ""), key=f"alt_ver_{a_idx}")
            render_html("</div>")

    pos["human_confirmed"] = st.checkbox("✅ 我已審閱並人工確認上述市場定位與替代品差異 (human_confirmed=true)", value=pos.get("human_confirmed", True))
    if pos["human_confirmed"]:
        pos["needs_review"] = False
    st.session_state.positioning = pos

    render_html("<div style='height: 25px;'></div>")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⬅️ 上一步：T 目標決策", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with col_nav2:
        if st.button("下一步：行銷 4P 組合策略 ➡️", type="primary", use_container_width=True):
            if not pos.get("product_name") or not pos.get("statement"):
                st.warning("⚠️ 請確認已填寫產品名稱與定位聲明喔！")
            else:
                st.session_state.step = 5
                st.rerun()

# ==========================================
# STEP 5: 行銷 4P 組合策略 (Marketing 4P Mix)
# ==========================================
elif st.session_state.step == 5:
    render_html(
        """
        <div class="guide-alert">
            <div class="guide-title">💡 小白心法 5：行銷 4P 組合 (Marketing Mix) —— 將定位化為市場落地實踐</div>
            <p class="guide-content">
                定位確立後，如何落地？經典 4P 提供最全方位的實戰框架：
                <b>Product (產品策略)</b> 打磨核心競爭力；<b>Price (價格策略)</b> 設計獲利架構與價值錨點；
                <b>Place (通路策略)</b> 規劃用戶觸達旅程；<b>Promotion (推廣策略)</b> 設計引爆點 Slogan 與吸睛 Hook！
            </p>
        </div>
        """
    )

    four_p = st.session_state.marketing_4p
    pos = st.session_state.positioning
    tgt = st.session_state.target_decision
    sel_id = tgt.get("selected_segment_id", "S1")
    sel_segment = next((s for s in st.session_state.segments if s["id"] == sel_id), None)

    col_4p_top1, col_4p_top2 = st.columns([3, 1])
    with col_4p_top1:
        st.markdown("### 📦 實戰行銷 4P 組合方案")
    with col_4p_top2:
        if st.button("✨ AI 推薦 4P 行銷組合策略", type="primary", use_container_width=True):
            with st.spinner("AI 正在根據 STP 定位推演全套 4P 實戰策略..."):
                p4_prompt = f"""
                你是一位頂尖行銷策略操盤手。請根據以下 STP 市場定位資訊，推演出一套高度具備商業可行性與傳播力的行銷 4P 組合策略。
                產品名稱：{pos.get('product_name')}
                目標客群：{sel_segment.get('name') if sel_segment else ''}
                核心價值主張：{pos.get('value')}
                定位聲明：{pos.get('statement')}
                
                請以繁體中文撰寫，輸出為合法 JSON 物件，包含四大模組：
                1. "product":
                   - "core_features": 核心功能與服務特色
                   - "packaging_spec": 規格與交付形式
                   - "brand_tone": 品牌個性與調性
                   - "usp": 獨特賣點 (USP)
                2. "price":
                   - "pricing_model": 收費模式 (例如：訂閱制、免費增值、買斷)
                   - "price_tier": 價格分級帶與具體金額規劃
                   - "discount_strategy": 折扣與激勵誘因策略
                   - "value_anchor": 價值錨定比較 (告訴用戶相較於其他成本有多划算)
                3. "place":
                   - "channels": 主要接觸與銷售通路
                   - "onboarding_path": 顧客體驗與快速導入轉換路徑
                   - "partnerships": 通路夥伴與生態同盟
                4. "promotion":
                   - "slogan": 一句吸睛且好記的核心行銷宣傳標語 Slogan
                   - "content_strategy": 內容行銷主軸與切角
                   - "growth_hooks": 獲客鉤子與試用活動 (Hook)
                   - "community": 社群口碑與社群營造策略
                """
                try:
                    res_raw = generate_content_with_fallback(p4_prompt, json_mode=True)
                    cleaned = clean_json_string(res_raw)
                    new_4p = json.loads(cleaned)
                    for k in ["product", "price", "place", "promotion"]:
                        if k in new_4p:
                            four_p[k] = new_4p[k]
                    st.session_state.marketing_4p = four_p
                    st.success("🎉 行銷 4P 組合推演成功！請在下方檢視與微調。")
                    st.rerun()
                except Exception as e:
                    st.error("4P 推演失敗。請檢查輸入資料、金鑰權限與配額後重試；原始錯誤內容不顯示。")

    # 4P 編輯卡片
    col_p_prod, col_p_price = st.columns(2)
    with col_p_prod:
        render_html("<div class='p-box product'><div class='p-box-title'>📦 1. 產品策略 (Product)</div>")
        prod = four_p.get("product", {})
        prod["core_features"] = st.text_area("核心功能特色", value=prod.get("core_features", ""), height=75)
        prod["packaging_spec"] = st.text_input("規格與交付形式", value=prod.get("packaging_spec", ""))
        prod["brand_tone"] = st.text_input("品牌調性", value=prod.get("brand_tone", ""))
        prod["usp"] = st.text_area("獨特賣點 (USP)", value=prod.get("usp", ""), height=75)
        four_p["product"] = prod
        render_html("</div>")

    with col_p_price:
        render_html("<div class='p-box price'><div class='p-box-title'>💰 2. 價格策略 (Price)</div>")
        price = four_p.get("price", {})
        price["pricing_model"] = st.text_input("收費模式", value=price.get("pricing_model", ""))
        price["price_tier"] = st.text_area("價格分級帶", value=price.get("price_tier", ""), height=75)
        price["discount_strategy"] = st.text_input("促銷與折讓策略", value=price.get("discount_strategy", ""))
        price["value_anchor"] = st.text_area("價值錨定比較", value=price.get("value_anchor", ""), height=75)
        four_p["price"] = price
        render_html("</div>")

    col_p_place, col_p_promo = st.columns(2)
    with col_p_place:
        render_html("<div class='p-box place'><div class='p-box-title'>🌐 3. 通路策略 (Place)</div>")
        place = four_p.get("place", {})
        place["channels"] = st.text_area("主要接觸與銷售渠道", value=place.get("channels", ""), height=75)
        place["onboarding_path"] = st.text_area("轉換與導入路徑", value=place.get("onboarding_path", ""), height=75)
        place["partnerships"] = st.text_input("通路夥伴生態", value=place.get("partnerships", ""))
        four_p["place"] = place
        render_html("</div>")

    with col_p_promo:
        render_html("<div class='p-box promotion'><div class='p-box-title'>🚀 4. 推廣策略 (Promotion)</div>")
        promo = four_p.get("promotion", {})
        promo["slogan"] = st.text_input("宣傳標語 Slogan", value=promo.get("slogan", ""))
        promo["content_strategy"] = st.text_area("內容行銷切角", value=promo.get("content_strategy", ""), height=75)
        promo["growth_hooks"] = st.text_area("獲客誘餌 (Growth Hook)", value=promo.get("growth_hooks", ""), height=75)
        promo["community"] = st.text_input("社群與口碑營造", value=promo.get("community", ""))
        four_p["promotion"] = promo
        render_html("</div>")

    st.session_state.marketing_4p = four_p

    render_html("<div style='height: 25px;'></div>")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⬅️ 上一步：P 市場定位", use_container_width=True):
            st.session_state.step = 4
            st.rerun()
    with col_nav2:
        if st.button("下一步：BMC 與假說驗證 ➡️", type="primary", use_container_width=True):
            st.session_state.step = 6
            st.rerun()

# ==========================================
# STEP 6: BMC 關鍵兩格與假說驗證行動
# ==========================================
elif st.session_state.step == 6:
    render_html(
        """
        <div class="guide-alert">
            <div class="guide-title">💡 小白心法 6：BMC 兩格串接與精實假說驗證 (Verification)</div>
            <p class="guide-content">
                你的定位與商業模式是否能經受市場考驗？我們把 STP 成果對齊到<b>商業模式圖 (BMC) 的兩大命脈：目標客層與價值主張</b>。
                同時，依照 BR10 規格，擬定 <b>最多 3 項關鍵假說驗證行動</b>，設定明確可衡量的「判定門檻」與「假設不成立時的修正策略 (if_false)」！
            </p>
        </div>
        """
    )

    bmc = st.session_state.bmc_summary
    pos = st.session_state.positioning
    tgt = st.session_state.target_decision
    sel_id = tgt.get("selected_segment_id", "S1")
    sel_segment = next((s for s in st.session_state.segments if s["id"] == sel_id), None)
    sel_name = sel_segment.get("name", sel_id) if sel_segment else sel_id

    # 自動同步 T 與 P 至 BMC
    bmc["target_segment_id"] = sel_id
    bmc["customer_segments"] = bmc.get("customer_segments", f"{sel_name} 之主要決策主管與成員")
    bmc["value_proposition"] = bmc.get("value_proposition", pos.get("value", ""))

    st.markdown("#### 🏢 1. 商業模式圖 (BMC) 核心兩格摘要")
    col_bmc1, col_bmc2 = st.columns(2)
    with col_bmc1:
        render_html("<div class='bmc-box'><div class='bmc-box-header'>👥 目標客層 (Customer Segments)</div>")
        st.caption(f"引用自目標決策：`{sel_id}`")
        bmc["customer_segments"] = st.text_area("具體客層特徵描述", value=bmc.get("customer_segments", ""), height=90)
        render_html("</div>")
    with col_bmc2:
        render_html("<div class='bmc-box'><div class='bmc-box-header'>🎁 價值主張 (Value Proposition)</div>")
        st.caption(f"引用自定位承諾：`{pos.get('product_name')}`")
        bmc["value_proposition"] = st.text_area("核心價值承諾", value=bmc.get("value_proposition", ""), height=90)
        render_html("</div>")

    bmc["other_impacts"] = st.text_input("對商業模式其他格位之衍生影響 (如關鍵夥伴、主要成本)", value=bmc.get("other_impacts", "需串接 Slack/GitHub API；主要成本為雲端運算與 LLM API 推論"))
    st.session_state.bmc_summary = bmc

    st.markdown("---")
    col_ver_top1, col_ver_top2 = st.columns([3, 1])
    with col_ver_top1:
        st.markdown("#### 🔬 2. 關鍵假說驗證行動 (上限 3 項，含決策門檻與修正策略)")
    with col_ver_top2:
        if st.button("✨ AI 推薦驗證行動", type="primary", use_container_width=True):
            with st.spinner("AI 正在推演精實創業假說驗證行動..."):
                ver_prompt = f"""
                你是一位精實創業導師。請根據產品「{pos.get('product_name')}」，針對其目標客群「{sel_name}」與價值主張「{pos.get('value')}」，
                規劃 3 項最高優先級的假說驗證行動。
                請以繁體中文撰寫，輸出為合法 JSON 陣列，每個元素包含：
                - "priority": 1, 2, 3
                - "method": 驗證方法 (例如深度訪談、Landing Page 廣告點擊測試、原型試用留存追蹤)
                - "audience": 驗證對象
                - "data_to_collect": 收集資料指標
                - "threshold": 判定成功之數據門檻
                - "threshold_reason": 設定此門檻的商業理由
                - "owner": 負責人代號
                - "due": 完成期限
                - "if_false": 若驗證不成立時的退路/修正策略 (Pivot)
                """
                try:
                    res_raw = generate_content_with_fallback(ver_prompt, json_mode=True)
                    cleaned = clean_json_string(res_raw)
                    new_vers = json.loads(cleaned)
                    if isinstance(new_vers, list):
                        st.session_state.verification_actions = new_vers[:3]
                        st.success("🎉 3 項驗證行動推演成功！")
                        st.rerun()
                except Exception as e:
                    st.error("推演驗證失敗。請檢查輸入資料、金鑰權限與配額後重試；原始錯誤內容不顯示。")

    actions = st.session_state.verification_actions
    for idx, act in enumerate(actions):
        with st.expander(f"行動 #{act.get('priority', idx+1)}：{act.get('method', '未命名行動')}", expanded=True):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                act["priority"] = idx + 1
                act["method"] = st.text_input(f"驗證方法 (#{idx+1})", value=act.get("method", ""), key=f"act_m_{idx}")
                act["audience"] = st.text_input(f"驗證對象 (#{idx+1})", value=act.get("audience", ""), key=f"act_aud_{idx}")
                act["data_to_collect"] = st.text_input(f"收集指標/資料 (#{idx+1})", value=act.get("data_to_collect", ""), key=f"act_data_{idx}")
                act["threshold"] = st.text_input(f"判定成功門檻 (#{idx+1})", value=act.get("threshold", ""), key=f"act_th_{idx}")
            with col_a2:
                act["threshold_reason"] = st.text_input(f"門檻設定理由 (#{idx+1})", value=act.get("threshold_reason", ""), key=f"act_thr_{idx}")
                act["owner"] = st.text_input(f"負責人 (#{idx+1})", value=act.get("owner", ""), key=f"act_own_{idx}")
                act["due"] = st.text_input(f"完成期限 (#{idx+1})", value=act.get("due", "2026-11-01"), key=f"act_due_{idx}")
                act["if_false"] = st.text_area(f"⚠️ 若假設不成立時的修正策略 (if_false)", value=act.get("if_false", ""), height=65, key=f"act_iff_{idx}")

    # 主張台帳與來源管理抽屜
    with st.expander("📚 查看主張台帳 (Claims) 與來源管理 (Sources)"):
        st.markdown("**主張台帳清單 (Claims Register)**")
        for clm in st.session_state.claims:
            st.markdown(f"- `[{clm.get('id')}]` {clm.get('text')} ｜ 性質: `{clm.get('nature')}` ｜ 狀態: `{clm.get('verification_status')}` ｜ 理由: {clm.get('human_reason')}")

    render_html("<div style='height: 25px;'></div>")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⬅️ 上一步：行銷 4P 組合", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
    with col_nav2:
        if st.button("下一步：提案預覽、版本保存與匯出 ➡️", type="primary", use_container_width=True):
            st.session_state.step = 7
            st.rerun()

# ==========================================
# STEP 7: 提案預覽、版本管理與雙格式匯出
# ==========================================
elif st.session_state.step == 7:
    render_html(
        """
        <div class="guide-alert">
            <div class="guide-title">💡 小白心法 7：提案成型、版本封存與雙格式匯出</div>
            <p class="guide-content">
                恭喜！您已完整建立 Persona ➔ STP ➔ 4P ➔ BMC ➔ 假說驗證 的完整策略閉環。
                在此您可以<b>保存草稿版本</b>（單調遞增並記錄變更歷程），並一鍵匯出<b>標準 Markdown 報告 (.md)</b> 與 <b>標準 JSON 規格檔 (.json)</b>，雙檔具備相同 SHA-256 驗證指紋！
            </p>
        </div>
        """
    )

    rev = st.session_state.revision
    case = st.session_state.case

    # 1. 提案版本管理
    st.markdown("#### 🔖 1. 版本控制與草稿保存")
    col_v1, col_v2, col_v3 = st.columns([1, 2, 1])
    with col_v1:
        st.info(f"當前提案版本：**v{rev.get('version', 1)}**")
        st.caption(f"提案編號: `{rev.get('proposal_id', 'PROP-G01')}`")
    with col_v2:
        change_note = st.text_input("本次修訂紀錄說明 (Change Log)", placeholder="例：調整 S1 區隔納入條件，並補齊 4P 價格分級策略")
    with col_v3:
        if st.button("💾 保存為新版本", type="primary", use_container_width=True):
            old_ver = rev.get("version", 1)
            new_ver = old_ver + 1
            rev["version"] = new_ver
            rev["parent_version"] = old_ver
            rev["saved_at"] = datetime.now().isoformat()
            log_msg = change_note if change_note.strip() else f"保存新版本 v{new_ver}"
            rev["change_log"].append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] v{new_ver}: {log_msg}")
            st.session_state.revision = rev
            st.success(f"🎉 成功保存為版本 v{new_ver}！")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📤 2. 雙格式一鍵匯出 (Markdown + JSON)")

    # 產生雙格式字串
    full_state = {
        "case": st.session_state.case,
        "persona": st.session_state.persona,
        "segments": st.session_state.segments,
        "criteria": st.session_state.criteria,
        "ratings": st.session_state.ratings,
        "target_decision": st.session_state.target_decision,
        "positioning": st.session_state.positioning,
        "marketing_4p": st.session_state.marketing_4p,
        "bmc_summary": st.session_state.bmc_summary,
        "verification_actions": st.session_state.verification_actions,
        "sources": st.session_state.sources,
        "claims": st.session_state.claims,
        "revision": st.session_state.revision
    }

    md_content = export_proposal_markdown(full_state)
    json_content = export_proposal_json(full_state)
    canonical_sha = compute_sha256(json_content)

    render_html(
        f"""
        <div style="background:rgba(22,30,46,0.6); border:1px dashed #8b5cf6; border-radius:12px; padding:14px; margin-bottom:18px;">
            <b style="color:#c084fc;">🔒 快照一致性校驗指紋 (Canonical SHA-256)：</b>
            <code style="color:#f8fafc; font-size:0.85rem;">{canonical_sha}</code>
            <div style="color:#94a3b8; font-size:0.8rem; margin-top:4px;">Markdown 與 JSON 匯出檔均帶有此相同雜湊碼，確保內容完全同一，杜絕版本錯亂。</div>
        </div>
        """
    )

    col_dl1, col_dl2, col_dl3 = st.columns(3)
    filename_base = f"{case.get('workspace_id', 'G01')}_v{rev.get('version', 1)}"

    with col_dl1:
        st.download_button(
            label="📄 下載 Markdown 報告 (.md)",
            data=md_content,
            file_name=f"{filename_base}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col_dl2:
        st.download_button(
            label="📦 下載 JSON 資料快照 (.json)",
            data=json_content,
            file_name=f"{filename_base}.json",
            mime="application/json",
            use_container_width=True
        )
    with col_dl3:
        # 下載驗收修改用的 xlsx
        excel_path = os.path.join(os.path.dirname(__file__), "市場定位分析_Web_App_驗收修改意見表.xlsx")
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f_excel:
                st.download_button(
                    label="📊 下載功能驗收修改表 (.xlsx)",
                    data=f_excel.read(),
                    file_name="市場定位分析_Web_App_驗收修改意見表.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.button("驗收表生成中...", disabled=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 👁️ 3. 提案報告即時預覽")
    with st.expander("展開即時檢視完整 Markdown 報告渲染", expanded=True):
        st.markdown(md_content)

    render_html("<div style='height: 25px;'></div>")
    if st.button("⬅️ 回到上一步：BMC 與驗證", use_container_width=True):
        st.session_state.step = 6
        st.rerun()

# ==========================================
# 頁尾資訊
# ==========================================
render_html(
    """
    <div style="text-align:center; padding:30px 0 10px 0; color:#64748b; font-size:0.85rem; border-top:1px solid rgba(255,255,255,0.06); margin-top:40px;">
        AI 市場定位分析師 (行銷 STP & 4P) v1.0.0 ｜ 支援 Google Gemini BYOK 0 成本架構 ｜ 具備多模型自動備援機制
    </div>
    """
)
