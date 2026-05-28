## General Introduction

This file highlights some results we had thus far. 

## Surprisal VS MLU

If we do not control for length and compute the average surprisal by utterance, we get an inverse of MLU : as children get older, they produce longer and longer utterances more often, which result in less surprising utterances. This is because as context windows get larger, models are less and less surprised by tokens they see. 

This result is shown in this pair of figures (that date from a while ago) : 

- On the left, we see the average bits per word when we combine all utterances together
- On the right, we see the average number of words per utterances
- As we can see, in both case there is seemingly no time effect on the MLU nor the informativeness of caretakers
- However, there is seemlingly a clear time effect on the MLU and informativeness of children
- This pair of images highlights the importance of controling for size of utterances!

<table>
  <tr>
    <td align="center">
      <img src="figs_docs/bits_per_word__by_age_bin.png" alt="Average bits per word by age bin" width="100%">
    </td>
    <td align="center">
      <img src="figs_docs/mlu_w__by_age_bin.png" alt="Average words per utterance by age bin" width="100%">
    </td>
  </tr>
</table>

## Various LLMs

Then we compared various LLMs to find the least surprised by child-speech LLM.

The clear winner was Mistral 7B params, who was less surprised than any other model faced with utterances. The closest contender was a BabyLM model with 100M params.

Three things two note : 

1. Mistral performed better than simpler models that were trained on the CHILDES dataset
2. It was the biggest model tested : was it the least surprised simply because it was the largest? 
3. As the size of utterances increase, the gap between model widens

The color of the dots correspond to the model, brown for Mistral and blue for BabyLM 100M. 

On the X axis we have various size of utterances, on the Y axis the average surprisal per token.

The first image shows utterances with 1 to 8 morphemes, the second with 9 to 18 morphemes.

<p align="center">
  <img src="figs_docs/surprisal_vs_morph_count_filter_morph_count_1-8.png" alt="Surprisal by morph count across language models" width="85%">
</p>

<p align="center">
  <img src="figs_docs/surprisal_vs_morph_count_filter_morph_count_9-18.png" alt="Surprisal by morph count across language models" width="85%">
</p>



## Children VS Baselines

We also compared the informativeness of children's utterances with those of baseline models using the same vocabularies and the same length of utterances (without controlling for the number of syllables or the number of morphemes).

The following images show the average surprisal per token for utterances containing 1 to 8 morphemes, when accounting for an increasing size of context windows. 

The are in order of values of k, from 0 to 3. 

We can see how children are more reactive and better account for the context when producing utterances (as opposed to frequentist models that do not consider the context).

It will be interesting how this gap holds up once we generate utterances with LLM that can take into account a context window when generating utterances. We will have to decide on what we put in those context windows!

<p align="center">
  <img src="figs_docs/without.png" width="85%">
</p>

<p align="center">
  <img src="figs_docs/with_k1.png" alt="Surprisal by morph count across language models" width="85%">
</p>


<p align="center">
  <img src="figs_docs/with_k2.png" alt="Surprisal by morph count across language models" width="85%">
</p>

<p align="center">
  <img src="figs_docs/with_k3.png" alt="Surprisal by morph count across language models" width="85%">
</p>



## Children VS Caretakers

Finally, we also compared the informativeness of speech of children in relation to their caretakers. 

These figures show the effects of considering a context window of size 0 to 3 on the utterances' surprisal. 

Unlike the previous sets of figures, these are not comparing the same utterances (like when we compare children VS baselines).

It is interesting to note that as the size of the context window increases, utterances of length 4 to 8 get closer and closer in their average surprisal per token. 

These images also show that for very similar context, parents will produce less surprising speech. 

<p align="center">
  <img src="figs_docs/cvc_k0.png" width="85%">
</p>

<p align="center">
  <img src="figs_docs/cvc_k1.png" width="85%">
</p>

<p align="center">
  <img src="figs_docs/cvc_k2.png" width="85%">
</p>

<p align="center">
  <img src="figs_docs/cvc_k3.png" width="85%">
</p>