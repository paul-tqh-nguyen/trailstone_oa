# Paul Nguyen Technical Task

## Goal

This implements a simple ETL client for that extracts solar and wind data into CSV files. They are placed in `./output`.

## Example

Here's an example of how to examine how well this ETL works.

The first step is to setup and use the conda environment.
```
conda env create
conda activate trailstone_oa
```

Let's start the server.
```
python -m uvicorn api_data_source.main:app --reload
```

You'll see some prints to STDOUT of where the documentation of how to use the API can be found. The prints will look like this:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Visit the webpage. You should see an API key on the documentation. The text might look something like this:
```
Valid api_key:ADU8S67Ddy!d7f?
```

In this example, the API key would be `api_key:ADU8S67Ddy!d7f?`. Keep track of this. You'll need to use the ETL client.

Run the ETL client like so:
```
python3 -O etl_client.py --api-key 'ADU8S67Ddy!d7f?' # the -O helps skip expensive assertions
```

Output h5 files can be found in `./output`:
```
$ ls output
solar.h5  wind.h5
```

The contents of these files can be viewed in Python.
```

>>> import pandas as pd
>>> pd.read_hdf('./output/solar.h5')
    naive_timestamp  variable      value         last_modified_utc
0     1690329600000       850  40.995896 2023-07-26 00:00:00+00:00
1     1690329900000       636 -45.693311 2023-07-26 00:00:00+00:00
2     1690330200000       511  32.270628 2023-07-26 00:00:00+00:00
3     1690330500000       269  -8.461596 2023-07-26 00:00:00+00:00
4     1690330800000       307  32.980399 2023-07-26 00:00:00+00:00
..              ...       ...        ...                       ...
284   1689896400000        65  25.714415 2023-07-20 00:00:00+00:00
285   1689896700000       962  42.314136 2023-07-20 00:00:00+00:00
286   1689897000000       601  16.280581 2023-07-20 00:00:00+00:00
287   1689897300000       296  41.549422 2023-07-20 00:00:00+00:00
288   1689897600000        10 -39.342209 2023-07-20 00:00:00+00:00

[2023 rows x 4 columns]
>>> pd.read_hdf('./output/wind.h5')
               naive_timestamp  variable      value         last_modified_utc
0    2023-07-26 00:00:00+00:00       991  31.448564 2023-07-26 00:00:00+00:00
1    2023-07-26 00:05:00+00:00       127 -13.684136 2023-07-26 00:00:00+00:00
2    2023-07-26 00:10:00+00:00       688  -4.955002 2023-07-26 00:00:00+00:00
3    2023-07-26 00:15:00+00:00       896 -19.730403 2023-07-26 00:00:00+00:00
4    2023-07-26 00:20:00+00:00       460  -4.380822 2023-07-26 00:00:00+00:00
..                         ...       ...        ...                       ...
284  2023-07-20 23:40:00+00:00       232  23.673275 2023-07-20 00:00:00+00:00
285  2023-07-20 23:45:00+00:00       815   7.262026 2023-07-20 00:00:00+00:00
286  2023-07-20 23:50:00+00:00       906  31.983168 2023-07-20 00:00:00+00:00
287  2023-07-20 23:55:00+00:00       658   7.498665 2023-07-20 00:00:00+00:00
288  2023-07-21 00:00:00+00:00       175  37.729540 2023-07-20 00:00:00+00:00

[2023 rows x 4 columns]
>>> 
```

## Implementation & Misc. Details

To see the version of Python or other libraries we use, see the environment.yml.

Given that the task was to treat this as production code, much of my philosophy regarding documentation is that the code should document itself. For a small task like this, I assert that self-documenting code is sufficient w.r.t documentation.

I chose to use `conda` rather than `pip` for portability.

The ETL code in this repository were autoformatted using a script that resembles this:
```
autoflake --in-place --remove-unused-variables *.py 
isort *.py 
black *.py
```