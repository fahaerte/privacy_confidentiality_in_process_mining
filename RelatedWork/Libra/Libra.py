import sys
import warnings
import os
import time
from event_log_sampling import main_anonymization
from utilities_module import read_event_log_xes
from pm4py.objects.conversion.log import factory as conversion_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from input_module import xes_to_DAFSA
import numpy as np
import itertools
import warnings
import pandas as pd


def anonymize_event_log(event_log, b=2, gamma=0.05, alpha=5,epsilon_in_minutes=20,delta=1e-4):
    print("\n{} {} {} {} {} {}".format(event_log, b, gamma, alpha, epsilon_in_minutes, delta))
    start_time = time.time()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(cur_dir, 'data')
    out_dir = os.path.join(cur_dir, "output")

    # log = read_event_log_xes(os.path.join(data_dir, event_log + ".xes"))

    log,vars =xes_to_DAFSA(os.path.join(data_dir, event_log + ".xes"))

    sampled, eps_after_composition = main_anonymization(log, gamma, b, epsilon_in_minutes, alpha, delta)

    if not type(sampled) == type(0):
        sampled['time:timestamp'] = sampled['time:timestamp'].astype('datetime64[s]')
        print("The amplified eps %s ---> Original eps = %s " % (str(round(eps_after_composition, 2)), b))
        log = log['case:concept:name'].unique().size
        print("Log size is: %s cases" % (log))

        sample_size = sampled['case:concept:name'].unique().size
        print("Sample size is: %s cases" % (sample_size))

        #export XES file
        log = conversion_factory.apply(sampled)
        output_name="%s_alpha%s_b%s_gamma%s_epsilon%s_delta%s" % (event_log, alpha, b, gamma, epsilon_in_minutes, delta)
        xes_exporter.export_log(log, os.path.join(out_dir, output_name + ".xes"))


        # sampled.to_csv("output/%s_eps%s.csv"%(event_log,round(eps_after_composition,2)))
        end_time = time.time()
        print("execution time = %s seconds" % (str(end_time - start_time)))


if __name__ == "__main__":
    # if not sys.warnoptions:
    #     warnings.simplefilter("ignore")

    # event_log=os.sys.argv[1]
    # b = float(os.sys.argv[2])

    # gamma = float(os.sys.argv[3])
    # alpha = int(os.sys.argv[4])
    # epsilon_in_minutes = float(os.sys.argv[5])
    # delta = float(os.sys.argv[6])

    # anonymize_event_log(event_log,b,gamma,alpha,epsilon_in_minutes,delta)

    # Brute force try combinations of parameters
    warnings.filterwarnings("ignore")
    event_log = 'Sepsis'
    output = ''
    b_list = range(1,6)
    gamma_list = np.arange(0.01, 0.1, 0.02)
    alpha_list = range(10, 30, 10)
    epsilon_list = range(10, 60, 10)
    delta_list = np.arange(0.001, 0.005, 0.001)

    brute_force = False

    # read list of all functioning parameter combinations
    working_parameter_as_df = pd.read_csv('.\master-thesis\Libra\paras.csv')

    # Create a list of parameter lists
    param_lists = [b_list, gamma_list, alpha_list, epsilon_list, delta_list]

    # Generate all combinations
    if brute_force:
        all_combinations = list(itertools.product(*param_lists))
        # Print the combinations
        for combination in all_combinations:
            try:
                anonymize_event_log(event_log, combination[0], combination[1], combination[2], combination[3], combination[4])
                # anonymize_event_log(event_log, 2, 0.05, 10, 20, 0.001)
            except:
                print("\n------------failure of execution---------------------")
    else:
        for i in range(0, working_parameter_as_df.shape[0]):
            try:
                anonymize_event_log(event_log, 
                                    b=int(working_parameter_as_df.loc[0]['b']), 
                                    gamma=working_parameter_as_df.loc[0]['gamma'], 
                                    alpha=int(working_parameter_as_df.loc[0]['alpha']), 
                                    epsilon_in_minutes=working_parameter_as_df.loc[0]['epsilon'], 
                                    delta=working_parameter_as_df.loc[0]['delta'])
            except:
                print("\n------------failure of execution---------------------")
    





