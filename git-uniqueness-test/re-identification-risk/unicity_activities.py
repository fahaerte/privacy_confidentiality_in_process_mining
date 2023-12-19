""" 
Calculate the uniqueness for event logs based on traces.
Adopted the algorithm proposed in:
Y.A. de Montjoye, C.A. Hidalgo,M. Verleysen and V.D. Blondel, V.D.: Unique in the
Crowd: The Privacy Bounds of Human Mobility. Scientific Reports 3 (2013) 1376

March, 2020

"""
import pandas as pd
import numpy as np
import random
import sys
import re

from scipy.stats import itemfreq


def generate_projection_view(projections_local, case_attribute_local, activity_local, event_attribute_local,
                             timestamp_local):
    """ Depending on the projection, the corresponding columns are selected."""

    if projections_local == 'A':
        qi = []
        events = activity_local + timestamp_local
    elif projections_local == 'B':
        qi = case_attribute_local
        events = activity_local + event_attribute_local
    elif projections_local == 'C':
        qi = []
        events = activity_local + event_attribute_local
    elif projections_local == 'D':
        qi = case_attribute_local
        events = activity_local
    elif projections_local == 'E':
        qi = []
        events = activity_local
    else:
        sys.exit("The given projection '" + projections_local + "' is not a valid projection")
    return qi, events


def prepare_data(events, data, attributes_local):
    """ Put the data in the right format. The column of the activities and event
    attributes consist of a list with the corresponding events.
    """
    # cols = data.columns
    # cols = [re.sub(r'\d+$', '', c) for c in cols]
    # print([print(c) for c in set(cols)])
    # print()
    for event in events:
        filter_col = [col for col in data if col.startswith(event)]
        col_name = event + '_combined'
        attributes_local.append(col_name)
        if type(data[filter_col[0]][0]).__name__ == 'str':
            data[col_name] = data[filter_col].apply(lambda row: row.tolist(), axis=1) 
            data[col_name] = data[col_name].apply(helps) 
        else:
            data[filter_col] = data[filter_col].astype(str)
            data[col_name] = data[filter_col].apply(lambda row: row.tolist(), axis=1)
            data[col_name] = data[col_name].apply(helps) 
    return data.loc[:, attributes_local]


def calculate_unicity(data, qi, events, number_points):
    """ Calculate the unicity based on randomly selected points.
    events[0] represents the column of activities. 
    The other events[1] ... events[len(events)-1] correspond to the other event attributes or timestamps.
    
    1. Activities and their correspondig attributes are selected randomly. We call them points. 
    2. Each case, more precisely all its points, are compared with the others.
    If the case is the only one with these points, it is declared as unique.
    The sum(uniques) represents the number of cases that are unique with the given points.
    3. Unicity is then the proportion of unique cases compared to the total number of cases.  
    """
    
    if number_points > 1:
        data = generate_random_points_absolute(data, events[0], number_points)
    else:
        data = generate_random_points(data, events[0], number_points)

    for k in range(1, len(events)):
        event = events[k]
        col_name = event + '_combined'
        col_name_new = event + '_points'
        data[col_name_new] = data.apply(make_otherpoints, args=[col_name, events[0]], axis=1)

    uniques = data.apply(uniqueness, args=[qi, events, data], axis=1)
    unicity = sum(uniques)/len(data)  
    return unicity


def generate_random_points(data, activity_local, number_points_local):
    """ generates random points depending on the relative frequency """
    data['random_p'] = data.apply(lambda x:
                                  random.sample(list(enumerate(x[activity_local+'_combined'])),
                                                int(len(x[activity_local + '_combined'])*number_points_local))
                                  if (int(len(x[activity_local+'_combined'])*number_points_local) > 1)
                                  else random.sample(list(enumerate(x[activity_local+'_combined'])), 1), axis=1)
    data['random_points_number'] = data.apply(lambda x: len(x.random_p), axis=1)
    data[activity_local + '_points'] = data.apply(makepoints, axis=1)
    data[activity_local + 'random_index'] = data.apply(getindex, axis=1)
    return data


def generate_random_points_absolute(data, activity_local, number_points_local):
    """ generates random points depending max trace length """
    data['random_p'] = data.apply(lambda x:
                                  random.sample(list(enumerate(x[activity_local + '_combined'])),
                                                number_points_local)
                                  if (len(x[activity + '_combined']) > number_points_local)
                                  else random.sample(list(enumerate(x[activity_local+'_combined'])),
                                                     len(x[activity_local+'_combined'])), axis=1)
    data['random_points_number'] = data.apply(lambda x: len(x.random_p), axis=1)
    data[activity_local + '_points'] = data.apply(makepoints, axis=1)
    data[activity_local + 'random_index'] = data.apply(getindex, axis=1)
    return data


def check_subset(data, subset):
    """frequency of each element than compare them"""   
    if all(elem in data for elem in subset):
        data_freq = itemfreq(data)
        subset_freq = itemfreq(subset)
        for elem in subset_freq: 
            if elem[0] in data_freq[:, 0]:
                itemindex = np.where(data_freq[:, 0] == elem[0])
                if (len(elem[0]) != len(data_freq[itemindex][0][0])) or \
                        (int(data_freq[itemindex][0][1]) < int(elem[1])):
                    return False
            else:
                return False
        return True
    return False


def makepoints(x):
    values = []
    for idx, val in x['random_p']:
        values.append(val)
    return values


def getindex(x):
    indexes = []
    for idx, val in x['random_p']:
        indexes.append(idx)
    return indexes


def make_otherpoints(x, event,act):
    points = []
    indexes = x[act+'random_index']
    for i in indexes:
        if i < len(x[event]):
            points.append(x[event][i])
    return points


def helps(x):
    n = len(x)-pd.Series(x).last_valid_index()
    del x[-n:]
    return x


def equality(x, qi, events_to_concat, row):
    """return true if all conditions true"""
    if len(qi) > 0:
        for q in qi:
            if x[q] != row[q]:
                return 0
    for e in events_to_concat:
        event_row = e + '_combined'
        points_row = e + '_points'
        if not check_subset(x[event_row], row[points_row]):
            return 0
    return 1


def uniqueness(x, qi, events_to_concat, df_data):
    
    unique = df_data.apply(equality, args=[qi, events_to_concat, x], axis=1)
    if sum(unique) == 1:
        return 1
    return 0


if __name__ == "__main__":
    pd.options.mode.chained_assignment = None 
    ################################################
    # Variables to customise
    ################################################
    # path of sources
    path_data_sources = 'master-thesis/data/'

    # source filename: The event log has to be in the format where one case corresponds to one row
    # and the columns to the activities, event and case attributes for each case.
    csv_source_file_name = 'Hospital_log.csv'

    # delimiter of csv-file
    csv_delimiter = ','
    
    # read csv. data from disk
    df_data = pd.read_csv(filepath_or_buffer=path_data_sources + csv_source_file_name, delimiter=csv_delimiter,
                          low_memory=False, header=0, nrows=100)
    
    # Specify columns
    unique_identifier = ['case:concept:name']
    case_attribute = ['case:Diagnosis', 'case:Age', 'case:Diagnosis code', 'case:Specialism code', 'case:Diagnosis Treatment Combination ID', 'case:Treatment code', 'case:Start date']
    activity = ['concept:name']
    event_attribute = ['Activity code']
    timestamp = ['time:timestamp']

    # Specify Projection
    # A: activities and timestamps 
    # B: activities, event and case attributes
    # C: activities and event attributes
    # D: activities and case attributes
    # E: activities
    projection = 'D'
    
    # Specify number or relative frequency of points
    number_points = 1

    # # # # # # # # # # # # # # # # # # # # #
    # Data preparation concatenating events
    quasi_identifier, events_to_concat = generate_projection_view(projection, case_attribute, activity,
                                                                  event_attribute, timestamp)
    attributes = unique_identifier + quasi_identifier 
    df_aggregated_data = prepare_data(events_to_concat, df_data, attributes)
    print("Data preparation finished")
    
    unicity = calculate_unicity(df_aggregated_data, quasi_identifier, events_to_concat, number_points)
    print(unicity)
