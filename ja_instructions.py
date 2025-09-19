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

"""日本語対応指示ライブラリ"""
import collections
import json
import random
import re
import string
from typing import Dict, Optional, Sequence, Union

import logging

import jp_instructions_util as instructions_util

_InstructionArgsDtype = Optional[Dict[str, Union[int, str, Sequence[str]]]]

_LANGUAGES = instructions_util.LANGUAGE_CODES if hasattr(instructions_util, 'LANGUAGE_CODES') else {
    "ja": "Japanese", "en": "English", "fr": "French", "de": "German", "es": "Spanish"
}

# 比較のための関係演算（日本語対応）
_COMPARISON_RELATION = ("未満", "以上")
_COMPARISON_RELATION_EN = ("less than", "at least")

# 文の最大数
_MAX_NUM_SENTENCES = 20

# プレースホルダーの数
_NUM_PLACEHOLDERS = 4

# 箇条書きリストの数
_NUM_BULLETS = 5

# 制約付き応答のオプション（日本語）
_CONSTRAINED_RESPONSE_OPTIONS = (
    "私の答えははいです。", "私の答えはいいえです。", "私の答えはたぶんです。")

# 開始キーワードのオプション（日本語）
_STARTER_OPTIONS = ("私が言うなら", "私の答えは", "私は信じます",
                    "私の意見では", "私は思います", "私は考えています", "私は感じます",
                    "私の観点から", "私が見る限り", "私によれば",
                    "私が関心を持つ限り", "私の理解では",
                    "私の見解では", "私の見解は", "私の認識では")

# 終了キーワードのオプション（日本語）
_ENDING_OPTIONS = ("他に質問はありますか？",
                   "他にお手伝いできることはありますか？")

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