from libc.stdlib cimport atoi, malloc, free
from libc.string cimport memcpy, strcpy
cimport numpy as np
import datetime
import numpy as np
import pandas as pd
cpdef mfs_dateparser(np.ndarray datetime_vec):
    """
    Parses dates in the e2t file which are in the format DD-mmm-YYYY-HHhMM
    """
    cdef int i, year, month, day, hour, min
    cdef char *datetime_str = <char *> malloc(17)
    cdef char *month_str = <char *> malloc(4)
    cdef int N = len(datetime_vec)
    cdef np.ndarray out_ar = np.empty(N, dtype=np.object) 
    
    for i in range(N):
        strcpy(datetime_str, datetime_vec[i].encode())
        datetime_str[2] = 0
        datetime_str[6] = 0
        datetime_str[11] = 0
        datetime_str[14] = 0
        min = atoi(datetime_str+15)
        hour = atoi(datetime_str+12)
        year = atoi(datetime_str+7)
        day = atoi(datetime_str)
        
        memcpy(month_str,datetime_str+3,3)
        month_str[3] = '\0'
        
        if month_str.lower()==b'jan':
            month = 1
        elif month_str.lower()==b'feb':
            month = 2
        elif month_str.lower()==b'mar':
            month = 3
        elif month_str.lower()==b'apr':
            month = 4
        elif month_str.lower()==b'may':
            month = 5
        elif month_str.lower()==b'jun':
            month = 6
        elif month_str.lower()==b'jul':
            month = 7
        elif month_str.lower()==b'aug':
            month = 8
        elif month_str.lower()==b'sep':
            month = 9
        elif month_str.lower()==b'oct':
            month = 10
        elif month_str.lower()==b'nov':
            month = 11
        elif month_str.lower()==b'dec':
            month = 12
        out_ar[i] = datetime.datetime(year, month, day, hour, min)
    free(datetime_str)
    free(month_str)
    return pd.to_datetime(out_ar)
