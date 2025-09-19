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

"""統合指示ライブラリ（日本語対応 + 英語版）"""
import collections
import json
import random
import re
import string
from typing import Dict, Optional, Sequence, Union

from absl import logging
import langdetect

import jp_instructions_util as instructions_util

_InstructionArgsDtype = Optional[Dict[str, Union[int, str, Sequence[str]]]]

_LANGUAGES = instructions_util.LANGUAGE_CODES if hasattr(instructions_util, 'LANGUAGE_CODES') else {
    "ja": "Japanese", "en": "English", "fr": "French", "de": "German", "es": "Spanish"
}

# 比較のための関係演算（日本語対応）
_COMPARISON_RELATION = ("未満", "以上")
_COMPARISON_RELATION_EN = ("less than", "at least")

# 英語版定数（instructions.pyより）
_COMPARISON_RELATION_ORIGINAL = ("less than", "at least")
_COMPARISON_RELATION_JA = ("未満", "以上")

# 文の最大数
_MAX_NUM_SENTENCES = 20

# プレースホルダーの数
_NUM_PLACEHOLDERS = 4

# 箇条書きリストの数
_NUM_BULLETS = 5

# 制約付き応答のオプション（日本語）
_CONSTRAINED_RESPONSE_OPTIONS = (
    "私の答えははいです。", "私の答えはいいえです。", "私の答えはたぶんです。")

# 制約付き応答のオプション（英語）
_CONSTRAINED_RESPONSE_OPTIONS_EN = (
    "My answer is yes.", "My answer is no.", "My answer is maybe.")

# 開始キーワードのオプション（日本語）
_STARTER_OPTIONS = ("私が言うなら", "私の答えは", "私は信じます",
                    "私の意見では", "私は思います", "私は考えています", "私は感じます",
                    "私の観点から", "私が見る限り", "私によれば",
                    "私が関心を持つ限り", "私の理解では",
                    "私の見解では", "私の見解は", "私の認識では")

# 終了キーワードのオプション（日本語）
_ENDING_OPTIONS = ("他に質問はありますか？",
                   "他にお手伝いできることはありますか？")

# 開始キーワードのオプション（英語）
_STARTER_OPTIONS_EN = ("I would say", "My answer is", "I believe",
                       "In my opinion", "I think", "I reckon", "I feel",
                       "From my perspective", "As I see it", "According to me",
                       "As far as I'm concerned", "To my understanding",
                       "In my view", "My take on it is", "As per my perception")

# 終了キーワードのオプション（英語）
_ENDING_OPTIONS_EN = ("Any other questions?",
                      "Is there anything else I can help with?")

# ハイライトされたセクションの数
_NUM_HIGHLIGHTED_SECTIONS = 4

# セクション分割子（日本語）
_SECTION_SPLITER = ("セクション", "節")

# セクションの数
_NUM_SECTIONS = 5

# 段落の数
_NUM_PARAGRAPHS = 5

# 追記マーカー（日本語）
_POSTSCRIPT_MARKER = ("追伸", "P.S.")

# 追記マーカー（英語）
_POSTSCRIPT_MARKER_EN = ("P.S.", "P.P.S")

# キーワードの数
_NUM_KEYWORDS = 2

# 単一キーワードの出現回数
_KEYWORD_FREQUENCY = 3

# 単一文字の出現回数
_LETTER_FREQUENCY = 10

# すべて大文字の単語の出現回数
_ALL_CAPITAL_WORD_FREQUENCY = 20

# 応答内の単語数
_NUM_WORDS_LOWER_LIMIT = 100
_NUM_WORDS_UPPER_LIMIT = 500


class Instruction:
  """指示テンプレート"""

  def __init__(self, instruction_id):
    self.id = instruction_id

  def build_description(self, **kwargs):
    raise NotImplementedError("`build_description`は実装されていません")

  def get_instruction_args(self):
    raise NotImplementedError("`get_instruction_args`は実装されていません")

  def get_instruction_args_keys(self):
    raise NotImplementedError("`get_instruction_args_keys`は実装されていません")

  def check_following(self, value):
    raise NotImplementedError("`check_following`は実装されていません")


class ResponseLanguageChecker(Instruction):
  """応答全体の言語をチェックします"""

  def build_description(self, *, language = None):
    """指示の説明を構築します
    
    Args:
      language: 応答の期待される言語を表す文字列
      
    Returns:
      指示の説明を表す文字列
    """
    self._language = language
    if self._language is None:
      self._language = random.choice(list(_LANGUAGES.keys()))

    if self._language == 'ja':
      self._description_pattern = (
          "あなたの全ての回答は日本語で行ってください。他の言語は使用しないでください。")
    else:
      self._description_pattern = (
          "あなたの全ての回答は{language}語で行ってください。他の言語は使用しないでください。")
      
    if self._language == 'ja':
      return self._description_pattern
    else:
      return self._description_pattern.format(language=_LANGUAGES.get(self._language, self._language))

  def get_instruction_args(self):
    """build_descriptionのキーワード引数を返します"""
    return {"language": self._language}

  def get_instruction_args_keys(self):
    """build_descriptionの引数キーを返します"""
    return ["language"]

  def check_following(self, value):
    """応答全体の言語が指示に従っているかをチェックします"""
    assert isinstance(value, str)

    # 簡易的な言語検出を使用
    detected_lang = instructions_util._detect_language(value)
    return detected_lang == self._language


class NumberOfSentences(Instruction):
  """文の数をチェックします"""

  def build_description(self, *, num_sentences = None, relation = None):
    """指示の説明を構築します"""
    self._num_sentences_threshold = num_sentences
    if (self._num_sentences_threshold is None or
        self._num_sentences_threshold < 0):
      self._num_sentences_threshold = random.randint(1, _MAX_NUM_SENTENCES)

    if relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif relation not in _COMPARISON_RELATION + _COMPARISON_RELATION_EN:
      raise ValueError(f"サポートされている関係は {_COMPARISON_RELATION} または {_COMPARISON_RELATION_EN} ですが、{relation} が指定されました")
    else:
      self._comparison_relation = relation

    # 日本語の関係演算子を使用
    if self._comparison_relation in _COMPARISON_RELATION_EN:
      relation_map = {"less than": "未満", "at least": "以上"}
      self._comparison_relation = relation_map.get(self._comparison_relation, self._comparison_relation)

    self._description_pattern = (
        "あなたの回答は{relation}{num_sentences}文を含む必要があります。")
    return self._description_pattern.format(
        relation=self._comparison_relation,
        num_sentences=self._num_sentences_threshold)

  def get_instruction_args(self):
    return {"num_sentences": self._num_sentences_threshold,
            "relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    return ["num_sentences", "relation"]

  def check_following(self, value):
    """文の数が指示に従っているかをチェックします"""
    num_sentences = instructions_util.count_sentences(value)
    if self._comparison_relation in ["未満", "less than"]:
      return num_sentences < self._num_sentences_threshold
    elif self._comparison_relation in ["以上", "at least"]:
      return num_sentences >= self._num_sentences_threshold


class PlaceholderChecker(Instruction):
  """テンプレート作成におけるプレースホルダーをチェックします"""

  def build_description(self, *, num_placeholders = None):
    """指示の説明を構築します"""
    self._num_placeholders = num_placeholders
    if self._num_placeholders is None or self._num_placeholders < 0:
      self._num_placeholders = random.randint(1, _NUM_PLACEHOLDERS)
    self._description_pattern = (
        "回答には[住所]のような角括弧で表現されたプレースホルダーを最低{num_placeholders}個含む必要があります。")
    return self._description_pattern.format(
        num_placeholders=self._num_placeholders)

  def get_instruction_args(self):
    return {"num_placeholders": self._num_placeholders}

  def get_instruction_args_keys(self):
    return ["num_placeholders"]

  def check_following(self, value):
    """プレースホルダーの数が指示に従っているかをチェックします"""
    placeholders = re.findall(r"\[.*?\]", value)
    num_placeholders = len(placeholders)
    return num_placeholders >= self._num_placeholders


class BulletListChecker(Instruction):
  """プロンプト内の箇条書きリストをチェックします"""

  def build_description(self, *, num_bullets = None):
    """指示の説明を構築します"""
    self._num_bullets = num_bullets
    if self._num_bullets is None or self._num_bullets < 0:
      self._num_bullets = random.randint(1, _NUM_BULLETS)
    self._description_pattern = (
        "あなたの回答は正確に{num_bullets}個の箇条書きポイントを含む必要があります。" +
        "マークダウンの箇条書きを次のように使用してください：\n" +
        "* これはポイント1です。\n" +
        "* これはポイント2です。")
    return self._description_pattern.format(
        num_bullets=self._num_bullets)

  def get_instruction_args(self):
    return {"num_bullets": self._num_bullets}

  def get_instruction_args_keys(self):
    return ["num_bullets"]

  def check_following(self, value):
    """箇条書きリストの数が要件を満たしているかをチェックします"""
    bullet_lists = re.findall(r"^\s*\*[^\*].*$", value, flags=re.MULTILINE)
    bullet_lists_2 = re.findall(r"^\s*-.*$", value, flags=re.MULTILINE)
    num_bullet_lists = len(bullet_lists) + len(bullet_lists_2)
    return num_bullet_lists == self._num_bullets


class ConstrainedResponseChecker(Instruction):
  """制約付き応答をチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._constrained_responses = _CONSTRAINED_RESPONSE_OPTIONS
    self._description_pattern = (
        "次のオプションのいずれかで答えてください：{response_options}")
    return self._description_pattern.format(
        response_options=self._constrained_responses)

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答が制約されたオプションと一致するかをチェックします"""
    value = value.strip()
    for constrained_response in self._constrained_responses:
      if constrained_response in value:
        return True
    return False


class ConstrainedStartChecker(Instruction):
  """応答の開始をチェックします"""

  def build_description(self, *, starter = None):
    """指示の説明を構築します"""
    self._starter = starter.strip() if isinstance(starter, str) else starter
    if self._starter is None:
      self._starter = random.choice(_STARTER_OPTIONS)
    self._description_pattern = (
        "会話中にあなたの番になったら、常に「{starter}」で始めてください。")
    return self._description_pattern.format(starter=self._starter)

  def get_instruction_args(self):
    return {"starter": self._starter}

  def get_instruction_args_keys(self):
    return ["starter"]

  def check_following(self, value):
    """応答が制約されたキーワードまたはフレーズで始まるかをチェックします"""
    response_pattern = r"^\s*" + re.escape(self._starter) + r".*$"
    response_with_constrained_start = re.search(response_pattern, value,
                                                flags=re.MULTILINE)
    return True if response_with_constrained_start else False


class KeywordChecker(Instruction):
  """特定のキーワードの存在をチェックします"""

  def build_description(self, *, keywords = None, lang = None):
    """指示の説明を構築します"""
    self._lang = lang or 'ja'  # デフォルトは日本語
    
    if not keywords:
      self._keywords = instructions_util.generate_keywords(
          num_keywords=_NUM_KEYWORDS, lang=self._lang)
    else:
      self._keywords = keywords
    self._keywords = sorted(self._keywords)

    self._description_pattern = ("回答に次のキーワード{keywords}を含めてください。")
    return self._description_pattern.format(keywords=self._keywords)

  def get_instruction_args(self):
    return {"keywords": self._keywords, "lang": self._lang}

  def get_instruction_args_keys(self):
    return ["keywords", "lang"]

  def check_following(self, value):
    """応答に期待されるキーワードが含まれているかをチェックします"""
    for keyword in self._keywords:
      if not re.search(re.escape(keyword), value, flags=re.IGNORECASE):
        return False
    return True


class NumberOfWords(Instruction):
  """単語数をチェックします"""

  def build_description(self, *, num_words = None, relation = None, lang = None):
    """指示の説明を構築します"""
    self._lang = lang or 'ja'  # デフォルトは日本語
    self._num_words = num_words
    if self._num_words is None or self._num_words < 0:
      self._num_words = random.randint(
          _NUM_WORDS_LOWER_LIMIT, _NUM_WORDS_UPPER_LIMIT
      )

    if relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif relation not in _COMPARISON_RELATION + _COMPARISON_RELATION_EN:
      raise ValueError(f"サポートされている関係は {_COMPARISON_RELATION} または {_COMPARISON_RELATION_EN} ですが、{relation} が指定されました")
    else:
      self._comparison_relation = relation

    # 日本語の関係演算子を使用
    if self._comparison_relation in _COMPARISON_RELATION_EN:
      relation_map = {"less than": "未満", "at least": "以上"}
      self._comparison_relation = relation_map.get(self._comparison_relation, self._comparison_relation)

    if self._lang == 'ja':
      self._description_pattern = ("{relation}{num_words}単語で回答してください。")
      unit = "単語"
    else:
      self._description_pattern = ("{relation}{num_words}単語で回答してください。")
      unit = "単語"

    return self._description_pattern.format(
        relation=self._comparison_relation,
        num_words=self._num_words)

  def get_instruction_args(self):
    return {"num_words": self._num_words,
            "relation": self._comparison_relation,
            "lang": self._lang}

  def get_instruction_args_keys(self):
    return ["num_words", "relation", "lang"]

  def check_following(self, value):
    """応答に期待される単語数が含まれているかをチェックします"""
    num_words = instructions_util.count_words(value, lang=self._lang)

    if self._comparison_relation in ["未満", "less than"]:
      return num_words < self._num_words
    elif self._comparison_relation in ["以上", "at least"]:
      return num_words >= self._num_words


class JsonFormat(Instruction):
  """JSON形式をチェックします"""

  def build_description(self):
    self._description_pattern = (
        "出力全体をJSON形式で包んでください。```のようなマークダウンティックを使用できます。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    value = (
        value.strip()
        .removeprefix("```json")
        .removeprefix("```Json")
        .removeprefix("```JSON")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
      json.loads(value)
    except ValueError as _:
      return False
    return True


class TitleChecker(Instruction):
  """応答にタイトルがあるかをチェックします"""

  def build_description(self):
    self._description_pattern = (
        "あなたの回答は<<喜びの詩>>のような二重山括弧で囲まれたタイトルを含む必要があります。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答にタイトルが含まれているかをチェックします"""
    pattern = r"<<[^\n]+>>"
    re_pattern = re.compile(pattern)
    titles = re.findall(re_pattern, value)

    for title in titles:
      if title.lstrip("<").rstrip(">").strip():
        return True
    return False


class EndChecker(Instruction):
  """プロンプトが指定されたフレーズで終わるかをチェックします"""

  def build_description(self, *, end_phrase = None):
    """指示の説明を構築します"""
    self._end_phrase = (
        end_phrase.strip() if isinstance(end_phrase, str) else end_phrase
    )
    if self._end_phrase is None:
      self._end_phrase = random.choice(_ENDING_OPTIONS)
    self._description_pattern = (
        "この正確なフレーズ「{ender}」で回答を終えてください。" +
        "このフレーズの後に他の単語は続けないでください。")
    return self._description_pattern.format(ender=self._end_phrase)

  def get_instruction_args(self):
    return {"end_phrase": self._end_phrase}

  def get_instruction_args_keys(self):
    return ["end_phrase"]

  def check_following(self, value):
    """応答が期待されるフレーズで終わるかをチェックします"""
    value = value.strip().strip("\"").lower()
    self._end_phrase = self._end_phrase.strip().lower()
    return value.endswith(self._end_phrase)


class QuotationChecker(Instruction):
  """応答が二重引用符で囲まれているかをチェックします"""

  def build_description(self):
    self._description_pattern = (
        "あなたの回答全体を二重引用符で囲んでください。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答が二重引用符で囲まれているかをチェックします"""
    value = value.strip()
    return len(value) > 1 and value[0] == '"' and value[-1] == '"'


class PostscriptChecker(Instruction):
  """追伸をチェックします"""

  def build_description(self, *, postscript_marker = None):
    """指示の説明を構築します"""
    self._postscript_marker = postscript_marker.strip() if isinstance(
        postscript_marker, str) else postscript_marker
    if self._postscript_marker is None:
      self._postscript_marker = random.choice(_POSTSCRIPT_MARKER)

    self._description_pattern = (
        "回答の最後に、{postscript}で始まる追伸を明示的に追加してください。")
    return self._description_pattern.format(postscript=self._postscript_marker)

  def get_instruction_args(self):
    return {"postscript_marker": self._postscript_marker}

  def get_instruction_args_keys(self):
    return ["postscript_marker"]

  def check_following(self, value):
    """応答が追伸の形式に従っているかをチェックします"""
    value_lower = value.lower()
    if self._postscript_marker == "追伸":
      postscript_pattern = r"追伸.*$"
    elif self._postscript_marker == "P.S.":
      postscript_pattern = r"\s*p\.\s?s\..*$"
    else:
      postscript_pattern = r"\s*" + re.escape(self._postscript_marker.lower()) + r".*$"
    postscript = re.findall(postscript_pattern, value_lower, flags=re.MULTILINE)
    return True if postscript else False


class HighlightSectionChecker(Instruction):
  """ハイライトされたセクションをチェックします"""

  def build_description(self, *, num_highlights = None):
    """指示の説明を構築します"""
    self._num_highlights = num_highlights
    if self._num_highlights is None or self._num_highlights < 0:
      self._num_highlights = random.randint(1, _NUM_HIGHLIGHTED_SECTIONS)

    self._description_pattern = (
        "回答に最低{num_highlights}個のセクションをマークダウンでハイライトしてください。" +
        "例：*ハイライトされたセクション*")

    return self._description_pattern.format(num_highlights=self._num_highlights)

  def get_instruction_args(self):
    return {"num_highlights": self._num_highlights}

  def get_instruction_args_keys(self):
    return ["num_highlights"]

  def check_following(self, value):
    """ハイライトされたセクションの数が要件を満たしているかをチェックします"""
    num_highlights = 0
    highlights = re.findall(r"\*[^\n\*]*\*", value)
    double_highlights = re.findall(r"\*\*[^\n\*]*\*\*", value)
    for highlight in highlights:
      if highlight.strip("*").strip():
        num_highlights += 1
    for highlight in double_highlights:
      if highlight.removeprefix("**").removesuffix("**").strip():
        num_highlights += 1

    return num_highlights >= self._num_highlights


class SectionChecker(Instruction):
  """セクションをチェックします"""

  def build_description(self, *, section_spliter = None, num_sections = None):
    """指示の説明を構築します"""
    self._section_spliter = section_spliter.strip() if isinstance(
        section_spliter, str) else section_spliter
    if self._section_spliter is None:
      self._section_spliter = random.choice(_SECTION_SPLITER)

    self._num_sections = num_sections
    if self._num_sections is None or self._num_sections < 0:
      self._num_sections = random.randint(1, _NUM_SECTIONS)

    self._description_pattern = (
        "回答は{num_sections}個のセクションを含む必要があります。" +
        "各セクションの始まりを{section_spliter} X でマークしてください。例：\n" +
        "{section_spliter} 1\n" +
        "[セクション1の内容]\n" +
        "{section_spliter} 2\n" +
        "[セクション2の内容]")

    return self._description_pattern.format(
        num_sections=self._num_sections,
        section_spliter=self._section_spliter)

  def get_instruction_args(self):
    return {"section_spliter": self._section_spliter,
            "num_sections": self._num_sections}

  def get_instruction_args_keys(self):
    return ["section_spliter", "num_sections"]

  def check_following(self, value):
    """応答に複数のセクションが含まれているかをチェックします"""
    section_splitter_patten = r"\s?" + self._section_spliter + r"\s?\d+\s?"
    sections = re.split(section_splitter_patten, value)
    num_sections = len(sections) - 1
    return num_sections >= self._num_sections


class ParagraphChecker(Instruction):
  """段落をチェックします"""

  def build_description(self, *, num_paragraphs = None):
    """指示の説明を構築します"""
    self._num_paragraphs = num_paragraphs
    if self._num_paragraphs is None or self._num_paragraphs < 0:
      self._num_paragraphs = random.randint(1, _NUM_PARAGRAPHS)

    self._description_pattern = (
        "{num_paragraphs}個の段落を含む必要があります。" +
        "段落はマークダウン区切り文字 *** で区切ってください。")

    return self._description_pattern.format(num_paragraphs=self._num_paragraphs)

  def get_instruction_args(self):
    return {"num_paragraphs": self._num_paragraphs}

  def get_instruction_args_keys(self):
    return ["num_paragraphs"]

  def check_following(self, value):
    """応答に必要な数の段落が含まれているかをチェックします"""
    paragraphs = re.split(r"\s?\*\*\*\s?", value)
    num_paragraphs = len(paragraphs)

    for index, paragraph in enumerate(paragraphs):
      if not paragraph.strip():
        if index == 0 or index == len(paragraphs) - 1:
          num_paragraphs -= 1
        else:
          return False

    return num_paragraphs == self._num_paragraphs


class RephraseChecker(Instruction):
  """言い換えをチェックします"""

  def build_description(self, *, original_message):
    """指示の説明を構築します"""
    if not self.is_change(original_message):
      raise ValueError(f"メッセージ {original_message} には *変更してください* の形式の変更が含まれていません。")

    self._reference_without_change = original_message
    self._description = ("言い換え：言い換えられた回答は、*変更してください* のような" +
                         "2つのアスタリスクの間の単語/文のみを変更してください。")
    return self._description

  def get_instruction_args(self):
    return {"original_message": self._reference_without_change}

  def get_instruction_args_keys(self):
    return ["original_message"]

  def check_following(self, value):
    """言い換えが指示に従っているかをチェックします"""
    if not self.is_change(value):
      raise ValueError(f"値 {value} には *変更してください* の形式の変更が含まれていません。")

    response_without_changes = self.strip_changes(value)
    reference_without_changes = self.strip_changes(
        self._reference_without_change)

    return response_without_changes == reference_without_changes

  def is_change(self, response):
    """応答に*変更してください*の形式の変更があるかをチェックします"""
    return re.search(r"\*.*\*", response)

  def strip_changes(self, response):
    """変更を削除します"""
    return re.sub(r"\*.*\*", "", response)


class KeywordFrequencyChecker(Instruction):
  """キーワードの頻度をチェックします"""

  def build_description(self, *, keyword = None, frequency = None, relation = None, lang = None):
    """指示の説明を構築します"""
    self._lang = lang or 'ja'
    
    if not keyword:
      self._keyword = instructions_util.generate_keywords(num_keywords=1, lang=self._lang)[0]
    else:
      self._keyword = keyword.strip()

    self._frequency = frequency
    if self._frequency is None or self._frequency < 0:
      self._frequency = random.randint(1, _KEYWORD_FREQUENCY)

    if relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif relation not in _COMPARISON_RELATION + _COMPARISON_RELATION_EN:
      raise ValueError(f"サポートされている関係は {_COMPARISON_RELATION} または {_COMPARISON_RELATION_EN} ですが、{relation} が指定されました")
    else:
      self._comparison_relation = relation

    # 日本語の関係演算子を使用
    if self._comparison_relation in _COMPARISON_RELATION_EN:
      relation_map = {"less than": "未満", "at least": "以上"}
      self._comparison_relation = relation_map.get(self._comparison_relation, self._comparison_relation)

    self._description_pattern = (
        "回答内で、単語「{keyword}」が{relation}{frequency}回出現する必要があります。")

    return self._description_pattern.format(
        keyword=self._keyword,
        relation=self._comparison_relation,
        frequency=self._frequency)

  def get_instruction_args(self):
    return {"keyword": self._keyword,
            "frequency": self._frequency,
            "relation": self._comparison_relation,
            "lang": self._lang}

  def get_instruction_args_keys(self):
    return ["keyword", "frequency", "relation", "lang"]

  def check_following(self, value):
    """応答に必要な頻度でキーワードが含まれているかをチェックします"""
    actual_occurrences = len(re.findall(
        re.escape(self._keyword), value, flags=re.IGNORECASE))

    if self._comparison_relation in ["未満", "less than"]:
      return actual_occurrences < self._frequency
    elif self._comparison_relation in ["以上", "at least"]:
      return actual_occurrences >= self._frequency


class ParagraphFirstWordCheck(Instruction):
  """段落とn番目の段落の最初の単語をチェックします"""

  def build_description(self, num_paragraphs = None, nth_paragraph = None, first_word = None, lang = None):
    """指示の説明を構築します"""
    self._lang = lang or 'ja'
    
    self._num_paragraphs = num_paragraphs
    if self._num_paragraphs is None or self._num_paragraphs < 0:
      self._num_paragraphs = random.randint(1, _NUM_PARAGRAPHS)

    self._nth_paragraph = nth_paragraph
    if (self._nth_paragraph is None or self._nth_paragraph <= 0 or
        self._nth_paragraph > self._num_paragraphs):
      self._nth_paragraph = random.randint(1, self._num_paragraphs + 1)

    self._first_word = first_word
    if self._first_word is None:
      self._first_word = instructions_util.generate_keywords(num_keywords=1, lang=self._lang)[0]
    self._first_word = self._first_word.lower() if self._lang == 'en' else self._first_word

    self._description_pattern = (
        "{num_paragraphs}個の段落を含む必要があります。" +
        "段落は2つの改行（\\n\\n）で区切られます。" +
        "{nth_paragraph}番目の段落は単語「{first_word}」で始まる必要があります。")

    return self._description_pattern.format(
        num_paragraphs=self._num_paragraphs,
        nth_paragraph=self._nth_paragraph,
        first_word=self._first_word)

  def get_instruction_args(self):
    return {"num_paragraphs": self._num_paragraphs,
            "nth_paragraph": self._nth_paragraph,
            "first_word": self._first_word,
            "lang": self._lang}

  def get_instruction_args_keys(self):
    return ["num_paragraphs", "nth_paragraph", "first_word", "lang"]

  def check_following(self, value):
    """必要な段落数と正しい最初の単語をチェックします"""
    paragraphs = re.split(r"\n\n", value)
    num_paragraphs = len(paragraphs)

    for paragraph in paragraphs:
      if not paragraph.strip():
        num_paragraphs -= 1

    # インデックスが範囲外にならないかをチェック
    if self._nth_paragraph <= num_paragraphs:
      paragraph = paragraphs[self._nth_paragraph - 1].strip()
      if not paragraph:
        return False
    else:
      return False

    # 日本語の場合は単純に最初の単語を取得
    if self._lang == 'ja':
      first_word = paragraph.split()[0] if paragraph.split() else ""
      return num_paragraphs == self._num_paragraphs and first_word == self._first_word
    else:
      # 英語の場合は句読点を削除
      first_word = ""
      punctuation = {".", ",", "?", "!", "'", '"'}
      word = paragraph.split()[0].strip()
      word = word.lstrip("'").lstrip('"')
      for letter in word:
        if letter in punctuation:
          break
        first_word += letter.lower()
      return num_paragraphs == self._num_paragraphs and first_word == self._first_word


class KeySentenceChecker(Instruction):
  """特定のキーセンテンスの存在をチェックします"""

  def build_description(self, key_sentences = None, num_sentences = None):
    """指示の説明を構築します"""
    if not key_sentences:
      self._key_sentences = set(["現時点では、これで問題ありません。"])
    else:
      self._key_sentences = key_sentences

    if not num_sentences:
      self._num_sentences = random.randint(1, len(self._key_sentences))
    else:
      self._num_sentences = num_sentences

    self._description_pattern = (
        "次の文のうち{num_sentences}個を含めてください：{key_sentences}")

    return self._description_pattern.format(
        num_sentences=self._num_sentences, key_sentences=self._key_sentences)

  def get_instruction_args(self):
    return {"num_sentences": self._num_sentences,
            "key_sentences": list(self._key_sentences)}

  def get_instruction_args_keys(self):
    return ["num_sentences", "key_sentences"]

  def check_following(self, value):
    """応答に期待されるキーセンテンスが含まれているかをチェックします"""
    count = 0
    sentences = instructions_util.split_into_sentences(value)
    for sentence in self._key_sentences:
      if sentence in sentences:
        count += 1

    return count == self._num_sentences


class ForbiddenWords(Instruction):
  """指定された単語が応答に使われていないかをチェックします"""

  def build_description(self, *, forbidden_words = None, lang = None):
    """指示の説明を構築します"""
    self._lang = lang or 'ja'
    
    if not forbidden_words:
      self._forbidden_words = instructions_util.generate_keywords(
          num_keywords=_NUM_KEYWORDS, lang=self._lang)
    else:
      self._forbidden_words = list(set(forbidden_words))
    self._forbidden_words = sorted(self._forbidden_words)
    
    self._description_pattern = ("回答にキーワード{forbidden_words}を含めないでください。")

    return self._description_pattern.format(forbidden_words=self._forbidden_words)

  def get_instruction_args(self):
    return {"forbidden_words": self._forbidden_words, "lang": self._lang}

  def get_instruction_args_keys(self):
    return ["forbidden_words", "lang"]

  def check_following(self, value):
    """応答に期待されるキーワードが含まれていないかをチェックします"""
    for word in self._forbidden_words:
      if self._lang == 'ja':
        # 日本語の場合は単純な文字列検索
        if word in value:
          return False
      else:
        # 英語の場合は単語境界を考慮
        if re.search(r"\b" + re.escape(word) + r"\b", value, flags=re.IGNORECASE):
          return False
    return True


class RephraseParagraph(Instruction):
  """段落が言い換えられているかをチェックします"""

  def build_description(self, *, original_paragraph, low, high):
    """指示の説明を構築します"""
    self._original_paragraph = original_paragraph
    self._low = low
    self._high = high

    self._description = ("次の段落を言い換えてください：" +
                         "{original_paragraph}\n" +
                         "あなたの回答は{low}から{high}個の同じ単語を含む必要があります。" +
                         "単語は、大文字小文字を無視して、すべての文字が同じ場合にのみ同じです。" +
                         "例えば、'run'は'Run'と同じですが、'ran'とは異なります。")

    return self._description.format(original_paragraph=original_paragraph,
                                    low=self._low, high=self._high)

  def get_instruction_args(self):
    return {"original_paragraph": self._original_paragraph,
            "low": self._low,
            "high": self._high}

  def get_instruction_args_keys(self):
    return ["original_paragraph", "low", "high"]

  def check_following(self, value):
    val_words = re.findall(r"\w+", value.lower())
    original_words = re.findall(r"\w+", self._original_paragraph.lower())
    similar_words = 0

    dict_val = collections.Counter(val_words)
    dict_original = collections.Counter(original_words)

    for word in dict_original:
      similar_words += min(dict_original[word], dict_val[word])

    return similar_words >= self._low and similar_words <= self._high


class TwoResponsesChecker(Instruction):
  """2つの応答が与えられているかをチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._description_pattern = (
        "2つの異なる回答を提供してください。回答は6つのアスタリスク記号（******）で区切ってください。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答に2つの異なる回答があるかをチェックします"""
    valid_responses = list()
    responses = value.split("******")
    for index, response in enumerate(responses):
      if not response.strip():
        if index != 0 and index != len(responses) - 1:
          return False
      else:
        valid_responses.append(response)
    return (len(valid_responses) == 2 and
            valid_responses[0].strip() != valid_responses[1].strip())


class RepeatPromptThenAnswer(Instruction):
  """プロンプトが最初に繰り返され、その後回答されるかをチェックします"""

  def build_description(self, *, prompt_to_repeat = None):
    """指示の説明を構築します"""
    if not prompt_to_repeat:
      raise ValueError("prompt_to_repeatを設定する必要があります。")
    else:
      self._prompt_to_repeat = prompt_to_repeat
    self._description_pattern = (
        "最初にリクエストを一字一句変更せずに繰り返し、その後に回答を提供してください" +
        "（1. リクエストを繰り返す前に他の単語や文字を言わないでください；" +
        "2. 繰り返す必要があるリクエストにはこの文は含まれません）")
    return self._description_pattern

  def get_instruction_args(self):
    return {"prompt_to_repeat": self._prompt_to_repeat}

  def get_instruction_args_keys(self):
    return ["prompt_to_repeat"]

  def check_following(self, value):
    if value.strip().lower().startswith(self._prompt_to_repeat.strip().lower()):
      return True
    return False


class LetterFrequencyChecker(Instruction):
  """文字の頻度をチェックします"""

  def build_description(self, *, letter = None, let_frequency = None, let_relation = None):
    """指示の説明を構築します"""
    if (not letter or len(letter) > 1 or 
        ord(letter.lower()) < 97 or ord(letter.lower()) > 122):
      self._letter = random.choice(list(string.ascii_letters))
    else:
      self._letter = letter.strip()
    self._letter = self._letter.lower()

    self._frequency = let_frequency
    if self._frequency is None or self._frequency < 0:
      self._frequency = random.randint(1, _LETTER_FREQUENCY)

    if let_relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif let_relation not in _COMPARISON_RELATION + _COMPARISON_RELATION_EN:
      raise ValueError(f"サポートされている関係は {_COMPARISON_RELATION} または {_COMPARISON_RELATION_EN} ですが、{let_relation} が指定されました")
    else:
      self._comparison_relation = let_relation

    # 日本語の関係演算子を使用
    if self._comparison_relation in _COMPARISON_RELATION_EN:
      relation_map = {"less than": "未満", "at least": "以上"}
      self._comparison_relation = relation_map.get(self._comparison_relation, self._comparison_relation)

    self._description_pattern = (
        "回答内で、文字「{letter}」が{let_relation}{let_frequency}回出現する必要があります。")

    return self._description_pattern.format(
        letter=self._letter,
        let_frequency=self._frequency,
        let_relation=self._comparison_relation)

  def get_instruction_args(self):
    return {"letter": self._letter,
            "let_frequency": self._frequency,
            "let_relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    return ["letter", "let_frequency", "let_relation"]

  def check_following(self, value):
    """応答に文字が正しい頻度で含まれているかをチェックします"""
    value = value.lower()
    letters = collections.Counter(value)

    if self._comparison_relation in ["未満", "less than"]:
      return letters[self._letter] < self._frequency
    else:
      return letters[self._letter] >= self._frequency


class CapitalLettersEnglishChecker(Instruction):
  """応答が英語で、すべて大文字であるかをチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._description_pattern = (
        "あなたの回答全体は英語で、すべて大文字で記述してください。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答が英語で、すべて大文字であるかをチェックします"""
    assert isinstance(value, str)
    
    # 簡易的な言語検出を使用
    detected_lang = instructions_util._detect_language(value)
    return value.isupper() and detected_lang == "en"


class LowercaseLettersEnglishChecker(Instruction):
  """応答が英語で、すべて小文字であるかをチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._description_pattern = (
        "あなたの回答全体は英語で、すべて小文字で記述してください。大文字は使用できません。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答が英語で、すべて小文字であるかをチェックします"""
    assert isinstance(value, str)
    
    # 簡易的な言語検出を使用
    detected_lang = instructions_util._detect_language(value)
    return value.islower() and detected_lang == "en"


class CommaChecker(Instruction):
  """応答にコンマが含まれていないかをチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._description_pattern = (
        "回答全体でコンマの使用を控えてください。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答にコンマが含まれていないかをチェックします"""
    return not re.search(r"\,", value)


class CapitalWordFrequencyChecker(Instruction):
  """すべて大文字の単語の頻度をチェックします"""

  def build_description(self, capital_frequency = None, capital_relation = None):
    """指示の説明を構築します"""
    self._frequency = capital_frequency
    if self._frequency is None:
      self._frequency = random.randint(1, _ALL_CAPITAL_WORD_FREQUENCY)

    self._comparison_relation = capital_relation
    if capital_relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif capital_relation not in _COMPARISON_RELATION + _COMPARISON_RELATION_EN:
      raise ValueError(f"サポートされている関係は {_COMPARISON_RELATION} または {_COMPARISON_RELATION_EN} ですが、{capital_relation} が指定されました")

    # 日本語の関係演算子を使用
    if self._comparison_relation in _COMPARISON_RELATION_EN:
      relation_map = {"less than": "未満", "at least": "以上"}
      self._comparison_relation = relation_map.get(self._comparison_relation, self._comparison_relation)

    self._description_pattern = (
        "回答内で、すべて大文字の単語が{relation}{frequency}個出現する必要があります。")

    return self._description_pattern.format(
        frequency=self._frequency, relation=self._comparison_relation)

  def get_instruction_args(self):
    return {"capital_frequency": self._frequency,
            "capital_relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    return ["capital_frequency", "capital_relation"]

  def check_following(self, value):
    """すべて大文字の単語の頻度をチェックします"""
    # 単語を抽出（英数字のみ）
    words = re.findall(r'\b[A-Za-z]+\b', value)
    capital_words = [word for word in words if word.isupper()]
    capital_words_count = len(capital_words)

    if self._comparison_relation in ["未満", "less than"]:
      return capital_words_count < self._frequency
    else:
      return capital_words_count >= self._frequency


# 日本語特化の指示チェッククラス

class JapaneseHiraganaOnlyChecker(Instruction):
  """ひらがなのみを使用しているかチェックする指示クラス（英語の小文字制約に相当）"""

  def build_description(self, **kwargs):
    """指示の説明を構築"""
    return "回答はすべてひらがなで書いてください。漢字とカタカナは一切使用できません。"

  def get_instruction_args(self):
    return {}

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """回答がひらがなのみを使用しているかチェック"""
    # 空白、句読点、英数字以外の文字をチェック
    # ひらがな文字の範囲
    for char in value:
      # 空白、改行、句読点、基本的な記号は許可
      if char.isspace() or char in '。、！？（）「」『』［］｛｝【】〈〉《》〔〕・':
        continue
      # ひらがなの範囲をチェック
      if '\u3040' <= char <= '\u309F':
        continue
      # ひらがな以外の文字が見つかったらFalse
      return False
    
    # すべての文字がひらがなまたは許可された記号である
    return True


class JapaneseKatakanaOnlyChecker(Instruction):
  """カタカナのみを使用しているかチェックする指示クラス（英語の大文字制約に相当）"""

  def build_description(self, **kwargs):
    """指示の説明を構築"""
    return "回答はすべてカタカナで書いてください。ひらがなと漢字は一切使用できません。"

  def get_instruction_args(self):
    return {}

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """回答がカタカナのみを使用しているかチェック"""
    # 空白、句読点、英数字以外の文字をチェック
    # カタカナ文字の範囲
    for char in value:
      # 空白、改行、句読点、基本的な記号は許可
      if char.isspace() or char in '。、！？（）「」『』［］｛｝【】〈〉《》〔〕・':
        continue
      # カタカナの範囲をチェック
      if '\u30A0' <= char <= '\u30FF':
        continue
      # カタカナ以外の文字が見つかったらFalse
      return False
    
    # すべての文字がカタカナまたは許可された記号である
    return True


class JapaneseBracketEmphasisFrequencyChecker(Instruction):
  """【】強調表現の頻度制約クラス（英語の大文字単語頻度に相当）"""

  def build_description(self, capital_relation="以上", capital_frequency=1, **kwargs):
    """指示の説明を構築"""
    self._capital_relation = capital_relation
    self._capital_frequency = capital_frequency
    
    if capital_relation == "未満":
      return f"【】で囲んだ強調表現を{capital_frequency}回未満使用してください。"
    elif capital_relation == "以上":
      return f"【】で囲んだ強調表現を{capital_frequency}回以上使用してください。"
    elif capital_relation == "正確に":
      return f"【】で囲んだ強調表現を正確に{capital_frequency}回使用してください。"
    else:
      return f"【】で囲んだ強調表現を{capital_frequency}回{capital_relation}使用してください。"

  def get_instruction_args(self):
    return {
      "capital_relation": self._capital_relation,
      "capital_frequency": self._capital_frequency
    }

  def get_instruction_args_keys(self):
    return ["capital_relation", "capital_frequency"]

  def check_following(self, value):
    """【】強調表現の頻度をチェック"""
    emphasis_pattern = re.compile(r'【[^】]*】')
    matches = emphasis_pattern.findall(value)
    count = len(matches)
    
    if self._capital_relation == "less than" or self._capital_relation == "未満":
      return count < self._capital_frequency
    elif self._capital_relation == "at least" or self._capital_relation == "以上":
      return count >= self._capital_frequency
    elif self._capital_relation == "exactly" or self._capital_relation == "正確に":
      return count == self._capital_frequency
    else:
      return False


class JapaneseNoToutenChecker(Instruction):
  """読点（、）禁止制約クラス（英語のカンマ禁止に相当）"""

  def build_description(self, **kwargs):
    """指示の説明を構築"""
    return "回答に読点（、）を使用しないでください。"

  def get_instruction_args(self):
    return {}

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """読点が含まれていないかチェック"""
    return '、' not in value


class JapaneseStarFrequencyChecker(Instruction):
  """星印記号（★）の頻度制約クラス（英語のアスタリスクに相当）"""

  def build_description(self, let_relation="以上", let_frequency=6, letter="★", **kwargs):
    """指示の説明を構築"""
    self._let_relation = let_relation
    self._let_frequency = let_frequency
    self._letter = letter
    
    if let_relation == "未満":
      return f"'{letter}'記号を{let_frequency}回未満含めてください。"
    elif let_relation == "以上":
      return f"'{letter}'記号を{let_frequency}回以上含めてください。"
    elif let_relation == "正確に":
      return f"'{letter}'記号を正確に{let_frequency}回含めてください。"
    else:
      return f"'{letter}'記号を{let_frequency}回{let_relation}含めてください。"

  def get_instruction_args(self):
    return {
      "let_relation": self._let_relation,
      "let_frequency": self._let_frequency,
      "letter": self._letter
    }

  def get_instruction_args_keys(self):
    return ["let_relation", "let_frequency", "letter"]

  def check_following(self, value):
    """星印記号の頻度をチェック"""
    count = value.count(self._letter)
    
    if self._let_relation == "less than" or self._let_relation == "未満":
      return count < self._let_frequency
    elif self._let_relation == "at least" or self._let_relation == "以上":
      return count >= self._let_frequency
    elif self._let_relation == "exactly" or self._let_relation == "正確に":
      return count == self._let_frequency
    else:
      return False


class JapanesePostscriptChecker(Instruction):
  """日本語追記マーカークラス（英語のP.S.に相当）"""

  def build_description(self, postscript_marker="追記", **kwargs):
    """指示の説明を構築"""
    self._postscript_marker = postscript_marker
    return f"回答の最後に「{postscript_marker}」で始まる追記を含めてください。"

  def get_instruction_args(self):
    return {"postscript_marker": self._postscript_marker}

  def get_instruction_args_keys(self):
    return ["postscript_marker"]

  def check_following(self, value):
    """追記マーカーが含まれているかチェック"""
    lines = value.strip().split('\n')
    for line in reversed(lines):
      line = line.strip()
      if line:
        return line.startswith(self._postscript_marker)
    return False


class JapaneseEndingPhraseChecker(Instruction):
  """日本語終了フレーズクラス（英語のend_checkerに相当）"""

  def build_description(self, end_phrase="", **kwargs):
    """指示の説明を構築"""
    self._end_phrase = end_phrase
    return f"回答を「{end_phrase}」という正確なフレーズで終えてください。"

  def get_instruction_args(self):
    return {"end_phrase": self._end_phrase}

  def get_instruction_args_keys(self):
    return ["end_phrase"]

  def check_following(self, value):
    """指定されたフレーズで終わっているかチェック"""
    return value.strip().endswith(self._end_phrase)


class JapaneseOnlyLanguageChecker(Instruction):
  """日本語のみ制約クラス"""

  def build_description(self, language="ja", **kwargs):
    """指示の説明を構築"""
    self._language = language
    if language == "ja":
      return "日本語のみを使用して回答してください。他の言語は使用できません。"
    else:
      lang_name = _LANGUAGES.get(language, language)
      return f"{lang_name}のみを使用して回答してください。他の言語は使用できません。"

  def get_instruction_args(self):
    return {"language": self._language}

  def get_instruction_args_keys(self):
    return ["language"]

  def check_following(self, value):
    """日本語のみで構成されているかチェック"""
    if self._language == "ja":
      # 日本語文字（ひらがな、カタカナ、漢字）
      japanese_chars = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
      
      # 基本的な記号、数字、スペースは許可
      allowed_chars = re.compile(r'[0-9\s\n.,!?()「」『』【】\u3000-\u303F\uFF00-\uFFEF#★]')
      
      # 英語のアルファベットをチェック
      english_chars = re.compile(r'[a-zA-Z]')
      
      # 英語が含まれている場合はNG（ただし基本的な記号は除く）
      if english_chars.search(value):
        return False
      
      # 少なくとも一つは日本語文字が含まれている必要がある
      return japanese_chars.search(value) is not None
    else:
      # 他の言語の場合は既存のロジックを使用
      detected_language = instructions_util._detect_language(value)
      return detected_language == self._language


class JapaneseLetterFrequencyChecker(Instruction):
  """日本語文字頻度制約クラス（日本語の特定文字に対応）"""

  def build_description(self, let_relation="以上", let_frequency=1, letter="あ", **kwargs):
    """指示の説明を構築"""
    self._let_relation = let_relation
    self._let_frequency = let_frequency
    self._letter = letter
    
    if let_relation == "未満":
      return f"文字「{letter}」は{let_frequency}回未満で現れる必要があります。"
    elif let_relation == "以上":
      return f"文字「{letter}」を{let_frequency}回以上含めてください。"
    elif let_relation == "正確に":
      return f"文字「{letter}」を正確に{let_frequency}回含めてください。"
    else:
      return f"文字「{letter}」を{let_frequency}回{let_relation}含めてください。"

  def get_instruction_args(self):
    return {
      "let_relation": self._let_relation,
      "let_frequency": self._let_frequency,
      "letter": self._letter
    }

  def get_instruction_args_keys(self):
    return ["let_relation", "let_frequency", "letter"]

  def check_following(self, value):
    """指定された文字の頻度をチェック"""
    count = value.count(self._letter)
    
    if self._let_relation == "less than" or self._let_relation == "未満":
      return count < self._let_frequency
    elif self._let_relation == "at least" or self._let_relation == "以上":
      return count >= self._let_frequency
    elif self._let_relation == "exactly" or self._let_relation == "正確に":
      return count == self._let_frequency
    else:
      return False


# 不足していた指示クラスを追加

class NumberOfParagraphs(Instruction):
  """段落の数をチェックします"""

  def build_description(self, *, num_paragraphs = None):
    """指示の説明を構築します"""
    self._num_paragraphs = num_paragraphs
    if self._num_paragraphs is None or self._num_paragraphs < 0:
      self._num_paragraphs = random.randint(1, _NUM_PARAGRAPHS)
    
    self._description_pattern = (
        "回答は正確に{num_paragraphs}段落を含む必要があります。")
    return self._description_pattern.format(num_paragraphs=self._num_paragraphs)

  def get_instruction_args(self):
    return {"num_paragraphs": self._num_paragraphs}

  def get_instruction_args_keys(self):
    return ["num_paragraphs"]

  def check_following(self, value):
    """段落の数が指示に従っているかをチェックします"""
    paragraphs = [p.strip() for p in value.split('\n\n') if p.strip()]
    # マークダウン区切り文字***でも分割
    if '***' in value:
      paragraphs = [p.strip() for p in value.split('***') if p.strip()]
    return len(paragraphs) == self._num_paragraphs


class KeywordFrequencyChecker(Instruction):
  """特定のキーワードの頻度をチェックします"""

  def build_description(self, *, keyword = None, frequency = None, relation = None):
    """指示の説明を構築します"""
    self._keyword = keyword or "キーワード"
    self._frequency = frequency or _KEYWORD_FREQUENCY
    self._relation = relation or "以上"

    if self._relation == "未満":
      self._description_pattern = (
          "「{keyword}」という単語を{frequency}回未満で使用してください。")
    elif self._relation == "以上":
      self._description_pattern = (
          "「{keyword}」という単語を少なくとも{frequency}回使用してください。")
    elif self._relation == "正確に":
      self._description_pattern = (
          "「{keyword}」という単語を正確に{frequency}回使用してください。")
    else:
      self._description_pattern = (
          "「{keyword}」という単語を{frequency}回{relation}使用してください。")

    return self._description_pattern.format(
        keyword=self._keyword, frequency=self._frequency)

  def get_instruction_args(self):
    return {"keyword": self._keyword, "frequency": self._frequency, 
            "relation": self._relation}

  def get_instruction_args_keys(self):
    return ["keyword", "frequency", "relation"]

  def check_following(self, value):
    """キーワードの頻度が指示に従っているかをチェックします"""
    count = value.count(self._keyword)
    
    if self._relation in ["未満", "less than"]:
      return count < self._frequency
    elif self._relation in ["以上", "at least"]:
      return count >= self._frequency
    elif self._relation in ["正確に", "exactly"]:
      return count == self._frequency
    else:
      return False


class LetterFrequencyChecker(Instruction):
  """特定の文字の頻度をチェックします"""

  def build_description(self, *, letter = None, let_frequency = None, let_relation = None):
    """指示の説明を構築します"""
    self._letter = letter or "あ"
    self._let_frequency = let_frequency or _LETTER_FREQUENCY
    self._let_relation = let_relation or "以上"

    if self._let_relation == "未満":
      return f"文字「{self._letter}」は{self._let_frequency}回未満で現れる必要があります。"
    elif self._let_relation == "以上":
      return f"文字「{self._letter}」を{self._let_frequency}回以上含めてください。"
    elif self._let_relation == "正確に":
      return f"文字「{self._letter}」を正確に{self._let_frequency}回含めてください。"
    else:
      return f"文字「{self._letter}」を{self._let_frequency}回{self._let_relation}含めてください。"

  def get_instruction_args(self):
    return {"letter": self._letter, "let_frequency": self._let_frequency, 
            "let_relation": self._let_relation}

  def get_instruction_args_keys(self):
    return ["letter", "let_frequency", "let_relation"]

  def check_following(self, value):
    """文字の頻度が指示に従っているかをチェックします"""
    count = value.count(self._letter)
    
    if self._let_relation in ["未満", "less than"]:
      return count < self._let_frequency
    elif self._let_relation in ["以上", "at least"]:
      return count >= self._let_frequency
    elif self._let_relation in ["正確に", "exactly"]:
      return count == self._let_frequency
    else:
      return False


class RepeatPromptChecker(Instruction):
  """プロンプトの繰り返しをチェックします"""

  def build_description(self, *, prompt_to_repeat = None):
    """指示の説明を構築します"""
    self._prompt_to_repeat = prompt_to_repeat or ""
    
    self._description_pattern = (
        "最初にリクエストを一字一句変更せずに繰り返し、その後に回答してください。")
    return self._description_pattern

  def get_instruction_args(self):
    return {"prompt_to_repeat": self._prompt_to_repeat}

  def get_instruction_args_keys(self):
    return ["prompt_to_repeat"]

  def check_following(self, value):
    """プロンプトが繰り返されているかをチェックします"""
    if not self._prompt_to_repeat:
      return True
    
    # 改行で分割して最初の部分をチェック
    lines = value.strip().split('\n')
    if not lines:
      return False
    
    first_part = lines[0].strip()
    return first_part == self._prompt_to_repeat.strip()


class TwoResponsesChecker(Instruction):
  """2つの異なる回答をチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._description_pattern = (
        "正確に2つの異なる回答を提供してください。回答を6つの星印記号で区切ってください：★★★★★★。")
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """2つの回答が星印で区切られているかをチェックします"""
    # 6つの星印記号で分割
    separator = "★★★★★★"
    parts = value.split(separator)
    
    # 正確に2つの部分に分かれているかチェック
    if len(parts) != 2:
      return False
    
    # 両方の部分が空でないかチェック
    for part in parts:
      if not part.strip():
        return False
    
    return True


# 一般的な構造・形式制約クラス（日本語対応）

class QuotationChecker(Instruction):
  """応答が二重引用符で囲まれているかをチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._description_pattern = (
        "回答全体を二重引用符で囲んでください。"
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答が二重引用符で囲まれているかをチェックします"""
    value = value.strip()
    return len(value) > 1 and value[0] == '"' and value[-1] == '"'


class HighlightSectionChecker(Instruction):
  """ハイライトされたセクションをチェックします"""

  def build_description(self, *, num_highlights=None):
    """指示の説明を構築します
    
    Args:
      num_highlights: ハイライトされたセクションの最小数を指定する整数
      
    Returns:
      指示の説明を表す文字列
    """
    self._num_highlights = num_highlights
    if self._num_highlights is None or self._num_highlights < 0:
      self._num_highlights = random.randint(1, _NUM_HIGHLIGHTED_SECTIONS)

    self._description_pattern = (
        "マークダウンで少なくとも{num_highlights}つのセクションをハイライトしてください。例：*ハイライトされたセクション*。")

    return self._description_pattern.format(num_highlights=self._num_highlights)

  def get_instruction_args(self):
    return {"num_highlights": self._num_highlights}

  def get_instruction_args_keys(self):
    return ["num_highlights"]

  def check_following(self, value):
    """ハイライトされたセクションの数が要件を満たしているかをチェックします
    
    Args:
      value: 応答を表す文字列。応答には*highlighted*の形式で
        ハイライトされたセクションが含まれていることが期待されます
        
    Returns:
      *ハイライトされたセクション*の形式での実際のハイライトされた
      セクションの数が最小要件を満たしている場合はTrue、そうでない場合はFalse
    """
    num_highlights = 0
    highlights = re.findall(r"\*[^\n\*]*\*", value)
    double_highlights = re.findall(r"\*\*[^\n\*]*\*\*", value)
    for highlight in highlights:
      if highlight.strip("*").strip():
        num_highlights += 1
    for highlight in double_highlights:
      if highlight.removeprefix("**").removesuffix("**").strip():
        num_highlights += 1

    return num_highlights >= self._num_highlights


class TitleChecker(Instruction):
  """応答にタイトルがあるかをチェックします"""

  def build_description(self):
    """指示の説明を構築します"""
    self._description_pattern = (
        "回答には二重角括弧で囲まれたタイトルを含める必要があります。例：<<タイトル>>。"
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答にタイトルが含まれているかをチェックします"""
    pattern = r"<<[^\n]+>>"
    re_pattern = re.compile(pattern)
    titles = re.findall(re_pattern, value)

    for title in titles:
      if title.lstrip("<").rstrip(">").strip():
        return True
    return False

# 日本語制約の便利関数とマッピング

def check_japanese_constraint(response: str, constraint_type: str, **kwargs) -> bool:
  """日本語制約の統一チェック関数"""
  
  if constraint_type == "hiragana_only":
    checker = JapaneseHiraganaOnlyChecker("temp")
    return checker.check_following(response)
  
  elif constraint_type == "katakana_only":
    checker = JapaneseKatakanaOnlyChecker("temp")
    return checker.check_following(response)
  
  elif constraint_type == "bracket_emphasis_frequency":
    relation = kwargs.get('relation', 'at least')
    frequency = kwargs.get('frequency', 1)
    checker = JapaneseBracketEmphasisFrequencyChecker("temp")
    checker.build_description(capital_relation=relation, capital_frequency=frequency)
    return checker.check_following(response)
  
  elif constraint_type == "no_touten":
    checker = JapaneseNoToutenChecker("temp")
    return checker.check_following(response)
  
  elif constraint_type == "star_frequency":
    relation = kwargs.get('relation', 'at least')
    frequency = kwargs.get('frequency', 6)
    letter = kwargs.get('letter', '★')
    checker = JapaneseStarFrequencyChecker("temp")
    checker.build_description(let_relation=relation, let_frequency=frequency, letter=letter)
    return checker.check_following(response)
  
  elif constraint_type == "japanese_postscript":
    marker = kwargs.get('marker', '追記')
    checker = JapanesePostscriptChecker("temp")
    checker.build_description(postscript_marker=marker)
    return checker.check_following(response)
  
  elif constraint_type == "japanese_ending":
    phrase = kwargs.get('phrase', '')
    checker = JapaneseEndingPhraseChecker("temp")
    checker.build_description(end_phrase=phrase)
    return checker.check_following(response)
  
  elif constraint_type == "japanese_only":
    language = kwargs.get('language', 'ja')
    checker = JapaneseOnlyLanguageChecker("temp")
    checker.build_description(language=language)
    return checker.check_following(response)
  
  elif constraint_type == "japanese_letter_frequency":
    relation = kwargs.get('relation', 'at least')
    frequency = kwargs.get('frequency', 1)
    letter = kwargs.get('letter', 'あ')
    checker = JapaneseLetterFrequencyChecker("temp")
    checker.build_description(let_relation=relation, let_frequency=frequency, letter=letter)
    return checker.check_following(response)
  
  else:
    return False


# 日本語対応指示クラスのマッピング
JAPANESE_INSTRUCTION_MAPPING = {
    "change_case:japanese_hiragana": JapaneseHiraganaOnlyChecker,
    "change_case:japanese_katakana": JapaneseKatakanaOnlyChecker,
    "change_case:japanese_bracket_emphasis": JapaneseBracketEmphasisFrequencyChecker,
    "punctuation:no_touten": JapaneseNoToutenChecker,
    "keywords:japanese_star_frequency": JapaneseStarFrequencyChecker,
    "keywords:japanese_letter_frequency": JapaneseLetterFrequencyChecker,
    "detectable_content:japanese_postscript": JapanesePostscriptChecker,
    "startend:japanese_end_checker": JapaneseEndingPhraseChecker,
    "language:japanese_only": JapaneseOnlyLanguageChecker,
}


def get_japanese_instruction(instruction_id: str, instruction_name: str):
  """日本語対応指示クラスを取得"""
  if instruction_name in JAPANESE_INSTRUCTION_MAPPING:
    return JAPANESE_INSTRUCTION_MAPPING[instruction_name](instruction_id)
  else:
    raise ValueError(f"未対応の日本語指示: {instruction_name}")


def convert_english_to_japanese_instruction(instruction_id_list, kwargs_list):
  """英語の指示IDを日本語対応に変換"""
  japanese_instruction_ids = []
  japanese_kwargs = []
  
  for i, instruction_id in enumerate(instruction_id_list):
    kwargs = kwargs_list[i] if i < len(kwargs_list) else {}
    
    # 英語の制約を日本語制約に変換
    if instruction_id == "change_case:english_lowercase":
      japanese_instruction_ids.append("change_case:japanese_hiragana")
      japanese_kwargs.append({})
      
    elif instruction_id == "change_case:english_capital":
      japanese_instruction_ids.append("change_case:japanese_katakana")
      japanese_kwargs.append({})
      
    elif instruction_id == "change_case:capital_word_frequency":
      japanese_instruction_ids.append("change_case:japanese_bracket_emphasis")
      japanese_kwargs.append(kwargs)
      
    elif instruction_id == "punctuation:no_comma":
      japanese_instruction_ids.append("punctuation:no_touten")
      japanese_kwargs.append({})
      
    elif instruction_id == "keywords:letter_frequency" and kwargs.get("letter") == "#":
      # ハッシュタグの場合はそのまま
      japanese_instruction_ids.append(instruction_id)
      japanese_kwargs.append(kwargs)
      
    elif instruction_id == "keywords:letter_frequency":
      # 他の文字の場合は日本語文字にマッピング
      letter_mapping = {"o": "あ", "t": "と", "\!": "！", "*": "★"}
      original_letter = kwargs.get("letter", "")
      if original_letter in letter_mapping:
        new_kwargs = kwargs.copy()
        new_kwargs["letter"] = letter_mapping[original_letter]
        japanese_instruction_ids.append("keywords:japanese_letter_frequency")
        japanese_kwargs.append(new_kwargs)
      else:
        japanese_instruction_ids.append(instruction_id)
        japanese_kwargs.append(kwargs)
        
    elif instruction_id == "detectable_content:postscript":
      japanese_instruction_ids.append("detectable_content:japanese_postscript")
      # P.S.やP.P.Sを追記に変換
      new_kwargs = kwargs.copy()
      marker = kwargs.get("postscript_marker", "P.S.")
      if marker in ["P.S.", "P.P.S"]:
        new_kwargs["postscript_marker"] = "追記"
      japanese_kwargs.append(new_kwargs)
      
    elif instruction_id == "startend:end_checker":
      japanese_instruction_ids.append("startend:japanese_end_checker")
      japanese_kwargs.append(kwargs)
      
    elif instruction_id == "language:response_language":
      if kwargs.get("language") == "ja":
        japanese_instruction_ids.append("language:japanese_only")
        japanese_kwargs.append(kwargs)
      else:
        # 他の言語の場合はそのまま
        japanese_instruction_ids.append(instruction_id)
        japanese_kwargs.append(kwargs)
        
    else:
      # その他の制約はそのまま
      japanese_instruction_ids.append(instruction_id)
      japanese_kwargs.append(kwargs)
  
  return japanese_instruction_ids, japanese_kwargs


# 日本語文字種チェック用ヘルパー関数
def is_hiragana_char(char: str) -> bool:
  """文字がひらがなかどうかをチェック"""
  return '\u3040' <= char <= '\u309F'


def is_katakana_char(char: str) -> bool:
  """文字がカタカナかどうかをチェック"""
  return '\u30A0' <= char <= '\u30FF'


def is_kanji_char(char: str) -> bool:
  """文字が漢字かどうかをチェック"""
  return '\u4E00' <= char <= '\u9FAF'


def is_japanese_char(char: str) -> bool:
  """文字が日本語（ひらがな、カタカナ、漢字）かどうかをチェック"""
  return is_hiragana_char(char) or is_katakana_char(char) or is_kanji_char(char)


def count_japanese_chars(text: str) -> dict:
  """日本語文字の種類別カウント"""
  counts = {
    'hiragana': 0,
    'katakana': 0,
    'kanji': 0,
    'total_japanese': 0
  }
  
  for char in text:
    if is_hiragana_char(char):
      counts['hiragana'] += 1
      counts['total_japanese'] += 1
    elif is_katakana_char(char):
      counts['katakana'] += 1
      counts['total_japanese'] += 1
    elif is_kanji_char(char):
      counts['kanji'] += 1
      counts['total_japanese'] += 1
  
  return counts


# テスト用関数
def test_japanese_constraints():
  """日本語制約チェック関数のテスト"""
  print("=== 日本語制約チェック関数テスト ===")
  
  # ひらがなのみテスト
  print("1. ひらがなのみチェック:")
  hiragana_text = "これはひらがなだけのぶんしょうです。"
  mixed_text = "これはひらがなとカタカナの文章です。"
  print(f"  '{hiragana_text}': {check_japanese_constraint(hiragana_text, 'hiragana_only')}")
  print(f"  '{mixed_text}': {check_japanese_constraint(mixed_text, 'hiragana_only')}")
  
  # カタカナのみテスト
  print("2. カタカナのみチェック:")
  katakana_text = "コレハカタカナダケノブンショウデス。"
  print(f"  '{katakana_text}': {check_japanese_constraint(katakana_text, 'katakana_only')}")
  print(f"  '{mixed_text}': {check_japanese_constraint(mixed_text, 'katakana_only')}")
  
  # 強調表現テスト
  print("3. 【】強調表現チェック:")
  emphasis_text = "これは【重要】な【ポイント】です【確認】してください。"
  print(f"  '{emphasis_text}': {check_japanese_constraint(emphasis_text, 'bracket_emphasis_frequency', relation='以上', frequency=3)}")
  
  # 読点チェック
  print("4. 読点なしチェック:")
  no_touten_text = "これは読点のない文章です。"
  with_touten_text = "これは、読点のある文章です。"
  print(f"  '{no_touten_text}': {check_japanese_constraint(no_touten_text, 'no_touten')}")
  print(f"  '{with_touten_text}': {check_japanese_constraint(with_touten_text, 'no_touten')}")
  
  # 星印チェック
  print("5. 星印頻度チェック:")
  star_text = "これは★★★★★★で区切られた文章です。"
  print(f"  '{star_text}': {check_japanese_constraint(star_text, 'star_frequency', relation='以上', frequency=6)}")
  
  # 追記チェック
  print("6. 追記マーカーチェック:")
  postscript_text = "本文です。\n追記 これは追記です。"
  print(f"  '{postscript_text}': {check_japanese_constraint(postscript_text, 'japanese_postscript', marker='追記')}")
  
  # 終了フレーズチェック
  print("7. 終了フレーズチェック:")
  ending_text = "これは文章です。他にご不明な点はございますか？"
  print(f"  '{ending_text}': {check_japanese_constraint(ending_text, 'japanese_ending', phrase='他にご不明な点はございますか？')}")
  
  # 日本語のみチェック
  print("8. 日本語のみチェック:")
  japanese_only_text = "これは日本語だけの文章です。"
  mixed_lang_text = "これはJapanese and English混合の文章です。"
  print(f"  '{japanese_only_text}': {check_japanese_constraint(japanese_only_text, 'japanese_only')}")
  print(f"  '{mixed_lang_text}': {check_japanese_constraint(mixed_lang_text, 'japanese_only')}")


def test_japanese_instructions():
  """日本語指示クラスのテスト"""
  print("=== 日本語指示クラステスト ===")
  
  # ひらがなのみ
  hiragana_inst = JapaneseHiraganaOnlyChecker("test_hiragana")
  print(f"1. ひらがなのみ指示: {hiragana_inst.build_description()}")
  print(f"   チェック結果: {hiragana_inst.check_following('これはひらがなです')}")
  
  # カタカナのみ
  katakana_inst = JapaneseKatakanaOnlyChecker("test_katakana")
  print(f"2. カタカナのみ指示: {katakana_inst.build_description()}")
  print(f"   チェック結果: {katakana_inst.check_following('コレハカタカナデス')}")
  
  # 強調表現
  emphasis_inst = JapaneseBracketEmphasisFrequencyChecker("test_emphasis")
  print(f"3. 強調表現指示: {emphasis_inst.build_description(capital_frequency=2)}")
  emphasis_inst.build_description(capital_frequency=2)
  print(f"   チェック結果: {emphasis_inst.check_following('これは【重要】な【ポイント】です')}")
  
  # 読点禁止
  touten_inst = JapaneseNoToutenChecker("test_touten")
  print(f"4. 読点禁止指示: {touten_inst.build_description()}")
  print(f"   チェック結果: {touten_inst.check_following('これは読点なしです')}")
  
  # 変換テスト
  print("5. 英語→日本語指示変換テスト:")
  english_ids = ["change_case:english_lowercase", "punctuation:no_comma"]
  english_kwargs = [{}, {}]
  japanese_ids, japanese_kwargs = convert_english_to_japanese_instruction(english_ids, english_kwargs)
  print(f"   英語: {english_ids}")
  print(f"   日本語: {japanese_ids}")


# 英語版指示クラス（instructions.pyより統合）

class ResponseLanguageCheckerEN(Instruction):
  """応答全体の言語をチェックします（英語版）"""

  def build_description(self, *, language = None):
    """指示の説明を構築します"""
    self._language = language
    if self._language is None:
      available_languages = list(_LANGUAGES.keys()) if hasattr(instructions_util, 'LANGUAGE_CODES') else ['en', 'ja', 'fr', 'de', 'es']
      self._language = random.choice(available_languages)
    
    self._description_pattern = (
        "Your ENTIRE response should be in {language} language, no other " +
        "language is allowed.")
    return self._description_pattern.format(language=_LANGUAGES.get(self._language, self._language))

  def get_instruction_args(self):
    return {"language": self._language}

  def get_instruction_args_keys(self):
    return ["language"]

  def check_following(self, value):
    """応答全体の言語が指示に従っているかをチェックします"""
    assert isinstance(value, str)

    try:
      return langdetect.detect(value) == self._language
    except langdetect.LangDetectException as e:
      logging.error(
          "Unable to detect language for text %s due to %s", value, e
      )
      return True


class NumberOfSentencesEN(Instruction):
  """文の数をチェックします（英語版）"""

  def build_description(self, *, num_sentences = None, relation = None):
    """指示の説明を構築します"""
    self._num_sentences_threshold = num_sentences
    if (self._num_sentences_threshold is None or
        self._num_sentences_threshold < 0):
      self._num_sentences_threshold = random.randint(1, _MAX_NUM_SENTENCES)

    if relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION_ORIGINAL)
    elif relation not in _COMPARISON_RELATION_ORIGINAL + _COMPARISON_RELATION_JA:
      raise ValueError("The supported relation for comparison must be in "
                       f"{_COMPARISON_RELATION_ORIGINAL + _COMPARISON_RELATION_JA}, but {relation} is given.")
    else:
      self._comparison_relation = relation

    self._description_pattern = (
        "Your response should contain {relation} {num_sentences} sentences.")
    return self._description_pattern.format(
        relation=self._comparison_relation,
        num_sentences=self._num_sentences_threshold)

  def get_instruction_args(self):
    return {"num_sentences": self._num_sentences_threshold,
            "relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    return ["num_sentences", "relation"]

  def check_following(self, value):
    """文の数が指示に従っているかをチェックします"""
    num_sentences = instructions_util.count_sentences(value)
    if self._comparison_relation == _COMPARISON_RELATION_ORIGINAL[0]:
      return num_sentences < self._num_sentences_threshold
    elif self._comparison_relation == _COMPARISON_RELATION_ORIGINAL[1]:
      return num_sentences >= self._num_sentences_threshold


class PlaceholderCheckerEN(Instruction):
  """テンプレート作成におけるプレースホルダーをチェックします（英語版）"""

  def build_description(self, *, num_placeholders = None):
    """指示の説明を構築します"""
    self._num_placeholders = num_placeholders
    if self._num_placeholders is None or self._num_placeholders < 0:
      self._num_placeholders = random.randint(1, _NUM_PLACEHOLDERS)
    self._description_pattern = (
        "The response must contain at least {num_placeholders} placeholders " +
        "represented by square brackets, such as [address].")
    return self._description_pattern.format(
        num_placeholders=self._num_placeholders)

  def get_instruction_args(self):
    return {"num_placeholders": self._num_placeholders}

  def get_instruction_args_keys(self):
    return ["num_placeholders"]

  def check_following(self, value):
    """プレースホルダーの数が指示に従っているかをチェックします"""
    placeholders = re.findall(r"\[.*?\]", value)
    num_placeholders = len(placeholders)
    return num_placeholders >= self._num_placeholders


class BulletListCheckerEN(Instruction):
  """プロンプト内の箇条書きリストをチェックします（英語版）"""

  def build_description(self, *, num_bullets = None):
    """指示の説明を構築します"""
    self._num_bullets = num_bullets
    if self._num_bullets is None or self._num_bullets < 0:
      self._num_bullets = random.randint(1, _NUM_BULLETS)
    self._description_pattern = (
        "Your answer must contain exactly {num_bullets} bullet points. " +
        "Use the markdown bullet points such as:\n" +
        "* This is point 1. \n" +
        "* This is point 2")
    return self._description_pattern.format(
        num_bullets=self._num_bullets)

  def get_instruction_args(self):
    return {"num_bullets": self._num_bullets}

  def get_instruction_args_keys(self):
    return ["num_bullets"]

  def check_following(self, value):
    """箇条書きリストの数が要件を満たしているかをチェックします"""
    bullet_lists = re.findall(r"^\s*\*[^\*].*$", value, flags=re.MULTILINE)
    bullet_lists_2 = re.findall(r"^\s*-.*$", value, flags=re.MULTILINE)
    num_bullet_lists = len(bullet_lists) + len(bullet_lists_2)
    return num_bullet_lists == self._num_bullets


class ConstrainedResponseCheckerEN(Instruction):
  """制約付き応答をチェックします（英語版）"""

  def build_description(self):
    """指示の説明を構築します"""
    self._constrained_responses = _CONSTRAINED_RESPONSE_OPTIONS_EN
    self._description_pattern = (
        "Answer with one of the following options: {response_options}")
    return self._description_pattern.format(
        response_options=self._constrained_responses)

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    return []

  def check_following(self, value):
    """応答が制約されたオプションと一致するかをチェックします"""
    value = value.strip()
    for constrained_response in self._constrained_responses:
      if constrained_response in value:
        return True
    return False


class ConstrainedStartCheckerEN(Instruction):
  """応答の開始をチェックします（英語版）"""

  def build_description(self, *, starter = None):
    """指示の説明を構築します"""
    self._starter = starter.strip() if isinstance(starter, str) else starter
    if self._starter is None:
      self._starter = random.choice(_STARTER_OPTIONS_EN)
    self._description_pattern = (
        "During the conversation, when it is your turn, " +
        "please always start with {starter}")
    return self._description_pattern.format(starter=self._starter)

  def get_instruction_args(self):
    return {"starter": self._starter}

  def get_instruction_args_keys(self):
    return ["starter"]

  def check_following(self, value):
    """応答が制約されたキーワードまたはフレーズで始まるかをチェックします"""
    response_pattern = r"^\s*" + self._starter + r".*$"
    response_with_constrained_start = re.search(response_pattern, value,
                                                flags=re.MULTILINE)
    return True if response_with_constrained_start else False


if __name__ == "__main__":
  test_japanese_constraints()
  print("\n")
  test_japanese_instructions()
