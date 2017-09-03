import videoname_prettify as module
import unittest

class SimpleTest(unittest.TestCase):
  def test_file_without_extension_is_skipped(self):
    no_ext = "a.B_c-d (h264, 5.1ch, dj zee)"
    self.assertEqual(no_ext, module.prettify(no_ext))

  def test_extension_is_lowercased(self):
    self.assertEqual(".avi", module.prettify(".AVI"))

  def test_name_is_capitalized(self):
    self.assertEqual(
        "Kokotstina Je Napr Tohle.avi",
        module.prettify("kOkOtstInA jE nApr tOhlE.avi"))

  def test_word_delimiters_are_normalized(self):
    self.assertEqual("A Big Cabin.avi", module.prettify("A.Big.Cabin.avi"))

  def test_word_delimiters_are_normalized_and_whitespaces_squashed(self):
    self.assertEqual("Why This.avi", module.prettify("Why._.This.avi"))

  def test_s01e01_converted_to_01x01(self):
    self.assertEqual(
        "Prefix 01x01 Suffix.avi",
        module.prettify("Prefix s01e01 Suffix.avi"))

  def test_trailing_garbage_removed(self):
    self.assertEqual(
        "American Pie 2.mkv",
        module.prettify("American.Pie.2.720p.BRRip.750MB-Sinner.mkv"))


if __name__ == "__main__":
  unittest.main()

