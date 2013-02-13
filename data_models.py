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

class BehaviorDataFile(object):
    """Represents a file containing Behavior data. Initiating with BehaviorDataFile(source_file) will read the
    contents of source_file into memory and parse each column (or related group of columns) into a separate BehaviorLog object."""

    # dictionary containing column_name: [list of data points]
    data = {}

    # list of lists of columns that tells the program how behavior log objects are grouped.
    # The first column in each group contains the time field (used for plotting and analysis)
    schema = []

    def __init__(self, source_file, schema_file):
        self.source_file = source_file
        self.get_schema(schema_file)
        self.read(source_file)

    def __str__(self):
        return "<%s: %i behavior types>" % (self.source_file, len(self.schema))

    def get_schema(self, schema_file):
        self.schema = []
        with open(schema_file, 'r') as inf:
            for line in inf:
                # ignore blanks
                if line.strip() == "": continue
                if line[0] == line[0].strip():
                    # line is not indented, create a new schema item
                    self.schema.append([line.strip()])
                else:
                    self.schema[-1].append(line.strip())
        self.col_names = [item for sublist in self.schema for item in sublist]


    def read(self, source_file):
        all_lines = []
        with open(source_file, 'r') as inf:
            csv_reader = csv.reader(inf, delimiter = ",")
            # note: this only works if the CSV file is a rectangular array (i.e. includes all blanks with trailing commas)
            # CSV files are supposed to be this way, but if someone mangles them in a text editor they could potentially
            # read as valid CSV files in Excel but not be imported properly. If this happens, zip will truncate all columns 
            # to the length of the shortest column.
            transposed_file = zip(*csv_reader)

        for col in transposed_file:
            self.data[col[0]] = [float(s) for s in col[1:] if s != '']


    def get_xy_pairs(self, x=None, y=None):
        # x must be defined, but y can be left as None in the case of Boolean data
        assert x in self.data.keys()
        if y is None:
            for t in self.data[x]:
                yield (t, None)
        else:
            assert y in self.data.keys()
            for i, t in enumerate(self.data[x]):
                yield (t, self.data[y][i])

class BehaviorLog(object):
    """Represents a set of instances of a certain type of behavior. At its simplest, this is just a list of timestamps
    and a behavior name. It can also include a dictionary of corresponding key: value metadata pairs."""

    timestamps = []
    metadata = []
    title = ""
    metadata_column_lookup = {}

    def __init__(self, title):
        self.title = title

    def set_times(self, times):
        self.timestamps = [float(t) for t in times]

    def add_metadata(self, key, value_list, column_label = None):
        assert len(self.timestamps) == len(value_list)
        if len(self.metadata) != len(value_list):
            self.metadata = [{} for t in value_list]
        for idx, d in enumerate(self.metadata):
            d[key] = value_list[idx]


if __name__ == '__main__':
    #testing
    f = BehaviorDataFile('sample data/Example_BehaviorData with more variables.csv', 'sample data/Example_BehaviorData with more variables.schema')
    print list(f.get_xy_pairs(x='Initiate movement towards Right Lever', y='Velocity of movement towards Right Lever'))
    print list(f.get_xy_pairs(x='Left Lever Press'))