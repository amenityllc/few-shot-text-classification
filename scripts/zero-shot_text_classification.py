# Load some data and perform zero-shot text classification using the
# Latent Embeddings approach
import os

import pandas as pd
from datasets import load_dataset
from sklearn.metrics import f1_score

import fewshot.embeddings.word_embeddings as w2v
from fewshot.embeddings.transformer_embeddings import get_transformer_embeddings
from fewshot.metrics import simple_accuracy, simple_topk_accuracy
from fewshot.models import load_transformer_model_and_tokenizer, \
    load_word_vector_model
from fewshot.path_helper import fewshot_filename
from fewshot.predictions import compute_predictions, \
    compute_predictions_projection

from fewshot.data.loaders import load_or_cache_sbert_embeddings
from fewshot.utils import load_tensor, to_tensor, compute_projection_matrix

DATADIR = "data"
DATASET_NAME = "AGNews"

## Load SBERT embeddings for dataset
sbert_embeddings = load_or_cache_sbert_embeddings(DATADIR, DATASET_NAME)

sbert_desc_embeddings = sbert_embeddings[: -len(categories)]
sbert_label_embeddings = sbert_embeddings[-len(categories):]

### Compute predictions based on cosine similarity
predictions = compute_predictions(
    sbert_desc_embeddings, sbert_label_embeddings, k=3
)

### Because our data is labeled, we can score the results!
score = simple_accuracy(df.label.tolist(), predictions)
score_intop3 = simple_topk_accuracy(df.label.tolist(), predictions)

### Visualize our data and labels


## Let's make this model a bit better!

### Learn a projection matrix that will project SBERT embeddings into Word2Vec space
# REASONING BEHIND ALL THIS NONSENSE
# Link to the Zero-Shot HF article
# Link to my own blog post describing what's going on?
w2v_model = load_word_vector_model(small=True, cache_dir=DATADIR)

scores = []
scores_intop3 = []

for topw in [1000, 10000, 100000]:
    w2v_embeddings_w2v_words, w2v_words = w2v.get_topk_w2v_vectors(w2v_model,
                                                                   k=topw)
    w2v_embeddings_w2v_words = to_tensor(w2v_embeddings_w2v_words)

    sbert_w2v_filename = fewshot_filename(
        DATADIR, f"sbert_embeddings_for_top{topw}_w2v_words.pt"
    )
    if os.path.exists(sbert_w2v_filename):
        cached_data = load_tensor(sbert_w2v_filename)
        sbert_embeddings_w2v_words = cached_data["embeddings"]
    else:
        sbert_embeddings_w2v_words = get_transformer_embeddings(
            w2v_words, model, tokenizer, output_filename=sbert_w2v_filename
        )

    projection_matrix = compute_projection_matrix(
        sbert_embeddings_w2v_words, w2v_embeddings_w2v_words
    )

    ### Compute new predictions utilizing the learned projection
    predictions = compute_predictions_projection(
        sbert_desc_embeddings, sbert_label_embeddings, projection_matrix, k=3
    )
    scores.append(
        f1_score(df.label.tolist(), [x.best for x in predictions], average="weighted"))
    scores_intop3.append(simple_topk_accuracy(df.label.tolist(), predictions))

### Visualize our modified data and label embeddings


#### ToDo
# 1. compare projections for increasing size k
# 2. compare projections learned from the most frequent words of our specific corpus
#     vs the frequency of the words inherent to the word2vec embeddings
