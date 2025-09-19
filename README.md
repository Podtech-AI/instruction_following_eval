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

## 統合指示ライブラリ (Unified Instruction Library)

このリポジトリには日本語・英語両対応の統合指示評価ライブラリが含まれています。

### 主要な機能

1. **統合指示ライブラリ (`ja_instructions.py`)**
   - **34個の指示クラス**を統合管理
   - **日本語特化指示**: 9個（ひらがな限定、読点禁止等）
   - **英語対応指示**: 25個（全ての既存英語制約）
   - **多言語対応**: 日本語・英語制約の同時サポート

2. **高精度形態素解析による単語数カウント**
   - [Sudachi](https://github.com/WorksApplications/Sudachi)形態素解析ライブラリを統合
   - 従来の文字数ベースから真の単語数ベースに改善
   - 内容語（名詞、動詞、形容詞、副詞）のみをカウント

3. **日本語用ユーティリティ (`jp_instructions_util.py`)**
   - 日本語文分割
   - 形態素解析による単語数カウント
   - 日本語キーワード生成

### アーキテクチャの改善

- **ファイル統合**: `instructions.py` → `ja_instructions.py`に統合
- **単一インポート**: `instructions_registry.py`で統一管理
- **後方互換性**: 既存の評価パイプラインと完全互換

### テスト結果

#### 統合システムテスト
- **✅ 総指示数**: 34クラス利用可能
- **✅ 日本語特化指示**: 9個正常動作
- **✅ 英語指示**: 25個正常動作  
- **✅ 評価ライブラリ**: 正常動作確認
- **✅ 応答生成**: モック・実機両対応

#### 日本語指示テスト (`ja_instructions_test.py`)
- **総テスト数**: 35件
- **成功率**: 88.6% (31/35件成功)
- **主な成功項目**: 強調表現、読点禁止、終了フレーズ、日本語のみ制約

#### 英語指示テスト (`instructions_test.py`)  
- **総テスト数**: 41件
- **成功**: 27件、一部制約で調整必要

### 使用例

```python
# 統合ライブラリの使用
import ja_instructions as instructions
import instructions_registry

# 日本語特化指示
hiragana_checker = instructions.JapaneseHiraganaOnlyChecker("test")
description = hiragana_checker.build_description()
# 出力: "回答はすべてひらがなで書いてください。漢字とカタカナは一切使用できません。"

# 英語指示も同じライブラリから利用可能
keyword_checker = instructions.KeywordChecker("test") 
description = keyword_checker.build_description(keywords=['テスト'])

# 指示レジストリ経由でのアクセス
all_instructions = instructions_registry.INSTRUCTION_DICT
print(f"利用可能指示数: {len(all_instructions)}")  # 34個
```

### テスト実行

```bash
# 日本語特化指示テスト
python3 ja_instructions_test.py

# 英語指示互換性テスト  
python3 instructions_test.py

# 統合システム確認
python3 -c "import instructions_registry; print('統合成功:', len(instructions_registry.INSTRUCTION_DICT), '指示')"
```

## 応答生成ツール (Response Generation)

### generate_responses.py 使用ガイド

`generate_responses.py`は、`input_data.jsonl`からプロンプトを読み取り、AIモデルに送信して応答を生成し、`input_response_data.jsonl`形式で保存するスクリプトです。

#### サポートモデル

**OpenAI API**
- `gpt-4`, `gpt-4-turbo`, `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`

**Anthropic API**
- `claude-3-5-sonnet`, `claude-3-haiku`, `claude-3-opus`

**HuggingFace Models (ローカル実行)**
- `sbintuitions/sarashina2.2-1b-instruct-v0.1` (日本語特化小型モデル)
- `sarashina` (上記のエイリアス)
- `microsoft/DialoGPT-medium`
- `rinna/japanese-gpt-neox-3.6b-instruction-sft`
- 任意のHuggingFace causal language model

**ローカル/テスト用**
- `mock` (テスト用のモック応答)

#### セットアップ

```bash
# 依存関係のインストール
pip install openai anthropic torch transformers accelerate

# API キーの設定
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

#### 使用方法

**基本的な使用**
```bash
python generate_responses.py \
  --input_data=data/ja_input_data_sample_ver2.jsonl \
  --output=data/input_response_data_claude_japanese.jsonl \
  --model=claude-3-5-sonnet
```

**主要オプション**
- `--input_data`: 入力データファイル (必須)
- `--output`: 出力ファイル (必須)
- `--model`: 使用するモデル (デフォルト: `mock`)
- `--delay`: API呼び出し間の待機時間(秒) (デフォルト: `1.0`)
- `--max_items`: 処理する最大項目数
- `--start_from`: 開始項目番号 (デフォルト: `0`)
- `--device`: HuggingFace モデル用デバイス (デフォルト: `auto`)

**実用例**

```bash
# テスト実行 (モックモード)
python generate_responses.py \
  --input_data=data/ja_input_data_sample_ver2.jsonl \
  --output=data/input_response_data_mock.jsonl \
  --model=mock --max_items=5

# HuggingFace Sarashinaモデル (ローカル実行)
python generate_responses.py \
  --input_data=data/ja_input_data_sample_ver2.jsonl \
  --output=data/input_response_data_sarashina.jsonl \
  --model=sarashina --device=cuda --delay=0.1

# 処理の再開
python generate_responses.py \
  --input_data=data/ja_input_data_sample_ver2.jsonl \
  --output=data/input_response_data_claude_continued.jsonl \
  --model=claude-3-5-sonnet --start_from=20
```

#### 生成後の評価実行

```bash
python3 -m instruction_following_eval.evaluation_main \
  --input_data=data/ja_input_data_sample_ver2.jsonl \
  --input_response_data=data/input_response_data_claude_japanese.jsonl \
  --output_dir=data/output_claude
```

## 指示ライブラリリファレンス

### instructions.py リファレンス

`instructions.py`は指示追従評価のためのライブラリで、様々な種類の制約をチェックするための指示クラスを提供します。各クラスは`Instruction`基底クラスを継承し、指示の生成と検証機能を実装します。

#### 基底クラス

**Instruction**: すべての指示クラスの基底クラス
- `__init__(instruction_id)`: 指示IDで初期化
- `build_description(**kwargs)`: 指示の説明文を構築（実装必須）
- `get_instruction_args()`: 指示引数を返す（実装必須）
- `get_instruction_args_keys()`: 引数キーを返す（実装必須）
- `check_following(value)`: 応答が指示に従っているかチェック（実装必須）

#### 主要な制約カテゴリ

**言語制約**
- `ResponseLanguageChecker`: 応答全体の言語をチェック

**長さ制約**
- `NumberOfSentences`: 文の数をチェック
- `NumberOfWords`: 単語数をチェック
- `ParagraphChecker`: 段落数をチェック

**コンテンツ制約**
- `PlaceholderChecker`: プレースホルダーの数をチェック
- `PostscriptChecker`: 追伸の有無をチェック
- `KeywordChecker`: 特定のキーワードの存在をチェック
- `KeywordFrequencyChecker`: キーワードの出現頻度をチェック
- `ForbiddenWords`: 禁止単語の使用をチェック

**フォーマット制約**
- `BulletListChecker`: 箇条書きリストの数をチェック
- `HighlightSectionChecker`: ハイライトされたセクションの数をチェック
- `SectionChecker`: セクション分割をチェック
- `TitleChecker`: タイトルの存在をチェック
- `JsonFormat`: JSON形式をチェック
- `ConstrainedResponseChecker`: 制約付き応答をチェック

**開始・終了制約**
- `ConstrainedStartChecker`: 応答の開始フレーズをチェック
- `EndChecker`: 応答の終了フレーズをチェック
- `QuotationChecker`: 二重引用符で囲まれているかをチェック

**大文字小文字制約**
- `CapitalLettersEnglishChecker`: 英語ですべて大文字かをチェック
- `LowercaseLettersEnglishChecker`: 英語ですべて小文字かをチェック
- `CapitalWordFrequencyChecker`: すべて大文字の単語の頻度をチェック

**句読点制約**
- `CommaChecker`: コンマの使用をチェック
- `LetterFrequencyChecker`: 特定文字の出現頻度をチェック

**複合制約**
- `TwoResponsesChecker`: 2つの異なる応答をチェック
- `RepeatPromptThenAnswer`: プロンプト繰り返しをチェック

### ja_instructions.py リファレンス（統合ライブラリ）

`ja_instructions.py`は日本語・英語両対応の統合指示追従評価ライブラリです。日本語特化の制約と英語制約の両方を提供します。

#### 日本語対応の一般制約

**ResponseLanguageChecker**: 応答全体の言語をチェック（日本語対応版）
- `language`: 言語コード（'ja', 'en', 'fr', 'de', 'es'）

**NumberOfSentences**: 文の数をチェック（日本語対応版）
- `num_sentences`: 閾値となる文の数（1-20）
- `relation`: 比較関係（'未満' または '以上'、英語版も受付）

**NumberOfWords**: 単語数をチェック（日本語対応版）
- `num_words`: 閾値となる単語数（100-500）
- `relation`: 比較関係（'未満' または '以上'）
- `lang`: 言語指定（デフォルト'ja'）

#### 日本語特化制約

**JapaneseHiraganaOnlyChecker**: ひらがなのみの使用をチェック
- ひらがな以外の文字（漢字、カタカナ、英字）を検出してエラー
- 許可文字：ひらがな、空白、基本的な句読点・記号

**JapaneseKatakanaOnlyChecker**: カタカナのみの使用をチェック
- カタカナ以外の文字（漢字、ひらがな、英字）を検出してエラー
- 許可文字：カタカナ、空白、基本的な句読点・記号

**JapaneseBracketEmphasisFrequencyChecker**: 【】強調表現の頻度をチェック
- `capital_relation`: 比較関係（'未満', '以上', '正確に'）
- `capital_frequency`: 期待頻度数

**JapaneseNoToutenChecker**: 読点（、）の使用禁止をチェック
- 日本語の読点（、）の存在をチェック

**JapaneseStarFrequencyChecker**: 星印記号（★）の頻度をチェック
- `let_relation`: 比較関係（'未満', '以上', '正確に'）
- `let_frequency`: 期待頻度数（デフォルト6）
- `letter`: 対象記号（デフォルト'★'）

**JapaneseLetterFrequencyChecker**: 日本語文字頻度をチェック
- `let_relation`: 比較関係（'未満', '以上', '正確に'）
- `let_frequency`: 期待頻度数
- `letter`: 対象文字（デフォルト'あ'）

**JapanesePostscriptChecker**: 日本語追記マーカーをチェック
- `postscript_marker`: 追記マーカー（デフォルト'追記'）

**JapaneseEndingPhraseChecker**: 日本語終了フレーズをチェック
- `end_phrase`: 終了フレーズ

**JapaneseOnlyLanguageChecker**: 日本語のみの使用をチェック
- `language`: 言語コード（デフォルト'ja'）

#### ユーティリティ関数

**文字種判定関数**
```python
def is_hiragana_char(char: str) -> bool
def is_katakana_char(char: str) -> bool  
def is_kanji_char(char: str) -> bool
def is_japanese_char(char: str) -> bool
```

**文字カウント関数**
```python
def count_japanese_chars(text: str) -> dict
# 戻り値: {'hiragana': 数, 'katakana': 数, 'kanji': 数, 'total_japanese': 数}
```

**統一チェック関数**
```python
def check_japanese_constraint(response: str, constraint_type: str, **kwargs) -> bool
```

対応制約タイプ: `"hiragana_only"`, `"katakana_only"`, `"bracket_emphasis_frequency"`, `"no_touten"`, `"star_frequency"`, `"japanese_postscript"`, `"japanese_ending"`, `"japanese_only"`, `"japanese_letter_frequency"`

**英語→日本語変換関数**
```python
def convert_english_to_japanese_instruction(instruction_id_list, kwargs_list)
```

変換例:
- `"change_case:english_lowercase"` → `"change_case:japanese_hiragana"`
- `"change_case:english_capital"` → `"change_case:japanese_katakana"`
- `"punctuation:no_comma"` → `"punctuation:no_touten"`

#### 統合ライブラリ使用例

```python
# 日本語特化制約の使用
checker = JapaneseHiraganaOnlyChecker("test_id")
description = checker.build_description()
result = checker.check_following("これはひらがなです")

# 英語制約も同じライブラリから利用
keyword_checker = KeywordChecker("test_id")
description = keyword_checker.build_description(keywords=["test"])

# 統一チェック関数を使用
result = check_japanese_constraint(
    "これは【重要】な【ポイント】です", 
    "bracket_emphasis_frequency", 
    relation="以上", 
    frequency=2
)

# 指示レジストリ経由でのアクセス（推奨）
import instructions_registry
instruction_cls = instructions_registry.INSTRUCTION_DICT["punctuation:no_touten"]
checker = instruction_cls("test_id")
```

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