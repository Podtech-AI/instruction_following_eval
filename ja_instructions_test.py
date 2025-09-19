# coding=utf-8
# Copyright 2025 The Google Research Authors.
#
# Apache License, Version 2.0 （以下「ライセンス」）の下でライセンスされています;
# このファイルはライセンスに従ってのみ使用することができます。

"""日本語指示チェッククラスのテストファイル"""

import unittest
from ja_instructions import (
    JapaneseHiraganaOnlyChecker,
    JapaneseKatakanaOnlyChecker,
    JapaneseBracketEmphasisFrequencyChecker,
    JapaneseNoToutenChecker,
    JapaneseStarFrequencyChecker,
    JapanesePostscriptChecker,
    JapaneseEndingPhraseChecker,
    JapaneseOnlyLanguageChecker,
    JapaneseLetterFrequencyChecker
)


class TestJapaneseHiraganaOnlyChecker(unittest.TestCase):
    """ひらがなが含まれているかチェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseHiraganaOnlyChecker("test_hiragana")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        description = self.checker.build_description()
        self.assertIn("ひらがな", description)
    
    def test_text_with_hiragana_passes(self):
        """ひらがなを含むテキストが通ることをテスト"""
        hiragana_text = "これはひらがなだけのぶんしょうです。"
        self.assertTrue(self.checker.check_following(hiragana_text))
        
        mixed_hiragana_text = "これはひらがなを含む文章です。"
        self.assertTrue(self.checker.check_following(mixed_hiragana_text))
    
    def test_text_without_hiragana_fails(self):
        """ひらがなを含まないテキストが失敗することをテスト"""
        katakana_only_text = "コレハカタカナダケデス。"
        self.assertFalse(self.checker.check_following(katakana_only_text))
        
        english_text = "This is English text."
        self.assertFalse(self.checker.check_following(english_text))
        
        kanji_only_text = "漢字文章。"
        self.assertFalse(self.checker.check_following(kanji_only_text))
    
    def test_hiragana_with_allowed_characters(self):
        """ひらがなと許可された文字の組み合わせをテスト"""
        text_with_numbers = "これは123ばんめのてすとです。"
        self.assertTrue(self.checker.check_following(text_with_numbers))
        
        text_with_symbols = "これは！？のぶんしょうです。"
        self.assertTrue(self.checker.check_following(text_with_symbols))


class TestJapaneseKatakanaOnlyChecker(unittest.TestCase):
    """カタカナが含まれているかチェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseKatakanaOnlyChecker("test_katakana")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        description = self.checker.build_description()
        self.assertIn("カタカナ", description)
    
    def test_text_with_katakana_passes(self):
        """カタカナを含むテキストが通ることをテスト"""
        katakana_text = "コレハカタカナダケノブンショウデス。"
        self.assertTrue(self.checker.check_following(katakana_text))
        
        mixed_katakana_text = "これはカタカナを含む文章です。"
        self.assertTrue(self.checker.check_following(mixed_katakana_text))
    
    def test_text_without_katakana_fails(self):
        """カタカナを含まないテキストが失敗することをテスト"""
        hiragana_only_text = "これはひらがなだけのぶんしょうです。"
        self.assertFalse(self.checker.check_following(hiragana_only_text))
        
        english_text = "This is English text."
        self.assertFalse(self.checker.check_following(english_text))
        
        kanji_only_text = "漢字文章。"
        self.assertFalse(self.checker.check_following(kanji_only_text))


class TestJapaneseBracketEmphasisFrequencyChecker(unittest.TestCase):
    """【】強調表現頻度チェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseBracketEmphasisFrequencyChecker("test_emphasis")
    
    def test_build_description_at_least(self):
        """以上関係の説明文構築をテスト"""
        description = self.checker.build_description(capital_relation="以上", capital_frequency=2)
        self.assertIn("【】", description)
        self.assertIn("2回以上", description)
    
    def test_build_description_less_than(self):
        """未満関係の説明文構築をテスト"""
        description = self.checker.build_description(capital_relation="未満", capital_frequency=3)
        self.assertIn("【】", description)
        self.assertIn("3回未満", description)
    
    def test_exactly_frequency_check(self):
        """正確な頻度チェックをテスト"""
        self.checker.build_description(capital_relation="正確に", capital_frequency=2)
        
        text_with_two_emphasis = "これは【重要】な【ポイント】です。"
        self.assertTrue(self.checker.check_following(text_with_two_emphasis))
        
        text_with_three_emphasis = "これは【重要】な【ポイント】で【確認】必要です。"
        self.assertFalse(self.checker.check_following(text_with_three_emphasis))
    
    def test_at_least_frequency_check(self):
        """以上頻度チェックをテスト"""
        self.checker.build_description(capital_relation="以上", capital_frequency=2)
        
        text_with_two_emphasis = "これは【重要】な【ポイント】です。"
        self.assertTrue(self.checker.check_following(text_with_two_emphasis))
        
        text_with_one_emphasis = "これは【重要】です。"
        self.assertFalse(self.checker.check_following(text_with_one_emphasis))


class TestJapaneseNoToutenChecker(unittest.TestCase):
    """読点禁止チェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseNoToutenChecker("test_no_touten")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        description = self.checker.build_description()
        self.assertIn("読点", description)
        self.assertIn("、", description)
    
    def test_no_touten_text_passes(self):
        """読点のないテキストが通ることをテスト"""
        no_touten_text = "これは読点のない文章です。"
        self.assertTrue(self.checker.check_following(no_touten_text))
    
    def test_with_touten_text_fails(self):
        """読点のあるテキストが失敗することをテスト"""
        with_touten_text = "これは、読点のある文章です。"
        self.assertFalse(self.checker.check_following(with_touten_text))


class TestJapaneseStarFrequencyChecker(unittest.TestCase):
    """星印頻度チェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseStarFrequencyChecker("test_star")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        description = self.checker.build_description(let_relation="以上", let_frequency=6, letter="★")
        self.assertIn("★", description)
        self.assertIn("6回以上", description)
    
    def test_sufficient_stars_passes(self):
        """十分な数の星印があるテキストが通ることをテスト"""
        self.checker.build_description(let_relation="以上", let_frequency=6, letter="★")
        
        text_with_stars = "これは★★★★★★の星印がある文章です。"
        self.assertTrue(self.checker.check_following(text_with_stars))
    
    def test_insufficient_stars_fails(self):
        """不十分な数の星印のテキストが失敗することをテスト"""
        self.checker.build_description(let_relation="以上", let_frequency=6, letter="★")
        
        text_with_few_stars = "これは★★★の星印がある文章です。"
        self.assertFalse(self.checker.check_following(text_with_few_stars))


class TestJapanesePostscriptChecker(unittest.TestCase):
    """日本語追記チェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapanesePostscriptChecker("test_postscript")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        description = self.checker.build_description(postscript_marker="追記")
        self.assertIn("追記", description)
    
    def test_with_postscript_passes(self):
        """追記のあるテキストが通ることをテスト"""
        self.checker.build_description(postscript_marker="追記")
        
        text_with_postscript = "本文です。\n追記 これは追記部分です。"
        self.assertTrue(self.checker.check_following(text_with_postscript))
    
    def test_without_postscript_fails(self):
        """追記のないテキストが失敗することをテスト"""
        self.checker.build_description(postscript_marker="追記")
        
        text_without_postscript = "これは追記のない文章です。"
        self.assertFalse(self.checker.check_following(text_without_postscript))
    
    def test_custom_postscript_marker(self):
        """カスタム追記マーカーのテスト"""
        self.checker.build_description(postscript_marker="注意")
        
        text_with_custom_marker = "本文です。\n注意 これは注意事項です。"
        self.assertTrue(self.checker.check_following(text_with_custom_marker))


class TestJapaneseEndingPhraseChecker(unittest.TestCase):
    """日本語終了フレーズチェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseEndingPhraseChecker("test_ending")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        phrase = "他にご不明な点はございますか？"
        description = self.checker.build_description(end_phrase=phrase)
        self.assertIn(phrase, description)
    
    def test_correct_ending_passes(self):
        """正しい終了フレーズのテキストが通ることをテスト"""
        phrase = "他にご不明な点はございますか？"
        self.checker.build_description(end_phrase=phrase)
        
        text_with_correct_ending = f"これは本文です。{phrase}"
        self.assertTrue(self.checker.check_following(text_with_correct_ending))
    
    def test_incorrect_ending_fails(self):
        """間違った終了フレーズのテキストが失敗することをテスト"""
        phrase = "他にご不明な点はございますか？"
        self.checker.build_description(end_phrase=phrase)
        
        text_with_wrong_ending = "これは本文です。ありがとうございました。"
        self.assertFalse(self.checker.check_following(text_with_wrong_ending))


class TestJapaneseOnlyLanguageChecker(unittest.TestCase):
    """日本語のみチェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseOnlyLanguageChecker("test_japanese_only")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        description = self.checker.build_description(language="ja")
        self.assertIn("日本語のみ", description)
    
    def test_japanese_only_text_passes(self):
        """日本語のみのテキストが通ることをテスト"""
        self.checker.build_description(language="ja")
        
        japanese_text = "これは日本語だけの文章です。"
        self.assertTrue(self.checker.check_following(japanese_text))
    
    def test_mixed_language_text_fails(self):
        """混合言語のテキストが失敗することをテスト"""
        self.checker.build_description(language="ja")
        
        mixed_text = "これはJapanese and English混合の文章です。"
        self.assertFalse(self.checker.check_following(mixed_text))
    
    def test_english_only_text_fails(self):
        """英語のみのテキストが失敗することをテスト"""
        self.checker.build_description(language="ja")
        
        english_text = "This is an English sentence."
        self.assertFalse(self.checker.check_following(english_text))


class TestJapaneseLetterFrequencyChecker(unittest.TestCase):
    """日本語文字頻度チェッカーのテスト"""
    
    def setUp(self):
        self.checker = JapaneseLetterFrequencyChecker("test_letter_freq")
    
    def test_build_description(self):
        """説明文の構築をテスト"""
        description = self.checker.build_description(let_relation="以上", let_frequency=3, letter="あ")
        self.assertIn("あ", description)
        self.assertIn("3回以上", description)
    
    def test_sufficient_letter_frequency_passes(self):
        """十分な文字頻度のテキストが通ることをテスト"""
        self.checker.build_description(let_relation="以上", let_frequency=3, letter="あ")
        
        text_with_letter = "あれはあそこにあります。"  # 「あ」が3回
        self.assertTrue(self.checker.check_following(text_with_letter))
    
    def test_insufficient_letter_frequency_fails(self):
        """不十分な文字頻度のテキストが失敗することをテスト"""
        self.checker.build_description(let_relation="以上", let_frequency=3, letter="あ")
        
        text_with_few_letters = "あれは場所です。"  # 「あ」が1回のみ
        self.assertFalse(self.checker.check_following(text_with_few_letters))
    
    def test_exactly_frequency_check(self):
        """正確な頻度チェックをテスト"""
        self.checker.build_description(let_relation="正確に", let_frequency=2, letter="と")
        
        text_with_exact_count = "これとそれとあれ"  # 「と」が2回
        self.assertTrue(self.checker.check_following(text_with_exact_count))
        
        text_with_wrong_count = "これとそれとあれとそれ"  # 「と」が3回
        self.assertFalse(self.checker.check_following(text_with_wrong_count))
    
    def test_less_than_frequency_check(self):
        """未満頻度チェックをテスト"""
        self.checker.build_description(let_relation="未満", let_frequency=2, letter="の")
        
        text_with_one_occurrence = "これの場所"  # 「の」が1回
        self.assertTrue(self.checker.check_following(text_with_one_occurrence))
        
        text_with_two_occurrences = "これの場所のもの"  # 「の」が2回
        self.assertFalse(self.checker.check_following(text_with_two_occurrences))


class TestIntegrationScenarios(unittest.TestCase):
    """統合シナリオのテスト"""
    
    def test_multiple_constraints_combination(self):
        """複数制約の組み合わせテスト"""
        # ひらがなのみ + 読点なし
        hiragana_checker = JapaneseHiraganaOnlyChecker("test1")
        touten_checker = JapaneseNoToutenChecker("test2")
        
        valid_text = "これはひらがなだけでとうてんのないぶんしょうです。"
        self.assertTrue(hiragana_checker.check_following(valid_text))
        self.assertTrue(touten_checker.check_following(valid_text))
        
        invalid_text = "これは、ひらがなだけですがとうてんがあります。"
        self.assertTrue(hiragana_checker.check_following(invalid_text))
        self.assertFalse(touten_checker.check_following(invalid_text))
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        # 空文字列
        hiragana_checker = JapaneseHiraganaOnlyChecker("test_empty")
        self.assertFalse(hiragana_checker.check_following(""))
        
        # 記号のみ
        self.assertFalse(hiragana_checker.check_following("！？。"))
        
        # 数字のみ
        self.assertFalse(hiragana_checker.check_following("123456"))


def run_all_tests():
    """すべてのテストを実行"""
    test_classes = [
        TestJapaneseHiraganaOnlyChecker,
        TestJapaneseKatakanaOnlyChecker,
        TestJapaneseBracketEmphasisFrequencyChecker,
        TestJapaneseNoToutenChecker,
        TestJapaneseStarFrequencyChecker,
        TestJapanesePostscriptChecker,
        TestJapaneseEndingPhraseChecker,
        TestJapaneseOnlyLanguageChecker,
        TestJapaneseLetterFrequencyChecker,
        TestIntegrationScenarios
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    print("=== 日本語指示チェッククラス テスト実行 ===")
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__} の実行:")
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        
        if result.failures:
            print(f"  失敗: {len(result.failures)}")
            for test, traceback in result.failures:
                print(f"    - {test}: {traceback}")
        
        if result.errors:
            print(f"  エラー: {len(result.errors)}")
            for test, traceback in result.errors:
                print(f"    - {test}: {traceback}")
    
    print(f"\n=== テスト結果サマリー ===")
    print(f"総テスト数: {total_tests}")
    print(f"成功: {total_tests - total_failures - total_errors}")
    print(f"失敗: {total_failures}")
    print(f"エラー: {total_errors}")
    print(f"成功率: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%")


if __name__ == "__main__":
    run_all_tests()