import torch
import transformers
from transformers import pipeline

print(torch.__version__)          # should be 2.12.0+cpu
print(transformers.__version__)   # should be 5.8.1

pipe = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", framework="pt")
result = pipe("I love reading books", candidate_labels=["hobby", "work", "sports"])
print(result)
