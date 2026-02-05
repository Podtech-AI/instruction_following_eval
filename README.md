# これは、IFEval: Instruction Following Evalをクローンして修正したリポジトリです。

https://github.com/google-research/google-research/tree/master/instruction_following_eval


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

### 既存の応答データを使用する場合

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

### AIモデルを使用して応答を生成する場合

複数のAIプロバイダーからモデルを選択して応答を生成し、評価を行うことができます。

#### 1. 旧来のGPTフラグを使用する場合（後方互換性）

OpenAI APIを使用してGPTモデルで応答を生成：

```bash
# 環境変数でAPIキーを設定
export OPENAI_API_KEY="your-api-key-here"

# GPT-3.5-turboを使用
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --use_gpt=True \
  --gpt_model=gpt-3.5-turbo \
  --output_dir=instruction_following_eval/data/test_output

# GPT-4を使用
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --use_gpt=True \
  --gpt_model=gpt-4 \
  --output_dir=instruction_following_eval/data/test_output

# コマンドライン引数でAPIキーを指定
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --use_gpt=True \
  --gpt_model=gpt-4-turbo \
  --openai_api_key="your-api-key-here" \
  --output_dir=instruction_following_eval/data/test_output
```

#### 2. 新しい複数プロバイダー対応フラグを使用する場合

##### OpenAI モデルを使用

```bash
# 環境変数でAPIキーを設定
export OPENAI_API_KEY="your-api-key-here"

# GPT-3.5-turboを使用（デフォルト）
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --model_provider=openai \
  --output_dir=instruction_following_eval/data/test_output

# 特定のモデルを指定
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --model_provider=openai \
  --model_name=gpt-4 \
  --output_dir=instruction_following_eval/data/test_output

# コマンドライン引数でAPIキーを指定
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --model_provider=openai \
  --model_name=gpt-4-turbo \
  --api_key="your-api-key-here" \
  --output_dir=instruction_following_eval/data/test_output
```

##### Anthropic モデルを使用

```bash
# 環境変数でAPIキーを設定
export ANTHROPIC_API_KEY="your-api-key-here"

# Claude 3 Sonnetを使用
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --model_provider=anthropic \
  --model_name=claude-3-sonnet-20240229 \
  --output_dir=instruction_following_eval/data/test_output

# コマンドライン引数でAPIキーを指定
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --model_provider=anthropic \
  --model_name=claude-3-opus-20240229 \
  --api_key="your-api-key-here" \
  --output_dir=instruction_following_eval/data/test_output
```

##### Google モデルを使用

```bash
# 環境変数でAPIキーを設定
export GOOGLE_AI_API_KEY="your-api-key-here"

# Gemini Proを使用
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --model_provider=google \
  --model_name=gemini-pro \
  --output_dir=instruction_following_eval/data/test_output

# コマンドライン引数でAPIキーを指定
python3 -m instruction_following_eval.evaluation_main \
  --input_data=instruction_following_eval/data/input_data.jsonl \
  --model_provider=google \
  --model_name=gemini-pro-vision \
  --api_key="your-api-key-here" \
  --output_dir=instruction_following_eval/data/test_output
```

#### 利用可能なモデル

**OpenAI:**
- `gpt-3.5-turbo` (デフォルト)
- `gpt-4`
- `gpt-4-turbo`
- その他OpenAI APIで利用可能なモデル

**Anthropic:**
- `claude-3-sonnet-20240229`
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`
- その他Anthropic APIで利用可能なモデル

**Google:**
- `gemini-pro`
- `gemini-pro-vision`
- その他Google AI APIで利用可能なモデル


```

以下のデータはサンプルデータから削除

// {"key": 2785, "prompt": "What is inside Shinto shrines? Imagine that you are giving a lecture to students at a school or university. Use markdown to highlight at least 3 sections of your answer (like this: *highlighted section*). Your answer must also contain at least 3 placeholders (an example of a placeholder is [address]).", "instruction_id_list": ["detectable_format:number_highlighted_sections", "detectable_content:number_placeholders"], "kwargs": [{"num_highlights": 3}, {"num_placeholders": 3}]}
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
