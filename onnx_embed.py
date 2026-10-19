"""
onnx_embed.py — lightweight embedder using ONNX Runtime instead of
sentence-transformers + PyTorch. Produces identical 384-dim vectors for
the all-MiniLM-L6-v2 model but with a much smaller Lambda package footprint.

Expects the model at ./onnx_model/model_single.onnx and the tokenizer at
./onnx_model/tokenizer.json (both included in the deployment zip).
"""
import os
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

_session = None
_tokenizer = None

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onnx_model")


def _load():
    global _session, _tokenizer
    if _session is None:
        tok = Tokenizer.from_file(os.path.join(MODEL_DIR, "tokenizer.json"))
        tok.enable_padding(pad_id=0, pad_token="[PAD]")
        tok.enable_truncation(max_length=128)
        _tokenizer = tok
        _session = ort.InferenceSession(os.path.join(MODEL_DIR, "model_single.onnx"))


def get_embedding(text: str) -> list[float]:
    _load()
    enc = _tokenizer.encode_batch([text])
    input_ids = np.array([e.ids for e in enc], dtype=np.int64)
    attention_mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
    output = _session.run(["last_hidden_state"], {"input_ids": input_ids, "attention_mask": attention_mask})[0]
    mask = attention_mask[:, :, np.newaxis].astype(np.float32)
    embedding = (output * mask).sum(axis=1) / mask.sum(axis=1)
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding[0].tolist()
