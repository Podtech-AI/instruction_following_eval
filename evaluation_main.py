# coding=utf-8
# Copyright 2025 The Google Research Authors.
#
# Apache License, Version 2.0（「ライセンス」）に基づいてライセンスされています。
# このファイルは、ライセンスに準拠していない限り使用できません。
# ライセンスのコピーは以下で入手できます：
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# 適用法で要求されるか、書面で合意されない限り、ライセンスに基づいて
# 配布されるソフトウェアは「現状のまま」で配布され、
# 明示的または黙示的を問わず、いかなる保証も条件もありません。
# 詳細については、ライセンスを参照してください。

"""指示追従評価のバイナリ。README.mdを参照してください。"""

import os
from typing import Sequence

from absl import app
from absl import flags
from absl import logging

from instruction_following_eval import evaluation_lib

import nltk
nltk.download('punkt_tab')

_INPUT_DATA = flags.DEFINE_string(
    "input_data", None, "入力データへのパス", required=True
)

_INPUT_RESPONSE_DATA = flags.DEFINE_string(
    "input_response_data", None, "入力応答データへのパス", required=False
)

_OUTPUT_DIR = flags.DEFINE_string(
    "output_dir",
    None,
    "推論と評価結果の出力ディレクトリ。",
    required=True,
)


def main(argv):
  if len(argv) > 1:
    raise app.UsageError("コマンドライン引数が多すぎます。")

  inputs = evaluation_lib.read_prompt_list(_INPUT_DATA.value)
  prompt_to_response = evaluation_lib.read_prompt_to_response_dict(
      _INPUT_RESPONSE_DATA.value)

  # 指示追従の結果を取得
  for func, output_file_name in [
      (evaluation_lib.test_instruction_following_strict, "eval_results_strict"),
      (evaluation_lib.test_instruction_following_loose, "eval_results_loose"),
  ]:
    logging.info("%s を生成中...", output_file_name)
    outputs = []
    for inp in inputs:
      outputs.append(func(inp, prompt_to_response))
    follow_all_instructions = [o.follow_all_instructions for o in outputs]
    accuracy = sum(follow_all_instructions) / len(outputs)
    logging.info("精度: %f", accuracy)

    output_file_name = os.path.join(
        _OUTPUT_DIR.value, output_file_name + ".jsonl"
    )
    evaluation_lib.write_outputs(output_file_name, outputs)
    logging.info("生成完了: %s", output_file_name)

    # 指示追従精度レポートを出力します。
    print("=" * 64)
    print(f"{output_file_name} 精度スコア:")
    evaluation_lib.print_report(outputs)


if __name__ == "__main__":
  app.run(main)
