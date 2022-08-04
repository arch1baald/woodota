from functools import lru_cache
from typing import List, Tuple

import torch
import torch.nn.functional as F
import transformers
from transformers import DistilBertTokenizer, DistilBertModel
from loguru import logger


@lru_cache
def load_text_model() -> tuple:
    model_version = 'distilbert-base-uncased'
    logger.info(f'Loading model: {model_version}')
    transformers.logging.set_verbosity_error()
    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
    model = DistilBertModel.from_pretrained("distilbert-base-uncased")
    return tokenizer, model


def get_distilbert_hidden_state(batch: List[str]) -> torch.Tensor:
    """
    Hidden State from the last TransformerBlock of DistilBert. Returns (B, T, H) Tensor, where

    - B - Batch Size,
    - T - Number of tokens in the longest string
    - H - Hidden Vector Dim (768 for DistilBert)
    """
    tokenizer, model = load_text_model()
    inputs = tokenizer(batch, return_tensors='pt', padding=True)
    outputs = model(**inputs)
    hidden_state = outputs.last_hidden_state
    return hidden_state


def get_text_embeddings(batch: List[str]) -> torch.Tensor:
    hidden_state = get_distilbert_hidden_state(batch)
    embeddings = torch.mean(hidden_state, dim=1)
    return embeddings


def search(text: str, corpus: List[str], top: int = 3) -> List[Tuple[int, str]]:
    """
    Search for text in corpus
    """
    batch = [text] + corpus
    with torch.no_grad():
        embeddings = get_text_embeddings(batch)
        similarities = F.cosine_similarity(embeddings[0:1], embeddings[1:], dim=1)
        top_ids = torch.topk(similarities, k=top).indices
    result = [
        (int(idx), corpus[idx])
        for idx in top_ids
    ]
    return result


def search_top1(text: str, corpus: List[str]) -> str:
    _, result = search(text, corpus, top=1)[0]
    return result
