# Project Motivation / Recent Email Context

Saved verbatim from the user-provided email context on 2026-06-16.

```text
Hi Nicolas, Eva,

It was good catching up just now. I did a quick literature research on the idea of communicative efficiency in child language. The most closely related study is this CogSci paper (2023) on "Communicative efficiency is present in young children and becomes more adult-like with age": [https://escholarship.org/uc/item/7mm0z6fk](https://escholarship.org/uc/item/7mm0z6fk)

Here, through experiments with 4-year olds, they showed that these children tended to be influenced by communicative efficiency in a task where they reduce utterance (or message) length when a short message is sufficient to convey meanings accurately.

Here's another paper from the same leading author suggesting there's communicative efficiency modulated behavior in production "Speakers use more redundant references with language learners: Evidence for communicatively-efficient referential choice": [https://www.sciencedirect.com/science/article/pii/S0749596X22000651](https://www.sciencedirect.com/science/article/pii/S0749596X22000651)

 In light of these findings, I think for our purpose we can test a similar idea except in naturalistic conversations, as opposed to controlled experimental settings. The idea is to assess whether children's natural language use is shaped by efficiency criteria, and if so, when does it start to emerge. the thing with CHILDES is that we can do analyses with children under 4, and track the progression over the developmental time line.

One simple analysis we could consider is as follows. At each developmental stage, e.g. 1 year, 1.5, 2, etc. We can develop a computational model to predict the utterance length of the child speaker; we could do the same prediction with adult speaker (as a comparison). In this model, we can incorporate explicit criteria related to efficiency, and see if such criteria actually help the model in inferring whether a child would produce a lengthy or short message. We can then plot model accuracy as a function of developmental stage, and observe when efficiency-based utterance length modulation starts to kick in through the development.

One efficiency criterion related to the CogSci paper above and also our analyses so far is "contextual predictability" or "contextual informativeness". If there is enough information in the (preceding) contexts say from parent's utterance, the child should just produce a short message and therefore minimizing effort in production. However, if there is not enough information in context, perhaps the child is more likely to produce a longer message. So in other words, contextual informativeness might predict utterance length of children, and we can test if this is true or not, for both children and adults.

There are other possible confounding criteria we can consider, for instance, one predictor is the utterance length of caretaker's preceding context, another predictor can be whether the preceding context is a statement vs question, and if a question, whether it's a what/why/how/binary question, which all could influence the length of child production; similarly, frequency of words and familiarity of topic in the preceding context also matters.

If we can show that contextual predictability and informativeness somehow best predicts child utterance length, despite controlling for various confounds, that might be something novel to report.

Let me know what you both think, and I'd be happy to chat more next Thursday when we meet. For now Nicolas, I think you may want to read the above two papers to get a clear sense of what's been done and found so far.

Just to relate the idea below to the current analysis; basically I see two ways that we can quantify communicative efficiency of child speech:

1) Given context, do children optimize informativeness in their speech with utterance length constrained? I think this is similar to surprisal(utterance|context) which Nicolas has been looking at so far.

2) Given context, do children optimize utterance length (or production effort) in their speech? I believe that this is not something we have looked into, but it complements the above question where we allow length to be a variable, and therefore, seek to predict when children shorten or lengthen utterances, and whether that modulation is "optimized' based on context. Specifically, I am guessing that for more contextually predictive scenarios, i.e. entropy or surprisal of (next word(s)|context) is low, children should tend to utter a short sentence compared to cases where that quantity is high. There's some related work here that uses LLM to estimate contextual predictability: [https://onlinelibrary.wiley.com/doi/epdf/10.1111/cogs.70202](https://onlinelibrary.wiley.com/doi/epdf/10.1111/cogs.70202)

If we can investigate both aspects, it seems a good package; and of course, it'd be a plus if we can examine how SES, gender, and clinical condition affect communicative efficiency in children.
```
