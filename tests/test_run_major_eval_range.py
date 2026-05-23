import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Assuming run_major_eval.py is in the parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))
import run_major_eval

@pytest.fixture
def mock_csv_path(tmp_path):
    # Create a dummy CSV file for testing
    csv_content = """学科门类代码,学科门类,专业类代码,专业类,专业代码,专业名称
01,哲学,0101,哲学类,010101,哲学
02,经济学,0201,经济学类,020101,经济学
03,法学,0301,法学类,030101,法学
04,教育学,0401,教育学类,040101,教育学
"""
    csv_file = tmp_path / "本科专业目录_2025.csv"
    csv_file.write_text(csv_content, encoding="utf-8-sig")
    return csv_file

@pytest.fixture
def mock_prompt_path(tmp_path):
    prompt_file = tmp_path / "跑专业的提示词-v2.txt"
    prompt_file.write_text("Prompt template for [专业名称]", encoding="utf-8")
    return prompt_file

@pytest.fixture(autouse=True)
def setup_run_major_eval_paths(mock_csv_path, mock_prompt_path, tmp_path):
    with (patch.object(run_major_eval, 'CSV_PATH', mock_csv_path),
          patch.object(run_major_eval, 'PROMPT_PATH', mock_prompt_path),
          patch.object(run_major_eval, 'OUTPUT_DIR', tmp_path / "data" / "专业评估报告")):
        yield

def test_run_major_eval_with_category_range():
    # Simulate command line arguments: --start 01 --end 03
    test_args = ["run_major_eval.py", "--start", "01", "--end", "03"]

    with (patch.object(sys, 'argv', test_args),
          patch.object(run_major_eval, 'run_category') as mock_run_category,
          patch.object(run_major_eval, 'show_status')):

        run_major_eval.main()

        # Assert that run_category was called for '01', '02', '03'
        assert mock_run_category.call_count == 3
        mock_run_category.assert_any_call("01", None, False)
        mock_run_category.assert_any_call("02", None, False)
        mock_run_category.assert_any_call("03", None, False)
