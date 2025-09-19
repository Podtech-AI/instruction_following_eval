# coding=utf-8
# Copyright 2025 The Google Research Authors.
#
# Apache License, Version 2.0（「ライセンス」）に基づいてライセンスされています。
# ライセンスに準拠する場合を除き、このファイルを使用することはできません。
# ライセンスのコピーは以下で入手できます：
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# 適用される法律で必要とされるか書面で合意されない限り、ソフトウェアは
# 「現状のまま」ライセンスの下で配布され、明示または黙示を問わず、
# いかなる種類の保証や条件もありません。
# ライセンスの下での権限と制限については、ライセンスを参照してください。

"""日本語対応指示ユーティリティライブラリのテスト"""

from absl.testing import absltest
from absl.testing import parameterized
import jp_instructions_util


class JapaneseInstructionsUtilTest(parameterized.TestCase):
    """日本語対応指示ユーティリティのテストクラス"""

    # 英語テストケース
    TEST_WORD_COUNT_CASE_EN_1 = ("word1, word2, word3, word4.", 4)
    TEST_WORD_COUNT_CASE_EN_2 = (
        "Bard can you tell me which is the best optimization method for the "
        "transition from an hydro-thermal system to an hydro-renewables system",
        24)
    TEST_WORD_COUNT_CASE_EN_3 = ("Hyphenated-word has two word counts.", 6)

    # 日本語テストケース
    TEST_WORD_COUNT_CASE_JA_1 = ("これは日本語のテストです。", 6)  # janome無しの場合は文字数
    TEST_WORD_COUNT_CASE_JA_2 = ("今日は良い天気ですね。", 7)  # janome無しの場合は文字数
    TEST_WORD_COUNT_CASE_JA_3 = ("私、は、元気、です。", 6)  # janome無しの場合は文字数（句読点除外）

    def test_word_count_english(self):
        """英語単語カウンターをテストする"""
        with self.subTest(f"{self.TEST_WORD_COUNT_CASE_EN_1[0]}"):
            text, expected_num_words = self.TEST_WORD_COUNT_CASE_EN_1
            actual_num_words = jp_instructions_util.count_words(text, lang='en')
            self.assertEqual(expected_num_words, actual_num_words)

        with self.subTest(f"{self.TEST_WORD_COUNT_CASE_EN_2[0]}"):
            text, expected_num_words = self.TEST_WORD_COUNT_CASE_EN_2
            actual_num_words = jp_instructions_util.count_words(text, lang='en')
            self.assertEqual(expected_num_words, actual_num_words)

        with self.subTest(f"{self.TEST_WORD_COUNT_CASE_EN_3[0]}"):
            text, expected_num_words = self.TEST_WORD_COUNT_CASE_EN_3
            actual_num_words = jp_instructions_util.count_words(text, lang='en')
            self.assertEqual(expected_num_words, actual_num_words)

    def test_word_count_japanese(self):
        """日本語単語カウンターをテストする（Sudachi形態素解析ベース）"""
        # Sudachi形態素解析による単語数テスト
        text = "こんにちは世界"
        word_count = jp_instructions_util.count_words(text, lang='ja')
        self.assertGreater(word_count, 0)
        self.assertEqual(word_count, 2)  # Sudachi単語数ベース
        
        # 句読点を含むテスト
        text_punct = "こんにちは、山田と言います。"
        word_count_punct = jp_instructions_util.count_words(text_punct, lang='ja')
        self.assertEqual(word_count_punct, 3)  # 単語数
        
        # 複雑な文のテスト
        complex_text = "こんにちは、世界！今日は、良い天気ですね。"
        complex_count = jp_instructions_util.count_words(complex_text, lang='ja')
        self.assertGreater(complex_count, 0)

    def test_word_count_auto_detect(self):
        """自動言語検出での単語カウンターをテストする"""
        # 英語テキスト
        text = "This is an English sentence."
        actual_num_words = jp_instructions_util.count_words(text)
        self.assertEqual(5, actual_num_words)
        
        # 日本語テキスト
        text = "これは日本語の文です。"
        actual_num_words = jp_instructions_util.count_words(text)
        self.assertGreater(actual_num_words, 0)

    @parameterized.named_parameters([
        {
            "testcase_name": f"_response={response}_num_sentences={num_sentences}",
            "response": response,
            "num_sentences": num_sentences,
        }
        for response, num_sentences in [
            ("xx,x. xx,x! xx/x. x{x}x? x.", 5),
            ("xx,x! xxxx. x(x)x?", 3),
            ("xxxx. xx,x! xx|x. x&x x?", 4),
            ("xx-x]xx,x! x{x}xx,x.", 2),
        ]
    ])
    def test_count_sentences_english(self, response, num_sentences):
        """英語文のカウンターをテストする"""
        actual_num_sentences = jp_instructions_util.count_sentences(response, lang='en')
        self.assertEqual(num_sentences, actual_num_sentences)

    @parameterized.named_parameters([
        {
            "testcase_name": f"_response={response}_num_sentences={num_sentences}",
            "response": response,
            "num_sentences": num_sentences,
        }
        for response, num_sentences in [
            ("こんにちは。元気ですか？私は元気です。", 3),
            ("今日は良い天気です！明日も晴れるでしょう。", 2),
            ("田中さんは言いました。「こんにちは」と。", 2),
            ("これは（テスト）です。本当です！", 2),
        ]
    ])
    def test_count_sentences_japanese(self, response, num_sentences):
        """日本語文のカウンターをテストする"""
        actual_num_sentences = jp_instructions_util.count_sentences(response, lang='ja')
        self.assertEqual(num_sentences, actual_num_sentences)

    def test_count_sentences_auto_detect(self):
        """自動言語検出での文カウンターをテストする"""
        # 英語テキスト
        text = "Hello world. How are you? I am fine."
        actual_num_sentences = jp_instructions_util.count_sentences(text)
        self.assertEqual(3, actual_num_sentences)
        
        # 日本語テキスト
        text = "こんにちは。元気ですか？私は元気です。"
        actual_num_sentences = jp_instructions_util.count_sentences(text)
        self.assertEqual(3, actual_num_sentences)

    # 英語文分割テスト
    TEST_SENTENCE_SPLIT_EN_1 = """
    Google is a technology company. It was founded in 1998 by Larry Page
    and Sergey Brin. Google's mission is to organize the world's information
    and make it universally accessible and useful.
    """

    TEST_SENTENCE_SPLIT_EN_2 = """
    The U.S.A has many Ph.D. students. They will often haven a .com website
    sharing the research that they have done.
    """

    EXPECTED_SENTENCE_SPLIT_EN_1 = [
        "Google is a technology company.",
        "It was founded in 1998 by Larry Page     and Sergey Brin.",
        "Google's mission is to organize the world's information     and make it universally accessible and useful.",
    ]

    EXPECTED_SENTENCE_SPLIT_EN_2 = [
        "The U.S.A has many Ph.D. students.",
        "They will often haven a .com website     sharing the research that they have done.",
    ]

    # 日本語文分割テスト
    TEST_SENTENCE_SPLIT_JA_1 = "これは日本語のテストです。元気ですか？私は元気です！"
    TEST_SENTENCE_SPLIT_JA_2 = "田中さんは「おはようございます」と言いました。私も挨拶しました。"
    
    EXPECTED_SENTENCE_SPLIT_JA_1 = [
        "これは日本語のテストです。",
        "元気ですか？",
        "私は元気です！"
    ]
    
    EXPECTED_SENTENCE_SPLIT_JA_2 = [
        "田中さんは「おはようございます」と言いました。",
        "私も挨拶しました。"
    ]

    def test_sentence_splitter_english(self):
        """英語文の分割器をテストする"""
        sentence_split_1 = jp_instructions_util.split_into_sentences(
            self.TEST_SENTENCE_SPLIT_EN_1, lang='en'
        )
        sentence_split_2 = jp_instructions_util.split_into_sentences(
            self.TEST_SENTENCE_SPLIT_EN_2, lang='en'
        )

        self.assertEqual(self.EXPECTED_SENTENCE_SPLIT_EN_1, sentence_split_1)
        self.assertEqual(self.EXPECTED_SENTENCE_SPLIT_EN_2, sentence_split_2)

    def test_sentence_splitter_japanese(self):
        """日本語文の分割器をテストする"""
        sentence_split_1 = jp_instructions_util.split_into_sentences(
            self.TEST_SENTENCE_SPLIT_JA_1, lang='ja'
        )
        sentence_split_2 = jp_instructions_util.split_into_sentences(
            self.TEST_SENTENCE_SPLIT_JA_2, lang='ja'
        )

        self.assertEqual(self.EXPECTED_SENTENCE_SPLIT_JA_1, sentence_split_1)
        self.assertEqual(self.EXPECTED_SENTENCE_SPLIT_JA_2, sentence_split_2)

    def test_sentence_splitter_auto_detect(self):
        """自動言語検出での文分割器をテストする"""
        # 英語テキスト（自動検出）
        sentences = jp_instructions_util.split_into_sentences("Hello. How are you?")
        self.assertEqual(["Hello.", "How are you?"], sentences)
        
        # 日本語テキスト（自動検出）
        sentences = jp_instructions_util.split_into_sentences("こんにちは。元気ですか？")
        self.assertEqual(["こんにちは。", "元気ですか？"], sentences)

    def test_generate_keywords_english(self):
        """英語キーワード生成機能をテストする"""
        keywords = jp_instructions_util.generate_keywords(10, lang='en')
        self.assertLen(keywords, 10)
        
        # すべて英語の単語リストに含まれることを確認
        for keyword in keywords:
            self.assertIn(keyword, jp_instructions_util.WORD_LIST)
        
        # 重複がないことを確認
        self.assertEqual(len(keywords), len(set(keywords)))

    def test_generate_keywords_japanese(self):
        """日本語キーワード生成機能をテストする"""
        keywords = jp_instructions_util.generate_keywords(5, lang='ja')
        self.assertLen(keywords, 5)
        
        # すべて日本語の単語リストに含まれることを確認
        for keyword in keywords:
            self.assertIn(keyword, jp_instructions_util.JAPANESE_WORD_LIST)
        
        # 重複がないことを確認
        self.assertEqual(len(keywords), len(set(keywords)))

    def test_generate_keywords_default_language(self):
        """デフォルト言語でのキーワード生成をテストする"""
        # デフォルトは英語
        keywords = jp_instructions_util.generate_keywords(3)
        self.assertLen(keywords, 3)
        for keyword in keywords:
            self.assertIn(keyword, jp_instructions_util.WORD_LIST)

    def test_language_detection(self):
        """言語検出機能をテストする"""
        # 日本語テキスト
        self.assertEqual(
            jp_instructions_util._detect_language("これは日本語です"), 'ja'
        )
        
        # 英語テキスト
        self.assertEqual(
            jp_instructions_util._detect_language("This is English"), 'en'
        )
        
        # 混合テキスト（日本語が含まれていれば'ja'）
        self.assertEqual(
            jp_instructions_util._detect_language("Hello これは混合です"), 'ja'
        )
        
        # 空文字列（デフォルトは英語）
        self.assertEqual(jp_instructions_util._detect_language(""), 'en')

    def test_error_handling(self):
        """エラーハンドリングをテストする"""
        # 日本語キーワード数の上限超過
        with self.assertRaises(ValueError):
            jp_instructions_util.generate_keywords(
                len(jp_instructions_util.JAPANESE_WORD_LIST) + 1, lang='ja'
            )
        
        # 英語キーワード数の上限超過
        with self.assertRaises(ValueError):
            jp_instructions_util.generate_keywords(
                len(jp_instructions_util.WORD_LIST) + 1, lang='en'
            )
        
        # 存在しない言語コードでのKeyError確認
        with self.assertRaises(KeyError):
            _ = jp_instructions_util.LANGUAGE_CODES['xx']

    def test_edge_cases(self):
        """エッジケースをテストする"""
        # 空文字列
        self.assertEqual(jp_instructions_util.split_into_sentences(""), [])
        self.assertEqual(jp_instructions_util.count_words(""), 0)
        self.assertEqual(jp_instructions_util.count_sentences(""), 0)
        
        # 句読点のみ（日本語）
        punct_only_ja = "。！？、"
        self.assertEqual(jp_instructions_util.count_words(punct_only_ja, lang='ja'), 0)
        
        # 句読点のみ（英語）
        punct_only_en = ".,!?"
        self.assertEqual(jp_instructions_util.count_words(punct_only_en, lang='en'), 0)
        
        # 数字のみは英語扱い
        self.assertEqual(jp_instructions_util._detect_language("123456"), 'en')

    def test_language_codes(self):
        """言語コード辞書をテストする"""
        self.assertIn('ja', jp_instructions_util.LANGUAGE_CODES)
        self.assertIn('en', jp_instructions_util.LANGUAGE_CODES)
        self.assertEqual(jp_instructions_util.LANGUAGE_CODES['ja'], 'Japanese')
        self.assertEqual(jp_instructions_util.LANGUAGE_CODES['en'], 'English')
        
        # 主要言語が含まれているか確認
        for lang in ['ja', 'en', 'fr', 'de']:
            self.assertIn(lang, jp_instructions_util.LANGUAGE_CODES)
        
        # 辞書のサイズ確認
        self.assertGreater(len(jp_instructions_util.LANGUAGE_CODES), 20)


    def test_complex_sentence_splitting(self):
        """複雑な文分割のテスト"""
        # 日本語複雑文分割
        ja_complex_text = "彼は「こんにちは」と言った。私は「元気です！」と答えた。それで終わり。"
        ja_result = jp_instructions_util.split_into_sentences(ja_complex_text, lang='ja')
        self.assertEqual(len(ja_result), 3)
        self.assertIn("彼は「こんにちは」と言った。", ja_result)
        
        # 英語複雑文分割
        en_complex_text = "Dr. Smith went to the U.S.A. He met Mr. Johnson there. They discussed Ph.D. requirements."
        en_result = jp_instructions_util.split_into_sentences(en_complex_text, lang='en')
        self.assertGreater(len(en_result), 2)
    
    def test_complex_sentence_counting(self):
        """複雑な文数カウントテスト"""
        # 日本語（引用符を含む）
        ja_complex = "彼は言った：「今日は良い天気だ。散歩に行こう！」そして外へ出た。"
        ja_count = jp_instructions_util.count_sentences(ja_complex, lang='ja')
        self.assertGreaterEqual(ja_count, 1)
        
        # 英語（略語を含む）
        en_complex = "Dr. Johnson said: 'Let's go to the U.S.A.!' Then we left."
        en_count = jp_instructions_util.count_sentences(en_complex, lang='en')
        self.assertGreater(en_count, 1)
    
    def test_keyword_generation_extended(self):
        """キーワード生成の拡張テスト"""
        # 日本語で多めの数を生成
        ja_keywords = jp_instructions_util.generate_keywords(10, lang='ja')
        self.assertEqual(len(ja_keywords), 10)
        self.assertEqual(len(ja_keywords), len(set(ja_keywords)))  # 重複なし
        
        # 英語で多めの数を生成
        en_keywords = jp_instructions_util.generate_keywords(15, lang='en')
        self.assertEqual(len(en_keywords), 15)
        self.assertEqual(len(en_keywords), len(set(en_keywords)))  # 重複なし
    
    def test_word_list_availability(self):
        """単語リストの利用可能性テスト"""
        # 英語単語リストの存在確認
        self.assertIsInstance(jp_instructions_util.WORD_LIST, list)
        self.assertGreater(len(jp_instructions_util.WORD_LIST), 100)
        
        # 日本語単語リストの存在確認
        self.assertIsInstance(jp_instructions_util.JAPANESE_WORD_LIST, list)
        self.assertGreater(len(jp_instructions_util.JAPANESE_WORD_LIST), 10)
        
        # 単語リストの重複チェック
        self.assertEqual(len(jp_instructions_util.WORD_LIST), len(set(jp_instructions_util.WORD_LIST)))
        self.assertEqual(len(jp_instructions_util.JAPANESE_WORD_LIST), len(set(jp_instructions_util.JAPANESE_WORD_LIST)))
    
    def test_word_counting_with_punctuation(self):
        """句読点を含む単語カウントテスト"""
        # 日本語
        ja_text_punct = "こんにちは、世界！今日は、良い天気ですね。"
        ja_count = jp_instructions_util.count_words(ja_text_punct, lang='ja')
        self.assertGreater(ja_count, 0)
        
        # 英語
        en_text_punct = "Hello, world! Today is a good day, isn't it?"
        en_count = jp_instructions_util.count_words(en_text_punct, lang='en')
        self.assertGreater(en_count, 5)


if __name__ == "__main__":
    print("=== 日本語対応ユーティリティテスト開始（absl版） ===")
    absltest.main()