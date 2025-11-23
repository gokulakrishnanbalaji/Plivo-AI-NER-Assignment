First install the requirements by 
```
pip install -r requirements.txt
```

then generate the synthetic data by 
```
python generate_synthetic_data.py
```

By default it will generate 1000 train and 300 dev entries, add arguments to change it.

then run the run.sh script to train the model, make predictions on dev set, compute metrics and to see the latency by running

```
./run.sh
```

if you dont have permission to run it, change it by

```
chmod 777 run.sh
```

The out folder that contains the model is saved in the gdrive and can be accessed here: 
