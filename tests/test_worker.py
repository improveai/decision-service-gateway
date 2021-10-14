# Built-in imports
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import json
import gzip
import os
import sys

# External imports
from pytest_cases import parametrize
from pytest_cases import parametrize_with_cases
from pytest_cases import fixture

sys.path.append(os.getenv('HOME_DIR'))

# Local imports
# from src.assign_rewards.utils import deepcopy
# from src.assign_rewards.config import DATETIME_FORMAT
# from src.assign_rewards.config import REWARD_WINDOW
# from src.assign_rewards.join_rewards import update_listeners
# from src.assign_rewards.join_rewards import assign_rewards_to_decisions

# TODO this imports can be fixed (dev-refactor-manuel branch) but are they
#  needed ?
# from src.assign_rewards.worker import gzip_records
# from src.assign_rewards.worker import identify_dirs_to_process
# from src.assign_rewards.worker import identify_files_to_process
# from src.assign_rewards.worker import delete_output_files


BASE_TIME = "2020-01-01T00:00:00.000-05:00"


# class CasesUpdateListeners:
#     """
#     In this class:
#         - All functions receive a fixture named "listeners"
#         - The methods are named according to:
#             - the passed reward value
#             - if the reward timestamp is inside or outside the reward window

#     """

#     def case_reward_true_inside_window(self, listeners):
#         reward = True
#         reward_time_past_base = REWARD_WINDOW - 1

#         window = timedelta(seconds=reward_time_past_base)
#         record_timestamp = datetime.strptime(BASE_TIME,
#                                              DATETIME_FORMAT) + window

#         expected_listeners = deepcopy(listeners)
#         expected_listeners[0]['reward'] = 1
#         expected_listeners[1]['reward'] = 1

#         return reward, record_timestamp, expected_listeners

#     def case_reward_true_outside_window(self, listeners):
#         reward = True
#         reward_time_past_base = REWARD_WINDOW + 1

#         window = timedelta(seconds=reward_time_past_base)
#         record_timestamp = datetime.strptime(BASE_TIME,
#                                              DATETIME_FORMAT) + window

#         expected_listeners = []

#         return reward, record_timestamp, expected_listeners

#     def case_reward_false_inside_window(self, listeners):
#         reward = False
#         reward_time_past_base = REWARD_WINDOW - 1

#         window = timedelta(seconds=reward_time_past_base)
#         record_timestamp = datetime.strptime(BASE_TIME,
#                                              DATETIME_FORMAT) + window

#         expected_listeners = deepcopy(listeners)
#         expected_listeners[0]['reward'] = 0
#         expected_listeners[1]['reward'] = 0

#         return reward, record_timestamp, expected_listeners

#     def case_reward_false_outside_window(self, listeners):
#         reward = False
#         reward_time_past_base = REWARD_WINDOW + 1

#         window = timedelta(seconds=reward_time_past_base)
#         record_timestamp = datetime.strptime(BASE_TIME,
#                                              DATETIME_FORMAT) + window

#         expected_listeners = []

#         return reward, record_timestamp, expected_listeners

#     def case_reward_number_inside_window(self, listeners):
#         reward = 5.3
#         reward_time_past_base = REWARD_WINDOW - 1

#         window = timedelta(seconds=reward_time_past_base)
#         record_timestamp = datetime.strptime(BASE_TIME,
#                                              DATETIME_FORMAT) + window

#         expected_listeners = deepcopy(listeners)
#         expected_listeners[0]['reward'] = reward
#         expected_listeners[1]['reward'] = reward

#         return reward, record_timestamp, expected_listeners

#     def case_reward_number_outside_window_1(self, listeners):
#         reward = 5.3
#         reward_time_past_base = REWARD_WINDOW + 1

#         window = timedelta(seconds=reward_time_past_base)
#         record_timestamp = datetime.strptime(BASE_TIME,
#                                              DATETIME_FORMAT) + window

#         expected_listeners = []

#         return reward, record_timestamp, expected_listeners

#     def case_reward_number_outside_window_3600(self, listeners):
#         reward = 5.3
#         reward_time_past_base = REWARD_WINDOW + 3600

#         window = timedelta(seconds=reward_time_past_base)
#         record_timestamp = datetime.strptime(BASE_TIME,
#                                              DATETIME_FORMAT) + window

#         expected_listeners = []

#         return reward, record_timestamp, expected_listeners


# @parametrize_with_cases(
#     "reward, record_timestamp, expected_listeners", cases=CasesUpdateListeners)
# def test_update_listeners(
#         listeners, reward, record_timestamp, expected_listeners):
#     update_listeners(listeners, record_timestamp, reward)

#     assert len(expected_listeners) == len(listeners)

#     for i, listener in enumerate(listeners):
#         assert listener['reward'] == expected_listeners[i]['reward']


# class CasesAssignRewardsToDecisions:

#     def case_only_decision_records(self, decision_records):
#         expected_records = decision_records
#         return decision_records, [], [], expected_records

#     def case_only_rewards(self, reward_records):
#         expected_records = []
#         return [], reward_records, [], expected_records

#     def case_only_events(self, event_records):
#         expected_records = []
#         return [], [], event_records, expected_records

#     def case_one_of_each(self, decision_records, reward_records, event_records):
#         decision_record = decision_records[0]
#         reward_record = reward_records[0]
#         event_record = event_records[0]

#         records = [decision_record, reward_record, event_record]

#         # Add the effect of the reward record
#         decision_record['value'] = reward_record['rewards']['rwkey_X']
#         # Add the effect of the event record
#         decision_record['value'] += event_record['properties']['value']

#         expected_records = [decision_record]

#         return [decision_record], [reward_record], [event_record], \
#                expected_records

#     def case_all_record_types(
#             self, decision_records, reward_records, event_records,
#             rewarded_records):
#         rewarded_records = \
#             assign_rewards_to_decisions(
#                 decision_records, reward_records, event_records)
#         expected_records = rewarded_records

#         return decision_records, reward_records, event_records, expected_records


# @parametrize_with_cases(
#     "decision_records, reward_records, event_records, expected_records",
#     cases=CasesAssignRewardsToDecisions)
# def test_assign_rewards_to_decisions(
#         decision_records, reward_records, event_records, expected_records):
#     rewarded_records = \
#         assign_rewards_to_decisions(
#             decision_records, reward_records, event_records)

#     assert len(rewarded_records) == len(expected_records)

#     for i, record in enumerate(rewarded_records):
#         assert record == decision_records[i]

# TODO depends on  old / deprecated import


# TODO depends on  old / deprecated import
# @parametrize(node_id=range(3))
# def test_identify_dirs_to_process(tmpdir, monkeypatch, node_id):
#
#     base = Path(str(tmpdir))
#
#     def mockdir(*args):
#         return [Path("aa"), Path("bb"), Path("cc")]
#
#     monkeypatch.setattr(Path, 'iterdir', mockdir)
#     monkeypatch.setattr(Path, 'is_dir', lambda x: True)
#     input_dir = base / Path("unimportant_dir")
#     node_count = 3
#     actual = identify_dirs_to_process(input_dir, node_id, node_count)
#
#     expected = {0: Path("bb"), 1: Path("aa"), 2:Path("cc") }
#
#     assert actual[0] == expected[node_id]


# TODO depends on  old / deprecated import
# def test_identify_files_to_process(tmpdir, mocker):
#     """
#     Create temp files in the input and output folder. Set all their last
#     modification times equal, except for one input file. Is expected that only
#     such file will be marked to modify.

#     Args:
#         tmpdir is a fixture provided by pytest
#         mocker is a fixture provided by pytest-mock
#     """

#     input_path = Path(str(tmpdir)) / "histories"
#     output_path = Path(str(tmpdir)) / "rewarded_decisions"

#     mocker.patch('src.worker.PATH_INPUT_DIR', new=input_path)
#     mocker.patch('src.worker.PATH_OUTPUT_DIR', new=output_path)

#     (input_path/"aa").mkdir(parents=True, exist_ok=True)
#     (output_path/"aa").mkdir(parents=True, exist_ok=True)

#     input_filenames = [input_path/"aa/aa1.jsonl", input_path/"aa/aa2.jsonl"]
#     output_filenames = [output_path/"aa/aa1.jsonl.gz", output_path/"aa/aa2.jsonl.gz"]

#     modification_time = datetime.strptime(
#         "2020-01-01T00:00:00.000-05:00", DATETIME_FORMAT).timestamp()

#     access_time = modification_time

#     # Create files and set all their last modification times to zero
#     for fname in input_filenames+output_filenames:
#         with fname.open(mode="w") as f: f.write("")
#         os.utime(fname.absolute(), (access_time, modification_time))

#     # Change the last modification time of only one file
#     os.utime(input_filenames[0].absolute(), (access_time, modification_time+99))

#     dirs_to_process = [ input_path/"aa" ]
#     files_to_process = identify_files_to_process(dirs_to_process)

#     assert len(files_to_process) == 1
#     assert files_to_process[0] == input_filenames[0]

# TODO depends on  old / deprecated import
# def test_delete_output_files(tmpdir, mocker):
#
#     def makedirs(dirs):
#         for d in dirs: d.mkdir(parents=True, exist_ok=True)
#
#     def makefiles(dirs, files):
#         for d in dirs:
#             for f in files:
#                 with (d/f).open("w") as f: f.write("")
#
#     input_path = Path(str(tmpdir)) / "histories"
#     output_path = Path(str(tmpdir)) / "rewarded_decisions"
#
#     mocker.patch('src.worker.PATH_INPUT_DIR', new=input_path)
#     mocker.patch('src.worker.PATH_OUTPUT_DIR', new=output_path)
#
#     # Test the deletion of all directories
#     out_dirs = [output_path/"aa", output_path/"bb"]
#     makedirs(out_dirs)
#     delete_output_files(delete_all=True)
#     for d in out_dirs: assert not d.exists()
#
#
#     # Test that a whole output directory is deleted if the input version
#     # doesn't exist
#     in_dirs = [input_path/"aa"]
#     out_dirs = [output_path/"aa", output_path/"bb"]
#     makedirs(in_dirs)
#     makedirs(out_dirs)
#     delete_output_files()
#     assert in_dirs[0].exists()
#     assert out_dirs[0].exists()
#     assert not out_dirs[1].exists()
#
#
#     # Test that output files are deleted if their input counterpart doesn't exist
#     in_dirs = [input_path/"aa"]
#     out_dirs = [output_path/"aa"]
#     in_files = ["aa1.jsonl"]
#     out_files = ["aa1.jsonl.gz", "aa2.jsonl.gz"]
#     makedirs(in_dirs)
#     makedirs(out_dirs)
#     makefiles(in_dirs, in_files)
#     makefiles(out_dirs, out_files)
#     delete_output_files()
#     assert (in_dirs[0]/in_files[0]).exists()
#     assert (out_dirs[0]/out_files[0]).exists()
#     assert not (out_dirs[0]/out_files[1]).exists()
