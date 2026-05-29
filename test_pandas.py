import os, sys
import pandas as pd
pandas_libs_dir = os.path.join(os.path.dirname(pd.__file__), 'pandas.libs')
print('pandas_libs_dir:', pandas_libs_dir)
print('exists:', os.path.isdir(pandas_libs_dir))
if os.path.isdir(pandas_libs_dir):
    print('files:', os.listdir(pandas_libs_dir))
