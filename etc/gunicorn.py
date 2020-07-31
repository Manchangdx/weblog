import multiprocessing


#bind = '0.0.0.0:1234'
bind = '127.0.0.1:1234'

workers = multiprocessing.cpu_count() * 2 + 1
