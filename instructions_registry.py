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
import ja_instructions as instructions

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

INSTRUCTION_DICT = {
    _KEYWORD + "existence": instructions.KeywordChecker,
    _KEYWORD + "frequency": instructions.KeywordFrequencyChecker,
    # TODO(jeffreyzhou): 選択するための適切な文のセットを作成する
    # _KEYWORD + "key_sentences": instructions.KeySentenceChecker,
    _KEYWORD + "forbidden_words": instructions.ForbiddenWords,
    _KEYWORD + "letter_frequency": instructions.LetterFrequencyChecker,
    _LANGUAGE + "response_language": instructions.ResponseLanguageChecker,
    _LENGTH + "number_sentences": instructions.NumberOfSentences,
    _LENGTH + "number_paragraphs": instructions.ParagraphChecker,
    _LENGTH + "number_words": instructions.NumberOfWords,
    _LENGTH + "nth_paragraph_first_word": instructions.ParagraphFirstWordCheck,
    _CONTENT + "number_placeholders": instructions.PlaceholderChecker,
    _CONTENT + "postscript": instructions.PostscriptChecker,
    _FORMAT + "number_bullet_lists": instructions.BulletListChecker,
    # TODO(jeffreyzhou): 段落を事前作成するか、プロンプトを使用して置き換える
    # _CONTENT + "rephrase_paragraph": instructions.RephraseParagraph,
    _FORMAT + "constrained_response": instructions.ConstrainedResponseChecker,
    _FORMAT + "number_highlighted_sections": (
        instructions.HighlightSectionChecker),
    _FORMAT + "multiple_sections": instructions.SectionChecker,
    # TODO(tianjianlu): メッセージの前処理で言い換えを再有効化する。
    # _FORMAT + "rephrase": instructions.RephraseChecker,
    _FORMAT + "json_format": instructions.JsonFormat,
    _FORMAT + "title": instructions.TitleChecker,
    # TODO(tianjianlu): 特定のプロンプトで再有効化する。
    # _MULTITURN + "constrained_start": instructions.ConstrainedStartChecker,
    _COMBINATION + "two_responses": instructions.TwoResponsesChecker,
    _COMBINATION + "repeat_prompt": instructions.RepeatPromptThenAnswer,
    _STARTEND + "end_checker": instructions.EndChecker,
    _CHANGE_CASES
    + "capital_word_frequency": instructions.CapitalWordFrequencyChecker,
    _CHANGE_CASES
    + "english_capital": instructions.CapitalLettersEnglishChecker,
    _CHANGE_CASES
    + "english_lowercase": instructions.LowercaseLettersEnglishChecker,
    _PUNCTUATION + "no_comma": instructions.CommaChecker,
    _STARTEND + "quotation": instructions.QuotationChecker,
    # 日本語特化指示
    _PUNCTUATION + "no_touten": instructions.JapaneseNoToutenChecker,
    _CHANGE_CASES + "japanese_hiragana": instructions.JapaneseHiraganaOnlyChecker,
    _CHANGE_CASES + "japanese_katakana": instructions.JapaneseKatakanaOnlyChecker,
    _CHANGE_CASES + "japanese_bracket_emphasis": instructions.JapaneseBracketEmphasisFrequencyChecker,
    _KEYWORD + "japanese_star_frequency": instructions.JapaneseStarFrequencyChecker,
    _KEYWORD + "japanese_letter_frequency": instructions.JapaneseLetterFrequencyChecker,
    _CONTENT + "japanese_postscript": instructions.JapanesePostscriptChecker,
    _STARTEND + "japanese_end_checker": instructions.JapaneseEndingPhraseChecker,
    _LANGUAGE + "japanese_only": instructions.JapaneseOnlyLanguageChecker,
}

INSTRUCTION_CONFLICTS = {
    _KEYWORD + "existence": {_KEYWORD + "existence"},
    _KEYWORD + "frequency": {_KEYWORD + "frequency"},
    # TODO(jeffreyzhou): 選択するための適切な文のセットを作成する
    # _KEYWORD + "key_sentences": instructions.KeySentenceChecker,
    _KEYWORD + "forbidden_words": {_KEYWORD + "forbidden_words"},
    _KEYWORD + "letter_frequency": {_KEYWORD + "letter_frequency"},
    _LANGUAGE
    + "response_language": {
        _LANGUAGE + "response_language",
        _FORMAT + "multiple_sections",
        _KEYWORD + "existence",
        _KEYWORD + "frequency",
        _KEYWORD + "forbidden_words",
        _STARTEND + "end_checker",
        _CHANGE_CASES + "english_capital",
        _CHANGE_CASES + "english_lowercase",
    },
    _LENGTH + "number_sentences": {_LENGTH + "number_sentences"},
    _LENGTH + "number_paragraphs": {
        _LENGTH + "number_paragraphs",
        _LENGTH + "nth_paragraph_first_word",
        _LENGTH + "number_sentences",
        _LENGTH + "nth_paragraph_first_word",
    },
    _LENGTH + "number_words": {_LENGTH + "number_words"},
    _LENGTH + "nth_paragraph_first_word": {
        _LENGTH + "nth_paragraph_first_word",
        _LENGTH + "number_paragraphs",
    },
    _CONTENT + "number_placeholders": {_CONTENT + "number_placeholders"},
    _CONTENT + "postscript": {_CONTENT + "postscript"},
    _FORMAT + "number_bullet_lists": {_FORMAT + "number_bullet_lists"},
    # TODO(jeffreyzhou): 段落を事前作成するか、プロンプトを使用して置き換える
    # _CONTENT + "rephrase_paragraph": instructions.RephraseParagraph,
    _FORMAT + "constrained_response": set(INSTRUCTION_DICT.keys()),
    _FORMAT
    + "number_highlighted_sections": {_FORMAT + "number_highlighted_sections"},
    _FORMAT
    + "multiple_sections": {
        _FORMAT + "multiple_sections",
        _LANGUAGE + "response_language",
        _FORMAT + "number_highlighted_sections",
    },
    # TODO(tianjianlu): メッセージの前処理で言い換えを再有効化する。
    # _FORMAT + "rephrase": instructions.RephraseChecker,
    _FORMAT
    + "json_format": set(INSTRUCTION_DICT.keys()).difference(
        {_KEYWORD + "forbidden_words", _KEYWORD + "existence"}
    ),
    _FORMAT + "title": {_FORMAT + "title"},
    # TODO(tianjianlu): 特定のプロンプトで再有効化する。
    # _MULTITURN + "constrained_start": instructions.ConstrainedStartChecker,
    _COMBINATION
    + "two_responses": set(INSTRUCTION_DICT.keys()).difference({
        _KEYWORD + "forbidden_words",
        _KEYWORD + "existence",
        _LANGUAGE + "response_language",
        _FORMAT + "title",
        _PUNCTUATION + "no_comma"
    }),
    _COMBINATION + "repeat_prompt": set(INSTRUCTION_DICT.keys()).difference({
        _KEYWORD + "existence",
        _FORMAT + "title",
        _PUNCTUATION + "no_comma"
    }),
    _STARTEND + "end_checker": {_STARTEND + "end_checker"},
    _CHANGE_CASES + "capital_word_frequency": {
        _CHANGE_CASES + "capital_word_frequency",
        _CHANGE_CASES + "english_lowercase",
        _CHANGE_CASES + "english_capital",
    },
    _CHANGE_CASES + "english_capital": {_CHANGE_CASES + "english_capital"},
    _CHANGE_CASES + "english_lowercase": {
        _CHANGE_CASES + "english_lowercase",
        _CHANGE_CASES + "english_capital",
    },
    _PUNCTUATION + "no_comma": {_PUNCTUATION + "no_comma"},
    _STARTEND + "quotation": {_STARTEND + "quotation", _FORMAT + "title"},
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
