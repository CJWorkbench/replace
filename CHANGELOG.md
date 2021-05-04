2021-05-04.01
-------------

* Fix crash on some category replacements.
* Change regex syntax to re2: https://github.com/google/re2/wiki/Syntax

(Internally, this is a rewrite using Arrow instead of Pandas.)

2020-06-22.01
-------------

* When `regex=False`, don't add backslashes before replacement spaces. (This
  was a regression in 2020-06-17.01.)

2020-06-17.01
-------------

* Test sub behavior: `replace("ABC", "([bB][cC])", r"\2 \1") == "AC B"`. (This
  previously was the case, but we never formally acknowledged it.)
* Report correct error when `replace_with` has an invalid escape sequence. (This
  used to crash the process.)
* When `regex=False`, don't use escape-sequence logic in `replace_with`.
  (Previously we did ... so a backslash would crash the process.)
