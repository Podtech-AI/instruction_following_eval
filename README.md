# IFEval: Instruction Following Eval

This is not an officially supported Google product.

This repository contains source code and data for
[Instruction Following Evaluation for Large Language Models](arxiv.org/abs/2311.07911)

## Dependencies

Please make sure that all required python packages are installed via:

```
pip3 install -r requirements.txt
```

## How to run

You need to create a jsonl file with two entries: prompt and response.
Then, call `evaluation_main` from the parent folder of
instruction_following_eval. For example:

```bash
# Content of `--input_response_data` should be like:
# {"prompt": "Write a 300+ word summary ...", "response": "PUT YOUR MODEL RESPONSE HERE"}
# {"prompt": "I am planning a trip to ...", "response": "PUT YOUR MODEL RESPONSE HERE"}
# ...
python3 -m instruction_following_eval.evaluation_main   --input_data=instruction_following_eval/data/input_data.jsonl   --input_response_data=instruction_following_eval/data/input_response_data_gpt4_20231107_145030.jsonl   --output_dir=instruction_following_eval/data/test_output
```

## 日本語対応 (Japanese Support)

このリポジトリには日本語対応の指示評価ライブラリが含まれています。

### 主要な機能

1. **日本語対応指示ライブラリ (`ja_instructions.py`)**
   - 29個の指示クラスを日本語化
   - 日本語特有の処理に最適化
   - 簡易的な言語検出機能

2. **高精度形態素解析による単語数カウント**
   - [Sudachi](https://github.com/WorksApplications/Sudachi)形態素解析ライブラリを統合
   - 従来の文字数ベースから真の単語数ベースに改善
   - 内容語（名詞、動詞、形容詞、副詞）のみをカウント

3. **日本語用ユーティリティ (`jp_instructions_util.py`)**
   - 日本語文分割
   - 形態素解析による単語数カウント
   - 日本語キーワード生成

### テスト結果

#### 完全網羅テスト (`test_ja_instructions.py`)
- **29クラス全て対象**
- **成功率: 93.1% (27/29件成功)**
- **特筆すべき改善:**
  - 単語数チェッカーでSudachi形態素解析による高精度評価を実現


### 使用例

```python
# 日本語指示チェッカーの使用
from ja_instructions import NumberOfWords

words_checker = NumberOfWords("test")
description = words_checker.build_description(num_words=5, relation="以上", lang='ja')
# 出力: "以上5単語で回答してください。"

# Sudachi形態素解析による単語数カウント
import jp_instructions_util as util
text = "これは日本語の形態素解析のテストです。"
word_count = util.count_words(text, lang='ja')
# 出力: 5 (従来の文字数ベースでは15文字)
```

### テスト実行

```bash
# 日本語対応指示ライブラリの完全テスト
python3 test_ja_instructions.py

```

```以下のデータはサンプルデータから削除
// {"key": 2785, "prompt": "What is inside Shinto shrines? Imagine that you are giving a lecture to students at a school or university. Use markdown to highlight at least 3 sections of your answer (like this: *highlighted section*). Your answer must also contain at least 3 placeholders (an example of a placeholder is [address]).", "instruction_id_list": ["detectable_format:number_highlighted_sections", "detectable_content:number_placeholders"], "kwargs": [{"num_highlights": 3}, {"num_placeholders": 3}]}

## Reference

If you use our work, please consider citing our preprint:

```
@article{zhou2023instruction,
  title={Instruction-Following Evaluation for Large Language Models},
  author={Zhou, Jeffrey and Lu, Tianjian and Mishra, Swaroop and Brahma, Siddhartha and Basu, Sujoy and Luan, Yi and Zhou, Denny and Hou, Le},
  journal={arXiv preprint arXiv:2311.07911},
  year={2023}
}
```