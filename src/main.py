import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

start = '2020-01-01'
end = '2023-01-01'

df = data.DataReader('AAPL', 'yahoo', start, end)
df.head()