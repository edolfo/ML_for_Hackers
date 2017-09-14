#!/usr/bin/env python3

# Stdlib
import os
import logging
import traceback
from datetime import datetime

# Third party lib
from plotly.offline import plot
from plotly.graph_objs import Scatter, Histogram, Layout

# Set up logging
FORMAT = '%(levelname)-8s %(asctime)-15s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
log = logging.getLogger()

abs_path = os.path.abspath(os.path.curdir)

# Column names
column_names = ['date_occurred', 'date_reported', 'location', 'short_description', 'duration', 'long_description']
OCCURRED = 'date_occurred'
REPORTED = 'date_reported'
LOCATION = 'location'
SHORT_DESCRIPTION = 'short_description'
DURATION = 'duration'
LONG_DESCRIPTION = 'long_description'

DATE_FORMAT = '%Y%m%d'


def main():
    data = load_data()

    # Dates
    log.info('transforming dates')
    data, bad_date_indices = transform_dates(data)
    log.info('trimming bad dates')
    log.info('There are ' + str(len(bad_date_indices)) + ' indices to remove')
    data = trim_indices(data, bad_date_indices)

    # Locations
    log.info('transforming locations')
    data, bad_location_indices = transform_locations(data)
    log.info('trimming bad locations')
    log.info('There are ' + str(len(bad_location_indices)) + ' indices to remove')
    data = trim_indices(data, bad_location_indices)

    log.info('Done with cleanup\n')

    # Some reporting
    graph_scatter(data)
    graph_histogram(data)
    graph_occurrences(data)
    return


def graph_scatter(data):
    plot([Scatter(x=[i for i in range(len(data[OCCURRED]))], y=data[OCCURRED], mode='markers')])
    return


def graph_histogram(data):
    plot([Histogram(x = data[OCCURRED])])


def graph_occurrences(data):
    # https://plot.ly/python/subplots/#multiple-subplots
    
    return


def trim_indices(data, indices):
    """
    Given a column name and an array of indices to remove, return the main data dict with
    each corresponding entry removed for all columns.

    :param data:
    :param indices:
    :return:
    """
    for key in data.keys():
        rows = data.get(key)
        rows = [item for index, item in enumerate(rows) if index not in indices]
        data[key] = rows

    return data


def load_data():
    filename = 'data/ufo/ufo_awesome.tsv'
    data = {}
    for name in column_names:
        data[name] = []

    with open(os.path.join(abs_path, filename), 'r') as f:
        lines = f.readlines()

    line_num = 0
    try:
        for line in lines:
            split_line = line.split('\t')
            if len(split_line) > len(column_names):
                split_line = fix_long_description(split_line)

            for i in range(len(column_names)):
                key = column_names[i]
                val = split_line[i]
                data[key].append(val)
            line_num += 1
    except Exception as e:
        log.error('Found error on line number ' + str(line_num))
        err_printer(e)

    return data


def fix_long_description(split_line):
    """
    If the long description column has tabs within, merge them and return the merged array
    :param split_line:
    :return:
    """
    last_column = len(column_names) - 1
    stragglers = []

    for i in range(last_column, len(split_line)):
        stragglers.append(split_line[i])
    stragglers = [item.strip() for item in stragglers if item.strip()]
    stragglers = '  '.join(stragglers)

    split_line[last_column] = stragglers
    split_line = split_line[:last_column + 1]

    return split_line


def transform_dates(data):
    """
    Attempt to validate and transform dates (date_occurred, date_reported columns).
    Toss out any rows that don't conform.

    :param data: The data we are iterating over
    :return:
    """

    bad_indices = []

    occurred_transformed, occurred_bad_indices = column_to_date(data[OCCURRED])
    reported_transformed, reported_bad_indices = column_to_date(data[REPORTED])

    bad_indices += occurred_bad_indices
    bad_indices += reported_bad_indices

    data[OCCURRED] = occurred_transformed
    data[REPORTED] = reported_transformed

    return data, bad_indices


def column_to_date(col):
    """
    Attempt to convert the date strings inside a given column into date objects.  Return the transformed
    dates, along with a listing of the indices where we were unable to do so.
    :param col:
    :return:
    """
    transformed = []
    bad_indices = []

    for i in range(len(col)):
        row = col[i]
        try:
            # transformed.append(datetime.strptime(row, DATE_FORMAT))
            datetime.strptime(row, DATE_FORMAT)
            transformed.append(row[:4]) # Just the year
        except:
            bad_indices.append(i)
    return transformed, bad_indices


def transform_locations(data):
    """
    Given the main data struct, format locations as a dictionary of the form
    {'city': 'FOO', 'state': 'BAR'}

    Additionally, remove all locations that do not meet the following criteria:
    1) Must be in the form of 'city, state'
    2) The 'state' field must be a recognized US state
    :param data:
    :return:
    """
    locations = data.get(LOCATION)
    bad_indices = []
    transformed_locations = []
    states = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'IA', 'ID',
              'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT',
              'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI',
              'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

    for i in range(len(locations)):
        row = locations[i]
        split = row.split(',')
        if len(split) != 2:
            bad_indices.append(i)
        elif split[1].upper().strip() not in states:
            bad_indices.append(i)

        if len(split) == 1:
            transformed_locations.append(split[0])
        else:
            d = {'city': split[0],
                 'state': split[1]}
            transformed_locations.append(d)
    data[LOCATION] = transformed_locations
    return data, bad_indices


def err_printer(e):
    log.error(type(e))
    log.error(e)
    log.error(traceback.print_stack())


if __name__ == "__main__":
    main()
