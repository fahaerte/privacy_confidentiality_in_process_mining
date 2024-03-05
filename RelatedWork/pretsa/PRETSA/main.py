from pretsa import Pretsa
from pretsa_star import Pretsa_star
import pm4py
import numpy as np
import pandas as pd

def import_xes(file_path):
    event_log = pm4py.read_xes(file_path)
    event_log['time:timestamp'] = pd.to_datetime(event_log['time:timestamp'], utc=True)
    return event_log


if __name__ == "__main__":
    file_name = 'Sepsis'
    input_dir = '../../data/'
    output_dir = 'output/'
    ks = range(2, 10)
    ts = np.arange(0.1, 1.0, 0.1)
    event_log = import_xes(input_dir + file_name + '.xes')
    event_log = event_log.sort_values(['case:concept:name', 'time:timestamp'])
    event_log['Duration'] = event_log.groupby('case:concept:name')['time:timestamp'].diff().fillna(pd.Timedelta(seconds=0))
    event_log['Duration'] = event_log['Duration'].dt.total_seconds().div(60).astype(int)
    print(event_log[['case:concept:name', 'concept:name', 'time:timestamp', 'Duration']])

    # Normal PRETSA
    pretsa = Pretsa(event_log)

    # BF-PRETSA
    pretsa_star = Pretsa_star(event_log, greedy=True)

    for k in ks:
        for t in ts:
            print("k: {} t: {} --start--".format(k, t))

            try:
                cutOutCases, distanceLog = pretsa.runPretsa(k=k, t=t)

                privateEventLog = pretsa.getPrivatisedEventLog()
                privateEventLog['Duration'] = privateEventLog['Duration'].astype(int)
                result = pd.merge(privateEventLog, event_log, how='left', on=['case:concept:name', 'concept:name', 'Duration'])

                print("Normal PRETSA:")
                print("inflictedChanges: {}".format(distanceLog))
                pm4py.write_xes(result, file_path='{}{}_privatized_k={}_t={}_normal'.format(output_dir, file_name, k, t))
                print('done\n\n')

                cutOutCases_star, distanceLog_star = pretsa_star.runPretsa(k=k, t=t)
                privateEventLog_star = pretsa_star.getPrivatisedEventLog()
                privateEventLog_star['Duration'] = privateEventLog_star['Duration'].astype(int)
                result_star = pd.merge(privateEventLog_star, event_log, how='left', on=['case:concept:name', 'concept:name', 'Duration'])

                print("PRETSA-BF:")
                print("inflictedChanges: {}".format(distanceLog))
                pm4py.write_xes(result, file_path='{}{}_privatized_k={}_t={}_bf'.format(output_dir, file_name, k, t))
                print('done\n\n')

            except:
                print("An error occurred")
