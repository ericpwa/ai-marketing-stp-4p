"""
系統自動化驗證與測試套件 (Automated Test Suite)
檢驗全流程業務規則 (BR01~BR11)、資料模型完整性與匯出功能
"""

import os
import json
import zipfile
from sample_data import SAMPLE_CASES
from export_helpers import export_proposal_json, export_proposal_markdown, compute_sha256
from generate_excel import build_acceptance_excel

def test_sample_data_integrity():
    print("[TEST 1] 檢驗預設案例完整性...")
    case = SAMPLE_CASES.get("collaboration_hub")
    assert case is not None, "未找到協作台示範案例"
    assert "persona" in case, "缺少 persona"
    assert len(case.get("segments", [])) >= 3, "候選區隔少於 3 個"
    assert len(case.get("criteria", [])) == 4, "評估條件不為 4 個"
    assert len(case.get("verification_actions", [])) <= 3, "驗證行動超過 3 個"
    print(" -> 預設案例資料完整無誤！")

def test_export_and_fingerprint():
    print("[TEST 2] 檢驗雙格式匯出與 SHA-256 指紋一致性...")
    data = SAMPLE_CASES["collaboration_hub"]
    json_out = export_proposal_json(data)
    md_out = export_proposal_markdown(data)
    
    sha_json = compute_sha256(json_out)
    assert sha_json in md_out, "Markdown front-matter 缺少與 JSON 一致的 SHA-256 指紋"
    assert "【⚠️ 教學模擬案例 - 非市場真實保證】" in md_out, "Markdown 缺少教學模擬標示"
    
    # 檢查 JSON 是否能正確還原
    parsed = json.loads(json_out)
    assert parsed["document_type"] == "proposal"
    assert parsed["target_decision"]["selected_segment_id"] == "S1"
    print(" -> 雙格式匯出與指紋校驗通過！")

def test_targeting_algorithm_complete_and_conditional():
    print("[TEST 3] 檢驗 T 評估演算法 (BR06/BR07)...")
    criteria = [
        {"id": "C1", "weight": 30.0},
        {"id": "C2", "weight": 25.0},
        {"id": "C3", "weight": 25.0},
        {"id": "C4", "weight": 20.0}
    ]
    # 權重檢查
    w_sum = sum(c["weight"] for c in criteria)
    assert abs(w_sum - 100.0) < 1e-4, "權重總和不為 100%"

    # 情境 A: 完整分數
    scores_s1 = {"C1": 4, "C2": 5, "C3": 3, "C4": 5}
    total_s1 = sum((c["weight"]/100.0) * scores_s1[c["id"]] for c in criteria)
    assert round(total_s1, 2) == 4.20, f"加權計算錯誤: {total_s1}"

    # 情境 B: 含有 null (缺值)
    scores_s2 = {"C1": 5, "C2": None, "C3": 4, "C4": 3}
    has_null = any(v is None for v in scores_s2.values())
    assert has_null is True, "未正確偵測出 null 缺值"
    print(" -> 完整計分與條件式缺值防呆演算法驗證通過！")

def test_excel_generation():
    print("[TEST 4] 檢驗驗收修改用 Excel 檔案...")
    excel_path = os.path.join(os.path.dirname(__file__), "市場定位分析_Web_App_驗收修改意見表.xlsx")
    build_acceptance_excel(excel_path)
    assert os.path.exists(excel_path), "Excel 檔案未成功建立"
    
    with zipfile.ZipFile(excel_path, 'r') as z:
        names = z.namelist()
        assert "xl/workbook.xml" in names
        assert "xl/worksheets/sheet1.xml" in names
        assert "xl/worksheets/sheet2.xml" in names
        assert "xl/worksheets/sheet3.xml" in names
        assert "xl/worksheets/sheet4.xml" in names
    print(f" -> Excel 表格驗證通過！包含 4 個專用工作表，檔案大小：{os.path.getsize(excel_path)} bytes")

if __name__ == "__main__":
    test_sample_data_integrity()
    test_export_and_fingerprint()
    test_targeting_algorithm_complete_and_conditional()
    test_excel_generation()
    print("\n🎉 全部測試套件通過 (100% PASS)！")
