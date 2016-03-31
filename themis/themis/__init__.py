import logging
import os

import pandas

logger = logging.getLogger(__name__)

QUESTION = "Question"
QUESTION_ID = "Question Id"
ANSWER = "Answer"
ANSWER_ID = "Answer Id"
TITLE = "Title"
FILENAME = "Filename"
CONFIDENCE = "Confidence"
FREQUENCY = "Frequency"
CORRECT = "Correct"
IN_PURVIEW = "In Purview"


def from_csv(file, **kwargs):
    return pandas.read_csv(file, encoding="utf-8", **kwargs)


def to_csv(filename, dataframe, **kwargs):
    dataframe.to_csv(filename, encoding="utf-8", **kwargs)


def print_csv(dataframe, **kwargs):
    print(dataframe.to_csv(encoding="utf-8", **kwargs))


class CsvFileType(object):
    """Pandas CSV file type used with argparse

    This allows you to specify the columns you wish to use and optionally rename them.
    """

    def __init__(self, columns=None, rename=None):
        self.columns = columns
        self.rename = rename

    def __call__(self, filename):
        csv = from_csv(filename, usecols=self.columns)
        if self.rename is not None:
            csv = csv.rename(columns=self.rename)
        csv.filename = filename
        return csv


class DataFrameCheckpoint(object):
    def __init__(self, output_filename, columns, interval=None):
        try:
            recovered = pandas.read_csv(open(output_filename), usecols=[0], encoding="utf-8")
            self.recovered = set(recovered[recovered.columns[0]])
            self.need_header = False
            logger.debug("Recovered %d items from disk" % len(self.recovered))
        except IOError:
            self.recovered = set()
            self.need_header = True
        except ValueError:
            raise Exception("Cannot recover data from %s" % output_filename)
        self.output_file = open(output_filename, "a")
        self.columns = columns
        self.buffer = pandas.DataFrame(columns=self.columns)
        self.interval = interval

    def write(self, *values):
        self.buffer = self.buffer.append(dict(zip(self.buffer.columns, values)), ignore_index=True)
        if self.interval is not None and len(self.buffer) % self.interval is 0:
            self.flush()

    def close(self):
        self.flush()
        self.output_file.close()

    def flush(self):
        logger.debug("Flush %d items to disk" % len(self.buffer))
        self.buffer.to_csv(self.output_file, header=self.need_header, index=False, encoding="utf-8")
        self.output_file.flush()
        self.buffer = pandas.DataFrame(columns=self.columns)
        self.need_header = False


def sample(sample_size, items, frequency, item_name, frequency_name):
    """
    Sample rows from the items table so that there are n unique items in a specified column. The sampling is done
    using frequencies in a separate table.

    :param sample_size: number of items to sample
    :param items: table to sample from
    :param frequency: table of frequencies
    :param item_name: column in the items table to sample
    :param frequency_name: column in frequency table that defines the sampling distribution
    :return: subset of the items table
    """
    t = pandas.merge(pandas.DataFrame({item_name: items[item_name].drop_duplicates()}), frequency, on=item_name)
    s = pandas.DataFrame({item_name: t.sample(sample_size, weights=frequency_name)[item_name]})
    return pandas.merge(s, items)


def configure_logger(level, format):
    logger.setLevel(level)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(format))
    logger.addHandler(h)


def ensure_directory_exists(directory):
    try:
        os.makedirs(directory)
    except OSError:
        pass
