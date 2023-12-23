import pandas as pd 
colnames = [i for i in range(64)]
tor_heatmap = pd.read_csv("./tor_heatmap_AMR_MiniApp_n1728_dumpi-1.csv", names=colnames, header=None)
print(tor_heatmap.head(10))