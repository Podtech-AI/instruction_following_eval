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

"""指示のライブラリ。"""
import collections
import json
import random
import re
import string
from typing import Dict, Optional, Sequence, Union

from absl import logging
import langdetect

import instructions_util


_InstructionArgsDtype = Optional[Dict[str, Union[int, str, Sequence[str]]]]

_LANGUAGES = instructions_util.LANGUAGE_CODES

# 比較のための関係演算。
_COMPARISON_RELATION = ("less than", "at least")

# 文の最大数。
_MAX_NUM_SENTENCES = 20

# プレースホルダーの数。
_NUM_PLACEHOLDERS = 4

# 箇条書きリストの数。
_NUM_BULLETS = 5

# 制約付き応答のオプション。
_CONSTRAINED_RESPONSE_OPTIONS = (
    "My answer is yes.", "My answer is no.", "My answer is maybe.")

# 開始キーワードのオプション。
_STARTER_OPTIONS = ("I would say", "My answer is", "I believe",
                    "In my opinion", "I think", "I reckon", "I feel",
                    "From my perspective", "As I see it", "According to me",
                    "As far as I'm concerned", "To my understanding",
                    "In my view", "My take on it is", "As per my perception")

# 終了キーワードのオプション。
# TODO(jeffreyzhou): より多くの終了オプションを追加する
_ENDING_OPTIONS = ("Any other questions?",
                   "Is there anything else I can help with?")

# ハイライトされたセクションの数。
_NUM_HIGHLIGHTED_SECTIONS = 4

# セクション分割子。
_SECTION_SPLITER = ("Section", "SECTION")

# セクションの数。
_NUM_SECTIONS = 5

# 段落の数。
_NUM_PARAGRAPHS = 5

# 追記マーカー。
_POSTSCRIPT_MARKER = ("P.S.", "P.P.S")

# キーワードの数。
_NUM_KEYWORDS = 2

# 単一キーワードの出現回数。
_KEYWORD_FREQUENCY = 3

# 単一文字の出現回数。
_LETTER_FREQUENCY = 10

# すべて大文字の単語の出現回数。
_ALL_CAPITAL_WORD_FREQUENCY = 20

# 応答内の単語数。
_NUM_WORDS_LOWER_LIMIT = 100
_NUM_WORDS_UPPER_LIMIT = 500


class Instruction:
  """指示テンプレート。"""

  def __init__(self, instruction_id):
    self.id = instruction_id

  def build_description(self, **kwargs):
    raise NotImplementedError("`build_description`は実装されていません。")

  def get_instruction_args(self):
    raise NotImplementedError("`get_instruction_args`は実装されていません。")

  def get_instruction_args_keys(self):
    raise NotImplementedError("`get_instruction_args_keys`は実装されていません。")

  def check_following(self, value):
    raise NotImplementedError("`check_following`は実装されていません。")


class ResponseLanguageChecker(Instruction):
  """応答全体の言語をチェックします。"""

  def build_description(self, *, language = None):
    """指示の説明を構築します。

    Args:
      language: 応答の期待される言語を表す文字列。
        言語は`langid.py` (https://pypi.org/project/langid/1.1.5/)で
        定義された97種類に準拠する必要があり、
        ISO 639-1コード (https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
        に従います。例：`en`（英語）、`zh`（中国語）、`fr`（フランス語）。

    Returns:
      指示の説明を表す文字列。
    """
    self._language = language
    if self._language is None:
      self._language = random.choice(list(_LANGUAGES.keys()))
        # TODO(tianjianlu): 説明の生成をより多くの選択肢に開放する。
    self._description_pattern = (
        "Your ENTIRE response should be in {language} language, no other " +
        "language is allowed.")
    return self._description_pattern.format(language=_LANGUAGES[self._language])

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"language": self._language}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["language"]

  def check_following(self, value):
    """応答全体の言語が指示に従っているかをチェックします。

    Args:
      value: 応答を表す文字列。

    Returns:
      `value`の言語が指示に従っている場合はTrue、そうでない場合はFalse。
    """
    assert isinstance(value, str)

    try:
      return langdetect.detect(value) == self._language
    except langdetect.LangDetectException as e:
      # 指示に従っていると見なす。
      logging.error(
          "Unable to detect language for text %s due to %s", value, e
      )  # refex: disable=pytotw.037
      return True


class NumberOfSentences(Instruction):
  """文の数をチェックします。"""

  def build_description(self, *, num_sentences = None,
                        relation = None):
    """指示の説明を構築します。

    Args:
      num_sentences: 閾値として文の数を指定する整数。
      relation: (`less than`, `at least`)のいずれかの文字列で、
        比較のための関係演算子を定義します。
        現在、2つの関係比較がサポートされています：
        'less than'の場合、実際の文数 < 閾値；
        'at least'の場合、実際の文数 >= 閾値。

    Returns:
      指示の説明を表す文字列。
    """
    # 比較のための閾値としての文の数。
    self._num_sentences_threshold = num_sentences
    if (self._num_sentences_threshold is None or
        self._num_sentences_threshold < 0):
      self._num_sentences_threshold = random.randint(1, _MAX_NUM_SENTENCES)

    if relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif relation not in _COMPARISON_RELATION:
      raise ValueError("The supported relation for comparison must be in "
                       f"{_COMPARISON_RELATION}, but {relation} is given.")
    else:
      self._comparison_relation = relation

    self._description_pattern = (
        "応答は{num_sentences}文{relation}である必要があります。")
    relation_jp = "より少ない" if self._comparison_relation == "less than" else "以上"
    return self._description_pattern.format(
        relation=relation_jp,
        num_sentences=self._num_sentences_threshold)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_sentences": self._num_sentences_threshold,
            "relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_sentences", "relation"]

  def check_following(self, value):
    """文の数が指示に従っているかをチェックします。

    Args:
      value: 応答を表す文字列。

    Returns:
      応答が指示に従っている場合はTrue。

    Raise:
        `instruction_args`の文字列が[`less_than`, `at_least`]に
        含まれていない場合はValueError。
    """
    num_sentences = instructions_util.count_sentences(value)
    if self._comparison_relation == _COMPARISON_RELATION[0]:
      return num_sentences < self._num_sentences_threshold
    elif self._comparison_relation == _COMPARISON_RELATION[1]:
      return num_sentences >= self._num_sentences_threshold  # pytype: disable=bad-return-type


class PlaceholderChecker(Instruction):
  """テンプレート作成におけるプレースホルダーをチェックします。"""

  def build_description(self, *, num_placeholders = None):
    """指示の説明を構築します。

    Args:
      num_placeholders: 応答に必要なプレースホルダーの
        最小数を示す整数。

    Returns:
      指示の説明を表す文字列。
    """
    self._num_placeholders = num_placeholders
    if self._num_placeholders is None or self._num_placeholders < 0:
      self._num_placeholders = random.randint(1, _NUM_PLACEHOLDERS)
    self._description_pattern = (
        "応答には[住所]のような角括弧で表された、少なくとも{num_placeholders}個のプレースホルダーが含まれている必要があります。")
    return self._description_pattern.format(
        num_placeholders=self._num_placeholders)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_placeholders": self._num_placeholders}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_placeholders"]

  def check_following(self, value):
    """プレースホルダーの数が指示に従っているかをチェックします。

    Args:
      value: 応答を表す文字列。

    Returns:
      応答内の実際のプレースホルダーの数が`num_placeholders`以上の
      場合はTrue、そうでない場合はFalse。
    """
    placeholders = re.findall(r"\[.*?\]", value)
    num_placeholders = len(placeholders)
    return num_placeholders >= self._num_placeholders


class BulletListChecker(Instruction):
  """プロンプト内の箇条書きリストをチェックします。"""

  def build_description(self, *, num_bullets = None):
    """指示の説明を構築します。

    Args:
      num_bullets: 応答に表示される必要がある箇条書きリストの
        正確な数を指定する整数。

    Returns:
      指示の説明を表す文字列。
    """
    self._num_bullets = num_bullets
    if self._num_bullets is None or self._num_bullets < 0:
      self._num_bullets = random.randint(1, _NUM_BULLETS)
    self._description_pattern = (
        "回答には正確に{num_bullets}個の箇条書きポイントが含まれている必要があります。" +
        "以下のようなマークダウン箇条書きを使用してください：\n" +
        "* これがポイント1です。\n" +
        "* これがポイント2です。")
    return self._description_pattern.format(
        num_bullets=self._num_bullets)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_bullets": self._num_bullets}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_bullets"]

  def check_following(self, value):
    r"""箇条書きリストの数が要件を満たしているかをチェックします。

    Args:
      value: 応答を表す文字列。応答には`\*`で始まる箇条書きリストが
        含まれていることが期待されます。

    Returns:
      応答内の実際の箇条書きリストの数が要件を満たしている場合はTrue。
    """
    bullet_lists = re.findall(r"^\s*\*[^\*].*$", value, flags=re.MULTILINE)
    bullet_lists_2 = re.findall(r"^\s*-.*$", value, flags=re.MULTILINE)
    num_bullet_lists = len(bullet_lists) + len(bullet_lists_2)
    return num_bullet_lists == self._num_bullets


class ConstrainedResponseChecker(Instruction):
  """制約付き応答をチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    # 期待される応答のオプションを表す文字列のシーケンス。
    self._constrained_responses = _CONSTRAINED_RESPONSE_OPTIONS
    self._description_pattern = (
        "Answer with one of the following options: {response_options}")
    return self._description_pattern.format(
        response_options=self._constrained_responses)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答が制約されたオプションと一致するかをチェックします。

    Args:
      value: 応答を表す文字列。

    Returns:
      実際の応答が制約された応答のオプションのいずれかを含む場合はTrue、
      そうでない場合はFalse。
    """
    value = value.strip()
    for constrained_response in self._constrained_responses:
      if constrained_response in value:
        return True
    return False


class ConstrainedStartChecker(Instruction):
  """応答の開始をチェックします。"""

  def build_description(self, *, starter = None):
    """指示の説明を構築します。

    Args:
      starter: 応答が始まるべきキーワードを表す文字列。

    Returns:
      指示の説明を表す文字列。
    """
    self._starter = starter.strip() if isinstance(starter, str) else starter
    if self._starter is None:
      self._starter = random.choice(_STARTER_OPTIONS)
    self._description_pattern = (
        "During the conversation, when it is your turn, " +
        "please always start with {starter}")
    return self._description_pattern.format(starter=self._starter)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"starter": self._starter}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["starter"]

  def check_following(self, value):
    """応答が制約されたキーワードまたはフレーズで始まるかをチェックします。

    Args:
      value: 応答を表す文字列。

    Returns:
      応答が`instruction_args`に含まれる指定されたフレーズまたは
      キーワードで始まる場合はTrue、そうでない場合はFalse。
    """
    response_pattern = r"^\s*" + self._starter + r".*$"
    response_with_constrained_start = re.search(response_pattern, value,
                                                flags=re.MULTILINE)
    return True if response_with_constrained_start else False


class HighlightSectionChecker(Instruction):
  """ハイライトされたセクションをチェックします。"""

  def build_description(self, *, num_highlights = None):
    """指示の説明を構築します。

    Args:
      num_highlights: ハイライトされたセクションの最小数を指定する整数。

    Returns:
      指示の説明を表す文字列。
    """
    self._num_highlights = num_highlights
    if self._num_highlights is None or self._num_highlights < 0:
      self._num_highlights = random.randint(1, _NUM_HIGHLIGHTED_SECTIONS)

    self._description_pattern = (
        "Highlight at least {num_highlights} sections in your answer with " +
        "markdown, i.e. *highlighted section*.")

    return self._description_pattern.format(num_highlights=self._num_highlights)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_highlights": self._num_highlights}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_highlights"]

  def check_following(self, value):
    """ハイライトされたセクションの数が要件を満たしているかをチェックします。

    Args:
      value: 応答を表す文字列。応答には*highlighted*の形式で
        ハイライトされたセクションが含まれていることが期待されます。

    Returns:
      *ハイライトされたセクション*の形式での実際のハイライトされた
      セクションの数が最小要件を満たしている場合はTrue、そうでない場合はFalse。
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


class SectionChecker(Instruction):
  """セクションをチェックします。"""

  def build_description(self, *, section_spliter = None,
                        num_sections = None):
    """指示の説明を構築します。

    Args:
      section_spliter: 新しいセクションをマークするセクション区切りキーワードを
        表す文字列。例：`Section`または`SECTION`。
      num_sections: セクションの数を指定する整数。

    Returns:
      指示の説明を表す文字列。
    """
    self._section_spliter = section_spliter.strip() if isinstance(
        section_spliter, str) else section_spliter
    if self._section_spliter is None:
      self._section_spliter = random.choice(_SECTION_SPLITER)

    self._num_sections = num_sections
    if self._num_sections is None or self._num_sections < 0:
      self._num_sections = random.randint(1, _NUM_SECTIONS)

    self._description_pattern = (
        "Your response must have {num_sections} sections. Mark the beginning " +
        "of each section with {section_spliter} X, such as:\n" +
        "{section_spliter} 1\n" +
        "[content of section 1]\n" +
        "{section_spliter} 2\n" +
        "[content of section 2]")

    return self._description_pattern.format(
        num_sections=self._num_sections,
        section_spliter=self._section_spliter)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"section_spliter": self._section_spliter,
            "num_sections": self._num_sections}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["section_spliter", "num_sections"]

  def check_following(self, value):
    """応答に複数のセクションが含まれているかをチェックします。

    Args:
      value: 応答を表す文字列。応答には複数のセクション（セクション数が
        1より大きい）が含まれていることが期待されます。新しいセクションは
        `Section 1`で始まり、数字はセクションインデックスを表します。

    Returns:
      応答内のセクション数が最小セクション数以上の場合はTrue、
      そうでない場合はFalse。
    """
    section_splitter_patten = r"\s?" + self._section_spliter  + r"\s?\d+\s?"
    sections = re.split(section_splitter_patten, value)
    num_sections = len(sections) - 1
    return num_sections >= self._num_sections


class ParagraphChecker(Instruction):
  """段落をチェックします。"""

  def build_description(self, *, num_paragraphs = None):
    """指示の説明を構築します。

    Args:
      num_paragraphs: 段落の数を指定する整数。

    Returns:
      指示の説明を表す文字列。
    """
    self._num_paragraphs = num_paragraphs
    if self._num_paragraphs is None or self._num_paragraphs < 0:
      self._num_paragraphs = random.randint(1, _NUM_PARAGRAPHS)

    self._description_pattern = (
        "There should be {num_paragraphs} paragraphs. " +
        "Paragraphs are separated with the markdown divider: ***")

    return self._description_pattern.format(num_paragraphs=self._num_paragraphs)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_paragraphs": self._num_paragraphs}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_paragraphs"]

  def check_following(self, value):
    """応答に必要な数の段落が含まれているかをチェックします。

    Args:
      value: 応答を表す文字列。応答にはマークダウン区切り文字`***`で
        区切られた段落が含まれている可能性があります。

    Returns:
      実際の段落数が必要数と同じ場合はTrue、そうでない場合はFalse。
    """
    paragraphs = re.split(r"\s?\*\*\*\s?", value)
    num_paragraphs = len(paragraphs)

    for index, paragraph in enumerate(paragraphs):
      if not paragraph.strip():
        if index == 0 or index == len(paragraphs) - 1:
          num_paragraphs -= 1
        else:
          return False

    return num_paragraphs == self._num_paragraphs


class PostscriptChecker(Instruction):
  """追伸をチェックします。"""

  def build_description(self, *, postscript_marker = None
                        ):
    """指示の説明を構築します。

    Args:
      postscript_marker: 追伸セクションの開始をマークするキーワードを
        含む文字列。

    Returns:
      指示の説明を表す文字列。
    """
    self._postscript_marker = postscript_marker.strip() if isinstance(
        postscript_marker, str) else postscript_marker
    if self._postscript_marker is None:
      self._postscript_marker = random.choice(_POSTSCRIPT_MARKER)

    self._description_pattern = (
        "At the end of your response, please explicitly add a postscript " +
        "starting with {postscript}")

    return self._description_pattern.format(postscript=self._postscript_marker)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"postscript_marker": self._postscript_marker}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["postscript_marker"]

  def check_following(self, value):
    """応答が追伸の形式に従っているかをチェックします。

    Args:
      value: 応答を表す文字列。応答には追伸セクションが含まれていることが
        期待されます。

    Returns:
      応答に`instruction_args`に含まれるキーワードで始まる追伸セクションが
      含まれている場合はTrue、そうでない場合はFalse。
    """
    value = value.lower()
    if self._postscript_marker == "P.P.S":
      postscript_pattern = r"\s*p\.\s?p\.\s?s.*$"
    elif self._postscript_marker == "P.S.":
      postscript_pattern = r"\s*p\.\s?s\..*$"
    else:
      postscript_pattern = r"\s*" + self._postscript_marker.lower() + r".*$"
    postscript = re.findall(postscript_pattern, value, flags=re.MULTILINE)
    return True if postscript else False


class RephraseChecker(Instruction):
  """言い換えをチェックします。"""

  def build_description(self, *, original_message):
    """指示の説明を構築します。

    Args:
      original_message: 元のメッセージを表す文字列。言い換えられた応答は、
        2つのアスタリスクの間の単語/文のみを変更する必要があります。
        例：*change me*。元のメッセージと言い換えられたメッセージの両方に
        *change me*の形式で変更が含まれている必要があります。

    Returns:
      指示の説明を表す文字列。
    """
    if not self.is_change(original_message):
      raise ValueError(f"Message {original_message} does not contain changes "
                       "in the form of *change me*.")

    self._reference_without_change = original_message
    self._description = ("Rephrasing: Your rephrased response should only" +
                         "change the words/sentences in between two asterisks" +
                         "such as *change me*.")
    return self._description

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"original_message": self._reference_without_change}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["original_message"]

  def check_following(self, value):
    r"""言い換えが指示に従っているかをチェックします。

    Args:
      value: `instruction_args`の文字列を言い換えることが期待される
        応答を表す文字列。

    Returns:
      `value`と`instruction_args`が*change me*のような2つのアスタリスクの間の
      単語/文のみで異なる場合はTrue、そうでない場合はFalse。
    """

    if not self.is_change(value):
      raise ValueError(f"value {value} does not contain "
                       "changes in the form of *change me*.")

    response_without_changes = self.strip_changes(value)
    reference_without_changes = self.strip_changes(
        self._reference_without_change)

    return response_without_changes == reference_without_changes

  def is_change(self, response):
    """応答に*change me*の形式の変更があるかをチェックします。"""
    return re.search(r"\*.*\*", response)

  def strip_changes(self, response):
    """変更を削除します。"""
    return re.sub(r"\*.*\*", "", response)


class KeywordChecker(Instruction):
  """特定のキーワードの存在をチェックします。"""

  def build_description(self, *, keywords = None
                        ):
    """指示の説明を構築します。

    Args:
      keywords: 応答に期待されるキーワードを表す文字列のシーケンス。

    Returns:
      指示の説明を表す文字列。
    """

    if not keywords:
      self._keywords = instructions_util.generate_keywords(
          num_keywords=_NUM_KEYWORDS)
    else:
      self._keywords = keywords
    self._keywords = sorted(self._keywords)

    self._description_pattern = ("回答にキーワード{keywords}を含めてください。")

    return self._description_pattern.format(keywords=self._keywords)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"keywords": self._keywords}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["keywords"]

  def check_following(self, value):
    """応答に期待されるキーワードが含まれているかをチェックします。"""
    for keyword in self._keywords:
      if not re.search(keyword, value, flags=re.IGNORECASE):
        return False
    return True


class KeywordFrequencyChecker(Instruction):
  """キーワードの頻度をチェックします。"""

  def build_description(self, *, keyword = None,
                        frequency = None,
                        relation = None):
    """指示の説明を構築します。

    Args:
      keyword: 応答に期待されるキーワードを表す文字列。
      frequency: `keyword`が応答に現れることが期待される回数を指定する整数。
      relation: (`less than`, `at least`)のいずれかの文字列で、
        比較のための関係演算子を定義します。
        現在、2つの関係比較がサポートされています：
        'less than'の場合、実際の出現回数 < frequency；
        'at least'の場合、実際の出現回数 >= frequency。

    Returns:
      指示の説明を表す文字列。
    """
    if not keyword:
      self._keyword = instructions_util.generate_keywords(num_keywords=1)[0]
    else:
      self._keyword = keyword.strip()

    self._frequency = frequency
    if self._frequency is None or self._frequency < 0:
      self._frequency = random.randint(1, _KEYWORD_FREQUENCY)

    if relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif relation not in _COMPARISON_RELATION:
      raise ValueError("The supported relation for comparison must be in "
                       f"{_COMPARISON_RELATION}, but {relation} is given.")
    else:
      self._comparison_relation = relation

    self._description_pattern = (
        "In your response, the word {keyword} should appear {relation} " +
        "{frequency} times.")

    return self._description_pattern.format(
        keyword=self._keyword,
        relation=self._comparison_relation,
        frequency=self._frequency)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"keyword": self._keyword,
            "frequency": self._frequency,
            "relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["keyword", "frequency", "relation"]

  def check_following(self, value):
    """応答に必要な頻度でキーワードが含まれているかをチェックします。"""
    actual_occurrences = len(re.findall(
        self._keyword, value, flags=re.IGNORECASE))

    if self._comparison_relation == _COMPARISON_RELATION[0]:
      return actual_occurrences < self._frequency
    elif self._comparison_relation == _COMPARISON_RELATION[1]:
      return actual_occurrences >= self._frequency  # pytype: disable=bad-return-type


class NumberOfWords(Instruction):
  """単語数をチェックします。"""

  def build_description(self, *, num_words = None,
                        relation = None):
    """指示の説明を構築します。

    Args:
      num_words: 応答に含まれる単語数を指定する整数。
      relation: (`less than`, `at least`)のいずれかの文字列で、
        比較のための関係演算子を定義します。
        現在、2つの関係比較がサポートされています：
        'less than'の場合、実際の単語数 < num_words；
        'at least'の場合、実際の単語数 >= num_words。

    Returns:
      指示の説明を表す文字列。
    """

    self._num_words = num_words
    if self._num_words is None or self._num_words < 0:
      self._num_words = random.randint(
          _NUM_WORDS_LOWER_LIMIT, _NUM_WORDS_UPPER_LIMIT
      )

    if relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif relation not in _COMPARISON_RELATION:
      raise ValueError("The supported relation for comparison must be in "
                       f"{_COMPARISON_RELATION}, but {relation} is given.")
    else:
      self._comparison_relation = relation

    self._description_pattern = (
        "Answer with {relation} {num_words} words.")

    return self._description_pattern.format(
        relation=self._comparison_relation,
        num_words=self._num_words)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_words": self._num_words,
            "relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_words", "relation"]

  def check_following(self, value):
    """応答に期待される単語数が含まれているかをチェックします。"""
    num_words = instructions_util.count_words(value)

    if self._comparison_relation == _COMPARISON_RELATION[0]:
      return num_words < self._num_words
    elif self._comparison_relation == _COMPARISON_RELATION[1]:
      return num_words >= self._num_words  # pytype: disable=bad-return-type


class JsonFormat(Instruction):
  """JSON形式をチェックします。"""

  def build_description(self):
    self._description_pattern = (
        "Entire output should be wrapped in JSON format. You can use markdown"
        " ticks such as ```."
    )
    return self._description_pattern

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
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


class ParagraphFirstWordCheck(Instruction):
  """段落とn番目の段落の最初の単語をチェックします。"""

  def build_description(self, num_paragraphs = None,
                        nth_paragraph = None,
                        first_word = None):
    r"""指示の説明を構築します。

    Args:
      num_paragraphs: 応答に期待される段落の数を示す整数。
        段落は'\n\n'で区切られることが期待される文字列のサブセットです。
      nth_paragraph: 確認する段落番号を示す整数。
        nは1から始まることに注意してください。
      first_word: n番目の段落の最初の単語を表す文字列。

    Returns:
      指示の説明を表す文字列。
    """
    self._num_paragraphs = num_paragraphs
    if self._num_paragraphs is None or self._num_paragraphs < 0:
      self._num_paragraphs = random.randint(1, _NUM_PARAGRAPHS)

    self._nth_paragraph = nth_paragraph
    if (
        self._nth_paragraph is None
        or self._nth_paragraph <= 0
        or self._nth_paragraph > self._num_paragraphs
    ):
      self._nth_paragraph = random.randint(1, self._num_paragraphs + 1)

    self._first_word = first_word
    if self._first_word is None:
      self._first_word = instructions_util.generate_keywords(num_keywords=1)[0]
    self._first_word = self._first_word.lower()

    self._description_pattern = (
        "There should be {num_paragraphs} paragraphs. " +
        "Paragraphs and only paragraphs are separated with each other by two " +
        "new lines as if it was '\\n\\n' in python. " +
        "Paragraph {nth_paragraph} must start with word {first_word}.")

    return self._description_pattern.format(
        num_paragraphs=self._num_paragraphs,
        nth_paragraph=self._nth_paragraph,
        first_word=self._first_word)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_paragraphs": self._num_paragraphs,
            "nth_paragraph": self._nth_paragraph,
            "first_word": self._first_word}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_paragraphs", "nth_paragraph", "first_word"]

  def check_following(self, value):
    """必要な段落数と正しい最初の単語をチェックします。

    Args:
      value: 応答を表す文字列。応答には2つの改行で区切られた段落が
        含まれ、n番目の段落の最初の単語は指定された単語と
        一致する必要があります。

    Returns:
      段落数が必要数と同じで、指定された段落の最初の単語が
      必要なものと同じ場合はTrue。そうでない場合はFalse。
    """

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

    first_word = ""
    punctuation = {".", ",", "?", "!", "'", '"'}

    # 最初の単語を取得し、句読点を削除
    word = paragraph.split()[0].strip()
    # TODO(jeffrey): もっと複雑にする？
    word = word.lstrip("'")
    word = word.lstrip('"')

    for letter in word:
      if letter in punctuation:
        break
      first_word += letter.lower()

    return (
        num_paragraphs == self._num_paragraphs
        and first_word == self._first_word
    )


# TODO(jeffrey) 関係を追加 - at least/at most?
class KeySentenceChecker(Instruction):
  """特定のキーセンテンスの存在をチェックします。"""

  def build_description(self, key_sentences = None,
                        num_sentences = None):
    """指示の説明を構築します。

    Args:
      key_sentences: 応答に期待されるキーセンテンスを表す文字列のシーケンス。
      num_sentences: 応答に含まれることが期待されるキーセンテンスの数。

    Returns:
      指示の説明を表す文字列。
    """

    if not key_sentences:
      # TODO(jeffrey) 文生成関数を作る？wonderwordsパッケージ
      self._key_sentences = set(["For now, this is fine."])
    else:
      self._key_sentences = key_sentences

    if not num_sentences:
      self._num_sentences = random.randint(1, len(self._key_sentences))
    else:
      self._num_sentences = num_sentences

    self._description_pattern = (
        "Include {num_sentences} of the following sentences {key_sentences}"
    )

    return self._description_pattern.format(
        num_sentences=self._num_sentences, key_sentences=self._key_sentences
    )

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"num_sentences": self._num_sentences,
            "key_sentences": list(self._key_sentences)}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["num_sentences", "key_sentences"]

  def check_following(self, value):
    """応答に期待されるキーセンテンスが含まれているかをチェックします。"""
    count = 0
    sentences = instructions_util.split_into_sentences(value)
    for sentence in self._key_sentences:
      if sentence in sentences:
        count += 1

    return count == self._num_sentences


class ForbiddenWords(Instruction):
  """指定された単語が応答に使われていないかをチェックします。"""

  def build_description(self, forbidden_words = None
                        ):
    """指示の説明を構築します。

    Args:
      forbidden_words: 応答で使用が許可されない単語を表す文字列のシーケンス。

    Returns:
      指示の説明を表す文字列。
    """

    if not forbidden_words:
      self._forbidden_words = instructions_util.generate_keywords(
          num_keywords=_NUM_KEYWORDS)
    else:
      self._forbidden_words = list(set(forbidden_words))
    self._forbidden_words = sorted(self._forbidden_words)
    self._description_pattern = (
        "Do not include keywords {forbidden_words} in the response."
    )

    return self._description_pattern.format(
        forbidden_words=self._forbidden_words
    )

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"forbidden_words": self._forbidden_words}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["forbidden_words"]

  def check_following(self, value):
    """応答に期待されるキーワードが含まれていないかをチェックします。"""
    for word in self._forbidden_words:
      if re.search(r"\b" + word + r"\b", value, flags=re.IGNORECASE):
        return False
    return True


class RephraseParagraph(Instruction):
  """段落が言い換えられているかをチェックします。"""

  def build_description(self, *, original_paragraph, low, high
                        ):
    """指示の説明を構築します。

    Args:
      original_paragraph: 元の段落を表す文字列。言い換えられた応答は
        low-highの範囲の単語を共通して持つ必要があります。
      low: 類似する単語の下限を示す整数。
      high: 類似する単語の上限を表す整数。

    Returns:
      指示の説明を表す文字列。
    """
    # TODO(jeffrey) より包括的にする
    self._original_paragraph = original_paragraph
    self._low = low
    self._high = high

    self._description = ("Rephrase the following paragraph: " +
                         "{original_paragraph}\nYour response should have " +
                         "between {low} and {high} of the same words. " +
                         "Words are the same if and only if all of the " +
                         "letters, ignoring cases, are the same. For " +
                         "example, 'run' is the same as 'Run' but different " +
                         "to 'ran'.")

    return self._description.format(original_paragraph=original_paragraph,
                                    low=self._low, high=self._high)

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"original_paragraph": self._original_paragraph,
            "low": self._low,
            "high": self._high}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
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
  """2つの応答が与えられているかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "Give two different responses. Responses and only responses should"
        " be separated by 6 asterisk symbols: ******."
    )
    return self._description_pattern

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答に2つの異なる回答があるかをチェックします。

    Args:
      value: 応答を表す文字列。

    Returns:
      2つの応答が検出された場合はTrue、そうでない場合はFalse。
    """
    valid_responses = list()
    responses = value.split("******")
    for index, response in enumerate(responses):
      if not response.strip():
        if index != 0 and index != len(responses) - 1:
          return False
      else:
        valid_responses.append(response)
    return (
        len(valid_responses) == 2
        and valid_responses[0].strip() != valid_responses[1].strip()
    )


class RepeatPromptThenAnswer(Instruction):
  """プロンプトが最初に繰り返され、その後回答されるかをチェックします。"""

  def build_description(self, *, prompt_to_repeat = None):
    """指示の説明を構築します。

    Args:
      prompt_to_repeat: 繰り返されるべきプロンプト。

    Returns:
      指示の説明を表す文字列。
    """
    if not prompt_to_repeat:
      raise ValueError("prompt_to_repeat must be set.")
    else:
      self._prompt_to_repeat = prompt_to_repeat
    self._description_pattern = (
        "First repeat the request word for word without change,"
        " then give your answer (1. do not say any words or characters"
        " before repeating the request; 2. the request you need to repeat"
        " does not include this sentence)"
    )
    return self._description_pattern

  def get_instruction_args(self):
    return {"prompt_to_repeat": self._prompt_to_repeat}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["prompt_to_repeat"]

  def check_following(self, value):
    if value.strip().lower().startswith(self._prompt_to_repeat.strip().lower()):
      return True
    return False


class EndChecker(Instruction):
  """プロンプトが指定されたフレーズで終わるかをチェックします。"""

  def build_description(self, *, end_phrase = None):
    """指示の説明を構築します。

    Args:
      end_phrase: 応答が終わるべきフレーズを表す文字列。

    Returns:
      指示の説明を表す文字列。
    """
    self._end_phrase = (
        end_phrase.strip() if isinstance(end_phrase, str) else end_phrase
    )
    if self._end_phrase is None:
      self._end_phrase = random.choice(_ENDING_OPTIONS)
    self._description_pattern = (
        "Finish your response with this exact phrase {ender}. "
        "No other words should follow this phrase.")
    return self._description_pattern.format(ender=self._end_phrase)

  def get_instruction_args(self):
    return {"end_phrase": self._end_phrase}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["end_phrase"]

  def check_following(self, value):
    """応答が期待されるフレーズで終わるかをチェックします。"""
    value = value.strip().strip("\"").lower()
    self._end_phrase = self._end_phrase.strip().lower()
    return value.endswith(self._end_phrase)


class TitleChecker(Instruction):
  """応答にタイトルがあるかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "Your answer must contain a title, wrapped in double angular brackets,"
        " such as <<poem of joy>>."
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答にタイトルが含まれているかをチェックします。"""
    pattern = r"<<[^\n]+>>"
    re_pattern = re.compile(pattern)
    titles = re.findall(re_pattern, value)

    for title in titles:
      if title.lstrip("<").rstrip(">").strip():
        return True
    return False


class LetterFrequencyChecker(Instruction):
  """文字の頻度をチェックします。"""

  def build_description(self, *, letter = None,
                        let_frequency = None,
                        let_relation = None):
    """指示の説明を構築します。

    Args:
      letter: 応答に期待される文字を表す文字列。
      let_frequency: `keyword`が応答に現れることが期待される回数を指定する整数。
      let_relation: (`less than`, `at least`)のいずれかの文字列で、
        比較のための関係演算子を定義します。現在、2つの関係比較が
        サポートされています。'less than'の場合、実際の出現回数 < frequency；
        'at least'の場合、実際の出現回数 >= frequency。

    Returns:
      指示の説明を表す文字列。
    """
    if (
        not letter
        or len(letter) > 1
        or ord(letter.lower()) < 97
        or ord(letter.lower()) > 122
    ):
      self._letter = random.choice(list(string.ascii_letters))
    else:
      self._letter = letter.strip()
    self._letter = self._letter.lower()

    self._frequency = let_frequency
    if self._frequency is None or self._frequency < 0:
      self._frequency = random.randint(1, _LETTER_FREQUENCY)

    if let_relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif let_relation not in _COMPARISON_RELATION:
      raise ValueError(
          "The supported relation for comparison must be in "
          f"{_COMPARISON_RELATION}, but {let_relation} is given."
      )
    else:
      self._comparison_relation = let_relation

    self._description_pattern = (
        "In your response, the letter {letter} should appear {let_relation}"
        " {let_frequency} times."
    )

    return self._description_pattern.format(
        letter=self._letter,
        let_frequency=self._frequency,
        let_relation=self._comparison_relation,
    )

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {"letter": self._letter,
            "let_frequency": self._frequency,
            "let_relation": self._comparison_relation}

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["letter", "let_frequency", "let_relation"]

  def check_following(self, value):
    """応答に文字が正しい頻度で含まれているかをチェックします。"""
    value = value.lower()
    letters = collections.Counter(value)

    if self._comparison_relation == _COMPARISON_RELATION[0]:
      return letters[self._letter] < self._frequency
    else:
      return letters[self._letter] >= self._frequency


class CapitalLettersEnglishChecker(Instruction):
  """応答が英語で、すべて大文字であるかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "Your entire response should be in English, and in all capital letters."
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答が英語で、すべて大文字であるかをチェックします。"""
    assert isinstance(value, str)

    try:
      return value.isupper() and langdetect.detect(value) == "en"
    except langdetect.LangDetectException as e:
      # 指示に従っていると見なす。
      logging.error(
          "Unable to detect language for text %s due to %s", value, e
      )  # refex: disable=pytotw.037
      return True


class LowercaseLettersEnglishChecker(Instruction):
  """応答が英語で、すべて小文字であるかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "Your entire response should be in English, and in all lowercase"
        " letters. No capital letters are allowed."
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答が英語で、すべて小文字であるかをチェックします。"""
    assert isinstance(value, str)

    try:
      return value.islower() and langdetect.detect(value) == "en"
    except langdetect.LangDetectException as e:
      # 指示に従っていると見なす。
      logging.error(
          "Unable to detect language for text %s due to %s", value, e
      )  # refex: disable=pytotw.037
      return True


class CommaChecker(Instruction):
  """応答にコンマが含まれていないかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "In your entire response, refrain from the use of any commas."
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答にコンマが含まれていないかをチェックします。"""
    return not re.search(r"\,", value)


class CapitalWordFrequencyChecker(Instruction):
  """すべて大文字の単語の頻度をチェックします。"""

  def build_description(
      self,
      capital_frequency = None,
      capital_relation = None,
  ):
    """指示の説明を構築します。

    Args:
      capital_frequency: すべて大文字であるべき単語の数を表す整数。
      capital_relation: 頻度に関して'at least'または'at most'のいずれかの文字列。

    Returns:
      指示の説明を表す文字列。
    """
    self._frequency = capital_frequency
    if self._frequency is None:
      self._frequency = random.randint(1, _ALL_CAPITAL_WORD_FREQUENCY)

    self._comparison_relation = capital_relation
    if capital_relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif capital_relation not in _COMPARISON_RELATION:
      raise ValueError(
          "The supported relation for comparison must be in "
          f"{_COMPARISON_RELATION}, but {capital_relation} is given."
      )

    self._description_pattern = (
        "In your response, words with all capital letters should appear"
        " {relation} {frequency} times."
    )

    return self._description_pattern.format(
        frequency=self._frequency, relation=self._comparison_relation
    )

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {
        "capital_frequency": self._frequency,
        "capital_relation": self._comparison_relation,
    }

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["capital_frequency", "capital_relation"]

  def check_following(self, value):
    """すべて大文字の単語の頻度をチェックします。"""
    # ハイフンでつながれた単語は1つの単語としてカウントされます
    words = instructions_util.nltk.word_tokenize(value)
    capital_words = [word for word in words if word.isupper()]

    capital_words = len(capital_words)

    if self._comparison_relation == _COMPARISON_RELATION[0]:
      return capital_words < self._frequency
    else:
      return capital_words >= self._frequency


class QuotationChecker(Instruction):
  """応答が二重引用符で囲まれているかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "Wrap your entire response with double quotation marks."
    )
    return self._description_pattern

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答が二重引用符で囲まれているかをチェックします。"""
    value = value.strip()
    return len(value) > 1 and value[0] == '"' and value[-1] == '"'


class JapaneseHiraganaChecker(Instruction):
  """応答がすべてひらがなで書かれているかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "回答はすべてひらがなで書いてください。漢字やカタカナは使用できません。"
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答がすべてひらがなで書かれているかをチェックします。"""
    assert isinstance(value, str)
    
    # 記号、数字、英字、空白を除去
    import re
    japanese_text = re.sub(r'[^\u3041-\u3096\u30FC\u3000\s\n。、！？]', '', value)
    
    # 残った文字がすべてひらがなかどうかチェック
    for char in japanese_text:
      if char not in ' \n\t\u3000。、！？' and not ('\u3041' <= char <= '\u3096'):
        return False
    return True


class JapaneseCasualChecker(Instruction):
  """応答が敬語を使わずカジュアルな日本語で書かれているかをチェックします。"""

  def build_description(self):
    """指示の説明を構築します。"""
    self._description_pattern = (
        "回答は敬語を使わず、カジュアルな日本語で書いてください。"
    )
    return self._description_pattern

  def get_instruction_args(self):
    return None

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return []

  def check_following(self, value):
    """応答が敬語を使わずカジュアルな日本語で書かれているかをチェックします。"""
    assert isinstance(value, str)
    
    # 敬語の典型的なパターンをチェック
    keigo_patterns = [
        r'です(?![^\u3040-\u309F])',  # 「です」
        r'ます(?![^\u3040-\u309F])',  # 「ます」
        r'である(?![^\u3040-\u309F])', # 「である」
        r'ございます',                # 「ございます」
        r'いらっしゃ',               # 「いらっしゃる」系
        r'お.*になる',               # 「お〜になる」
        r'させていただ',             # 「させていただく」系
    ]
    
    import re
    for pattern in keigo_patterns:
      if re.search(pattern, value):
        return False
    return True


class KatakanaWordFrequencyChecker(Instruction):
  """すべてカタカナの単語の頻度をチェックします。"""

  def build_description(
      self,
      capital_frequency = None,
      capital_relation = None,
  ):
    """指示の説明を構築します。

    Args:
      capital_frequency: すべてカタカナであるべき単語の数を表す整数。
      capital_relation: 頻度に関して'at least'または'less than'のいずれかの文字列。

    Returns:
      指示の説明を表す文字列。
    """
    self._frequency = capital_frequency
    if self._frequency is None:
      self._frequency = random.randint(1, 10)

    self._comparison_relation = capital_relation
    if capital_relation is None:
      self._comparison_relation = random.choice(_COMPARISON_RELATION)
    elif capital_relation not in _COMPARISON_RELATION:
      raise ValueError(
          "The supported relation for comparison must be in "
          f"{_COMPARISON_RELATION}, but {capital_relation} is given."
      )

    self._description_pattern = (
        "回答では、すべてカタカナの単語が{relation} {frequency}回現れる必要があります。"
    )

    return self._description_pattern.format(
        frequency=self._frequency, relation=self._comparison_relation
    )

  def get_instruction_args(self):
    """`build_description`のキーワード引数を返します。"""
    return {
        "capital_frequency": self._frequency,
        "capital_relation": self._comparison_relation,
    }

  def get_instruction_args_keys(self):
    """`build_description`の引数キーを返します。"""
    return ["capital_frequency", "capital_relation"]

  def check_following(self, value):
    """すべてカタカナの単語の頻度をチェックします。"""
    import re
    # カタカナのみで構成された単語を抽出
    katakana_words = re.findall(r'[\u30A1-\u30F6]+', value)
    katakana_count = len(katakana_words)

    if self._comparison_relation == _COMPARISON_RELATION[0]:  # less than
      return katakana_count < self._frequency
    else:  # at least
      return katakana_count >= self._frequency
