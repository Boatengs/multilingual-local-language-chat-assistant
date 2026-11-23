# End to end, revised Twi, Ewe and Hausa questions

Questions: data/qa/questions_revised.csv, from the translation file Sam uploaded on 23 November 2026 (raw file: data/qa/raw/revised_2026-11-23.txt). Against the ChatGPT version, 14 Twi, 20 Ewe and 10 Hausa questions differ. The Ga column was identical to ChatGPT's, so Ga was not rerun.

Correct / incorrect / not attempted, out of 20.

| Sources | Twi | Ewe | Hausa |
|---|---|---|---|
| Wikipedia only | 7 / 3 / 10 | 8 / 4 / 8 | 9 / 2 / 9 |
| Plus official pages | 10 / 3 / 7 | 8 / 3 / 9 | 10 / 2 / 8 |
| Plus the pages the answers came from (leak) | 11 / 3 / 6 | 8 / 3 / 9 | 15 / 1 / 4 |

Same runs on the ChatGPT version, for comparison: Twi 11 / 12 / 16, Ewe 6 / 6 / 8, Hausa 7 / 9 / 14 correct.

Notes from comparing the two runs question by question (Wikipedia only):
- Twi wording with everyday local words is read worse by the Twi to English model: "Mantam ahe" became "How many provinces", "Ghana sidi baako" became "one Ghanaian coin".
- Ewe improved where the new wording fixed a mistranslation: government_2 now reads "How old does one have to be to vote in Ghana?" instead of a question about a child's allowance.
- Festival names are still misread in Ewe and Hausa (Homowo as "Gay Day" and "Homosexuality", Hogbetsotso as "Hogwarts"). Glossary protection on the input side is not built yet.
- Some grades changed even where the English reading was almost the same (Twi health_2, money_5). With 20 questions, a difference of two or three answers between runs is within this noise.
