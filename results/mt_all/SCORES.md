# Translation scores

chrF++ (0 to 100, higher is better) with 95% bootstrap intervals, and BLEU.

## flores, Ewe, en>ewe

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 1012 | 37.4 (36.6 to 38.1) | 11.9 | 5.04 |
| nllb_600m | 1012 | 35.2 (34.3 to 36.0) | 11.4 | 4.55 |
| opus_mt | 1012 | 34.9 (34.2 to 35.6) | 9.7 | 0.33 |
| madlad_3b | 1012 | 24.6 (23.9 to 25.3) | 4.3 | 19.38 |

## flores, Ewe, ewe>en

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 1012 | 38.4 (37.6 to 39.3) | 16.3 | 3.39 |
| nllb_600m | 1012 | 35.8 (35.0 to 36.7) | 14.4 | 1.97 |
| madlad_3b | 1012 | 31.8 (31.0 to 32.6) | 10.3 | 7.03 |
| opus_mt | 1012 | 31.3 (30.7 to 32.0) | 8.8 | 0.33 |

## flores, Hausa, en>hau

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 1012 | 50.6 (49.7 to 51.6) | 25.4 | 4.47 |
| nllb_600m | 1012 | 48.7 (47.8 to 49.6) | 23.4 | 3.51 |
| madlad_3b | 1012 | 41.4 (40.5 to 42.3) | 15.3 | 9.51 |
| opus_mt | 1012 | 29.1 (28.5 to 29.7) | 7.2 | 0.32 |

## flores, Hausa, hau>en

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 1012 | 55.2 (54.2 to 56.2) | 33.8 | 3.20 |
| madlad_3b | 1012 | 53.2 (52.3 to 54.2) | 31.9 | 5.44 |
| nllb_600m | 1012 | 52.8 (51.9 to 53.7) | 31.0 | 1.78 |
| opus_mt | 1012 | 28.9 (28.3 to 29.4) | 6.7 | 0.44 |

## flores, Twi (Akan), en>twi

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| glossmt_nllb_1.3b | 1012 | 38.7 (38.1 to 39.3) | 12.8 | 4.35 |
| nllb_1.3b | 1012 | 37.4 (36.8 to 38.0) | 12.4 | 4.48 |
| nllb_600m | 1012 | 35.0 (34.4 to 35.7) | 11.1 | 3.29 |
| opus_mt | 1012 | 33.0 (32.5 to 33.6) | 9.0 | 0.31 |
| madlad_3b | 1012 | 18.0 (17.4 to 18.8) | 1.9 | 30.30 |

## flores, Twi (Akan), twi>en

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 1012 | 45.1 (44.2 to 46.1) | 23.4 | 5.21 |
| nllb_600m | 1012 | 42.9 (42.0 to 43.8) | 21.0 | 2.07 |
| madlad_3b | 1012 | 33.4 (32.6 to 34.2) | 11.9 | 7.05 |

## ghananlp, Ewe, en>ewe

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 500 | 55.3 (53.5 to 56.9) | 33.7 | 4.04 |
| nllb_600m | 500 | 51.0 (49.2 to 52.6) | 28.6 | 4.48 |
| opus_mt | 500 | 50.9 (49.0 to 52.5) | 28.7 | 0.26 |
| madlad_3b | 500 | 28.2 (27.0 to 29.5) | 7.2 | 12.64 |

## ghananlp, Ewe, ewe>en

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 500 | 46.4 (45.1 to 47.8) | 24.4 | 2.99 |
| nllb_600m | 500 | 43.8 (42.1 to 45.4) | 22.1 | 1.68 |
| opus_mt | 500 | 41.6 (40.2 to 42.9) | 18.7 | 0.22 |
| madlad_3b | 500 | 37.9 (36.6 to 39.2) | 16.9 | 5.09 |

## ghananlp, Ga, en>gaa

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| opus_mt | 500 | 53.3 (50.4 to 56.1) | 33.8 | 0.26 |

## ghananlp, Ga, gaa>en

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| opus_mt | 500 | 33.7 (32.4 to 35.0) | 13.5 | 0.28 |

## ghananlp, Twi (Akan), en>twi

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| glossmt_nllb_1.3b | 500 | 45.4 (43.9 to 47.1) | 22.1 | 2.50 |
| nllb_1.3b | 500 | 40.9 (39.6 to 42.2) | 17.9 | 3.55 |
| opus_mt | 500 | 38.7 (37.3 to 40.0) | 16.0 | 0.18 |
| nllb_600m | 500 | 38.1 (36.8 to 39.4) | 15.0 | 1.90 |
| madlad_3b | 500 | 16.0 (15.1 to 17.1) | 1.5 | 22.84 |

## ghananlp, Twi (Akan), twi>en

| Model | Sentences | chrF++ | BLEU | Seconds per sentence |
|---|---|---|---|---|
| nllb_1.3b | 500 | 43.5 (41.6 to 45.6) | 19.4 | 6.25 |
| nllb_600m | 500 | 40.4 (38.9 to 42.0) | 18.6 | 1.61 |
| madlad_3b | 500 | 25.6 (24.3 to 26.9) | 5.9 | 7.36 |
