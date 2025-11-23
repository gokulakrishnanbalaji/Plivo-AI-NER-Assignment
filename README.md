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

The out folder that contains the model is saved in the gdrive and can be accessed here: https://drive.google.com/drive/folders/1CQKFyq1vWiqVnDgyaCu45iJOCy9nr1Gs?usp=sharing

Synthetic data link: https://drive.google.com/drive/folders/19n5DfLPH5YrJV00EfZ8D1xQkjCjOm3Uu?usp=sharing

Predictions of dev data can be accessed here: https://drive.google.com/file/d/1xw-n4vuTe4bYqSeaLHMjCk4glAUJH9cy/view?usp=sharing

Metrics can be found here: https://docs.google.com/document/d/1GLgWOCypidYdkh097oJ2mOAgufOf02aYonc_B0Rxk2M/edit?usp=sharing
