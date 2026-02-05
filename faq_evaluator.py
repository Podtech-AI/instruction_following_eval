# faq_evaluator.py
import os
import json
import argparse
from pathlib import Path

# 既存のロジックを想定：evaluate_with_assistant(...) 等があるなら流用
# なければ下の run_eval_with_openai / run_eval_locally を使う

def run_eval_with_openai(model: str, input_path: str, output_dir: str, api_key: str | None = None):
    """
    input_path の jsonl（例: {"id": "...", "prompt": "..."}）を読み、
    OpenAI Chat Completions(API)で推論して output_dir に結果を書き出す最小例。
    必要に応じて Assistants API や Vector Store 呼び出しに置き換えてOK。
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
    if not client.api_key:
        raise RuntimeError("OPENAI_API_KEY が見つかりません。環境変数か --openai_api_key で指定してください。")

    out = []
    with open(input_path, "r") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            prompt = ex.get("prompt") or ex.get("instruction") or ""
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            out.append({
                "id": ex.get("id"),
                "prompt": prompt,
                "response": resp.choices[0].message.content,
            })

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(output_dir, "openai_results.jsonl"), "w") as w:
        for r in out:
            w.write(json.dumps(r, ensure_ascii=False) + "\n")

def run_eval_locally(input_path: str, output_dir: str):
    """
    ローカル/別モデルの評価処理をここに実装。
    何もなければダミーで例外にしておく。
    """
    raise NotImplementedError("ローカル評価処理を実装してください。")

def main():
    parser = argparse.ArgumentParser(description="FAQ evaluator with optional OpenAI GPT.")
    parser.add_argument("--input_data", required=True, help="Path to input .jsonl")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    # 追加: use_gpt と gpt_model / openai_api_key
    parser.add_argument("--use_gpt", action="store_true", help="Use OpenAI GPT via API if set.")
    parser.add_argument("--gpt_model", default="gpt-4o-mini", help="OpenAI model name")
    parser.add_argument("--openai_api_key", default=None, help="Override OPENAI_API_KEY")

    args = parser.parse_args()

    if args.use_gpt:
        run_eval_with_openai(
            model=args.gpt_model,
            input_path=args.input_data,
            output_dir=args.output_dir,
            api_key=args.openai_api_key,
        )
    else:
        run_eval_locally(
            input_path=args.input_data,
            output_dir=args.output_dir,
        )

if __name__ == "__main__":
    main()
