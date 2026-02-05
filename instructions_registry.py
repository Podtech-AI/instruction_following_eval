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

"""すべての指示のレジストリ。"""
import instructions

_KEYWORD = "keywords:"

_LANGUAGE = "language:"

_LENGTH = "length_constraints:"

_CONTENT = "detectable_content:"

_FORMAT = "detectable_format:"

_MULTITURN = "multi-turn:"

_COMBINATION = "combination:"

_STARTEND = "startend:"

_CHANGE_CASES = "change_case:"

_PUNCTUATION = "punctuation:"

# 日本語適応版：10~20個の指示に絞り込み
INSTRUCTION_DICT = {
    # キーワード関連（3つ）
    _KEYWORD + "existence": instructions.KeywordChecker,
    _KEYWORD + "frequency": instructions.KeywordFrequencyChecker,
    _KEYWORD + "forbidden_words": instructions.ForbiddenWords,
    
    # 長さ制約（4つ）
    _LENGTH + "number_sentences": instructions.NumberOfSentences,
    _LENGTH + "number_paragraphs": instructions.ParagraphChecker,
    _LENGTH + "number_words": instructions.NumberOfWords,
    _LENGTH + "nth_paragraph_first_word": instructions.ParagraphFirstWordCheck,
    
    # 内容（2つ）
    _CONTENT + "number_placeholders": instructions.PlaceholderChecker,
    _CONTENT + "postscript": instructions.PostscriptChecker,
    
    # フォーマット（5つ）
    _FORMAT + "number_bullet_lists": instructions.BulletListChecker,
    _FORMAT + "number_highlighted_sections": instructions.HighlightSectionChecker,
    _FORMAT + "multiple_sections": instructions.SectionChecker,
    _FORMAT + "json_format": instructions.JsonFormat,
    _FORMAT + "title": instructions.TitleChecker,
    
    # 開始・終了（2つ）
    _STARTEND + "end_checker": instructions.EndChecker,
    _STARTEND + "quotation": instructions.QuotationChecker,
    
    # 日本語特有（3つ）
    _CHANGE_CASES + "japanese_hiragana": instructions.JapaneseHiraganaChecker,
    _CHANGE_CASES + "japanese_casual": instructions.JapaneseCasualChecker,
    _CHANGE_CASES + "katakana_word_frequency": instructions.KatakanaWordFrequencyChecker,
    
    # 句読点
    _PUNCTUATION + "no_comma": instructions.CommaChecker,
    
    # 言語
    "language:response_language": instructions.ResponseLanguageChecker,
}

# 日本語適応版の競合関係
INSTRUCTION_CONFLICTS = {
    # キーワード関連
    _KEYWORD + "existence": {_KEYWORD + "existence"},
    _KEYWORD + "frequency": {_KEYWORD + "frequency"},
    _KEYWORD + "forbidden_words": {_KEYWORD + "forbidden_words"},
    
    # 長さ制約
    _LENGTH + "number_sentences": {_LENGTH + "number_sentences"},
    _LENGTH + "number_paragraphs": {
        _LENGTH + "number_paragraphs",
        _LENGTH + "nth_paragraph_first_word",
    },
    _LENGTH + "number_words": {_LENGTH + "number_words"},
    _LENGTH + "nth_paragraph_first_word": {
        _LENGTH + "nth_paragraph_first_word",
        _LENGTH + "number_paragraphs",
    },
    
    # 内容
    _CONTENT + "number_placeholders": {_CONTENT + "number_placeholders"},
    _CONTENT + "postscript": {_CONTENT + "postscript"},
    
    # フォーマット
    _FORMAT + "number_bullet_lists": {_FORMAT + "number_bullet_lists"},
    _FORMAT + "number_highlighted_sections": {_FORMAT + "number_highlighted_sections"},
    _FORMAT + "multiple_sections": {
        _FORMAT + "multiple_sections",
        _FORMAT + "number_highlighted_sections",
    },
    _FORMAT + "json_format": set(INSTRUCTION_DICT.keys()).difference(
        {_KEYWORD + "forbidden_words", _KEYWORD + "existence"}
    ),
    _FORMAT + "title": {_FORMAT + "title"},
    
    # 開始・終了
    _STARTEND + "end_checker": {_STARTEND + "end_checker"},
    _STARTEND + "quotation": {_STARTEND + "quotation", _FORMAT + "title"},
    
    # 日本語特有
    _CHANGE_CASES + "japanese_hiragana": {
        _CHANGE_CASES + "japanese_hiragana",
        _CHANGE_CASES + "japanese_casual",
        _CHANGE_CASES + "katakana_word_frequency",
    },
    _CHANGE_CASES + "japanese_casual": {
        _CHANGE_CASES + "japanese_casual",
        _CHANGE_CASES + "japanese_hiragana",
    },
    _CHANGE_CASES + "katakana_word_frequency": {
        _CHANGE_CASES + "katakana_word_frequency",
        _CHANGE_CASES + "japanese_hiragana",
    },
    
    # 句読点
    _PUNCTUATION + "no_comma": {_PUNCTUATION + "no_comma"},
    
    # 言語
    "language:response_language": {"language:response_language"},
}


def conflict_make(conflicts):
  """AがBと競合する場合、BもAと競合することを保証します。

  Args:
    conflicts: キーが指示idで、値が競合する指示idのセットである
      潜在的な競合の辞書。

  Returns:
    辞書の改訂版。すべての指示は自分自身と競合します。
    AがBと競合する場合、BもAと競合します。
  """
  for key in conflicts:
    for k in conflicts[key]:
      conflicts[k].add(key)
    conflicts[key].add(key)
  return conflicts
