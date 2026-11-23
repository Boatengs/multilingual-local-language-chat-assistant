# End to end, ChatGPT translated questions

Questions: data/qa/questions_gpt.csv. The 20 English questions in data/qa/questions_en.csv were translated by ChatGPT (chatgpt.com, logged out, 23 November 2026). The raw reply is in data/qa/raw/chatgpt_2026-11-23.txt. No native speaker has checked these translations yet.

Correct / incorrect / not attempted, out of 20. Judge: Qwen2.5 14B with the SimpleQA grader.

| Sources | Twi | Ewe | Ga | Hausa |
|---|---|---|---|---|
| Wikipedia only | 11 / 3 / 6 | 6 / 8 / 6 | 0 / 1 / 19 | 7 / 2 / 11 |
| Plus official pages | 12 / 3 / 5 | 6 / 6 / 8 | 0 / 1 / 19 | 9 / 1 / 10 |
| Plus the pages the answers came from (leak) | 16 / 2 / 2 | 8 / 6 / 6 | 0 / 1 / 19 | 14 / 1 / 5 |

English on the same questions, Wikipedia only: 11 / 3 / 6.

How the assistant read some questions (Wikipedia only run):

| Question | Twi read as | Ga read as |
|---|---|---|
| health_1 | In what year did Ghana enact its National Health Insurance Act? | Ghana's National Health Iyi? |
| government_1 | How many regions does Ghana have? | WHAT do we look like? |
| money_3 | How many pesos is one Ghanaian cedi? | Pesewas, who has come to Ghana ceds? |
| culture_1 | Who celebrates Halloween? | Who would not have been greater than Homoils? |
