python src/train.py \
  --model_name microsoft/MiniLM-L12-H384-uncased \
  --train data/train.jsonl \
  --dev data/dev.jsonl \
  --out_dir out \
  --epochs 20 \
  --lr 3e-5 \
  --batch_size 16 \
  --max_length 160



python src/predict.py \
  --model_dir out \
  --input data/dev.jsonl \
  --output out/dev_pred.json

python src/eval_span_f1.py \
  --gold data/dev.jsonl \
  --pred out/dev_pred.json

python src/measure_latency.py