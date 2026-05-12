# TODO.md

Lower-level working checklist for this repository.

Use this file for concrete tasks. Keep `AGENTS.md` high-level and stable.
When a task is completed, move any useful result or decision into
`docs/notes.md`.

## How To Use This File

- Keep tasks small enough to review in one diff.
- Use checkboxes for work items.
- Put open questions near the task they block.
- Add commands that verify the task.
- Link to files when the task concerns a specific script or output.

## Current Focus

- TODO: Add a new option to the prepare_datasets.py that will output the cleaned utterances but only to csv files in cleaned_utterances. These will contain also the counts of words, morphemes and our various syllable strategies. It willalso contain all the erlvant info like the stuff in preprocesseddata (line_no, age, namne of child, session id, line id utt id etc etc)


## List of next possible focus

These are never to be implemented at the same time, always one at a time described in the previous section :


- TODO : Fix the utterance generation script and regenerate all the utterances
- TODO : Then, score again all the utterances making sure it preserved punctuation and that sentences without any scorable-words are ignored. 
- TODO: The generation of utterances using small LLM : it will be more detailed once it'll be the `Current Focus` but the general goal is that for every dataset from CHILDES we have,
- TODO: Increase in questions over time?
- TODO: Clarify the & markers 
- TODO: Compare with and without these
- TODO: Create a minimalist interface to easily study various utterances surprisals. It should either take a csv file with a clean utterance per row and return it with an added column with the scored surprisal for each cleaned utterance.


## Done Log

Use this for short notes after finishing tasks.

- TODO: YYYY-MM-DD - Finished X; verified with Y.

