import csv


class TransientDataFile(object):
    """Represents a file containing transient data. Initiating with TransientDataFile(source_file) will read the
    contents of source_file into memory and parse each line into a separate TransientDataPoint object. The data
    property contains a list of TransientDataPoint objects corresponding to the lines in source_file."""

    # defines the order of the data fields in the input data file
    data_file_field_order = ['peak_time', 'amplitude', 'onset_time', 'rise', 'decay_time', 'area', 'baseline', 'half_width']
    has_header_row = True
    data = []

    def __init__(self, source_file, fields=None):
        if fields is not None: self.data_file_field_order = fields
        self.source_file = source_file
        self.read(source_file)

    def __str__(self):
        return "<%s: %i fields, %i records>" % (self.source_file, len(self.data_file_field_order), len(self.data))

    def read(self, source_file):
        all_lines = []
        with open(source_file, 'r') as inf:
            csv_reader = csv.reader(inf, delimiter = ",")
            for idx, line in enumerate(csv_reader):

                # skip header row
                if self.has_header_row and idx == 0: continue

                # skip blank lines
                if len(line) == 0: continue

                # otherwise, raise an Exception if the line doesn't match the defined field order
                assert len(line) == len(self.data_file_field_order)

                t = TransientDataPoint()
                t.set_from_row(line, self.data_file_field_order)
                all_lines.append(t)

        self.data = all_lines

    def get_xy_pairs(self, x='peak_time', y='amplitude'):
        assert x in self.data_file_field_order and y in self.data_file_field_order
        for d in self.data:
            yield (d[x], d[y])



class TransientDataPoint(object):
    """Represents one data point of processed transient neurotransmitter data."""

    peak_time = 0
    amplitude = 0
    onset_time = 0
    rise = 0
    decay_time = 0
    area = 0
    baseline = 0
    half_width = 0

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            assert k in dir(self)
            setattr(self, k, kwargs[k])
            
    def set_from_row(self, row, field_order):
        assert len(row) == len(field_order)
        for k, v in zip(field_order, row):
            try:
                # if the value is a string, remove thousand seperators and cast as float
                vf = float(v.replace(',',''))
            except AttributeError:
                vf = v
            setattr(self, k, vf)

    def __getitem__(self, val):
        return getattr(self, val)

class BehaviorLog(object):
    """Represents a set of instances of a certain type of behavior. At its simplest, this is just a list of timestamps
    and a behavior name. It can also include a dictionary of corresponding key: value metadata pairs."""

    timestamps = []
    metadata = []
    title = ""

    def __init__(self, title):
        self.title = title

    def set_times(self, times):
        self.timestamps = [float(t) for t in times]

    def add_metadata(self, key, value_list):
        assert len(self.timestamps) == len(value_list)
        if len(self.metadata) != len(value_list):
            self.metadata = [{} for t in value_list]
        for idx, d in enumerate(self.metadata):
            d[key] = value_list[idx]


if __name__ == '__main__':
    #testing
    f = TransientDataFile('sample data/CV5_Inst5aSuc_DATransientData.csv')
    print f