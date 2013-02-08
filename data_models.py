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

    # defines the order of the data fields in the input data files
    data_file_field_order = ['peak_time', 'amplitude', 'onset_time', 'rise', 'decay_time', 'area', 'baseline', 'half_width']

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            assert k in dir(self)
            setattr(self, k, kwargs[k])
            
    def set_from_row(self, row):
        assert len(row) == len(self.data_file_field_order)
        for k, v in zip(self.data_file_field_order, row):
            setattr(self, k, float(v))

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