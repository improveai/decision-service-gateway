"""
AWS Batch worker
This script is intended to be used from inside a Docker container to process
files from an EFS filesystem.
TODO: update this description
-------------------------------------------------------------------------------
Usage:
    python worker.py
"""

# Built-in imports
from datetime import timedelta
from datetime import datetime
import logging
import json
import gzip
import sys
import os
import shutil
import signal

# External imports
import mmh3
import requests

# Local imports
from utils import load_sorted_records
from utils import name_no_ext
from config import OUTPUT_FILENAME
from config import DEFAULT_REWARD_KEY
from config import DATETIME_FORMAT
from config import DEFAULT_EVENTS_REWARD_VALUE
from config import DEFAULT_REWARD_VALUE
from config import PATH_INPUT_DIR
from config import PATH_OUTPUT_DIR
from config import LOGGING_LEVEL
from config import LOGGING_FORMAT
from exceptions import InvalidType


# Setup logging
logging.basicConfig(format=LOGGING_FORMAT, level=LOGGING_LEVEL)

# Time window to add to a timestamp
window = timedelta(seconds=int(os.environ['DEFAULT_REWARD_WINDOW_IN_SECONDS']))

SIGTERM = False


def update_listeners(listeners, record, reward):
    """
    Update the reward property value of each of the given list of records, 
    in place.
    
    Args:
        listeners: list
        record   : dict, either with a property 'type'='reward' or 'type'='event'
        reward   : number
    
    Returns:
        None
    """

    # Loop backwards to be able to remove an item in place
    for i in range(len(listeners)-1, -1, -1):
        listener = listeners[i]
        listener_timestamp = datetime.strptime(listener['timestamp'], DATETIME_FORMAT)
        record_timestamp = datetime.strptime(record['timestamp'], DATETIME_FORMAT)
        if listener_timestamp + window < record_timestamp:
            logging.debug(f'Deleting listener: {listener_timestamp}, Reward/event: {record_timestamp}')
            del listeners[i]
        else:
            # logging.debug(f'Adding reward of {float(reward)} to decision.')
            listener['reward'] = (listener.get('reward', DEFAULT_REWARD_VALUE)) + float(reward)


def assign_rewards_to_decisions(records):
    """
    1) Collect all records of type "decision" in a dictionary.
    2) Assign the rewards of records of type "rewards" to all the "decision" 
    records that match two criteria:
      - reward_key
      - a time window
    3) Assign the value of records of type "event" to all "decision" records
    within a time window.

    Args:
        records: a list of records (dicts) sorted by their "timestamp" property.

    Returns:
        dict whose keys are 'reward_key's and its values are lists of records.
    
    Raises:
        InvalidType: If a record has an invalid type attribute.
    """

    decision_records_by_reward_key = {}
    for record in records:
        if record.get('type') == 'decision':
            reward_key = record.get('reward_key', DEFAULT_REWARD_KEY)
            listeners = decision_records_by_reward_key.get(reward_key, [])
            decision_records_by_reward_key[reward_key] = listeners
            listeners.append(record)
        
        elif record.get('type') == 'rewards':
            for reward_key, reward in record['rewards'].items():
                listeners = decision_records_by_reward_key.get(reward_key, [])
                update_listeners(listeners, record, reward)
        
        elif record.get('type') == 'event':
            reward = record.get('properties', { 'properties': {} }) \
                           .get('value', DEFAULT_EVENTS_REWARD_VALUE)
            # Update all stored records
            for reward_key, listeners in decision_records_by_reward_key.items():
                update_listeners(listeners, record, reward)
            
        else:
            raise InvalidType
    
    return decision_records_by_reward_key


def gzip_records(input_file, rewarded_records):
    """
    Create a gzipped jsonlines file with the rewarded-decisions records.
    Create parent subdir if doesn't exist (e.g. dir "aa" in aa/file.jsonl.gz)
    
    Args:
        input_file      : Path object towards the input jsonl file
        rewarded_records: a dict as returned by assign_rewards_to_decisions
    """

    output_subdir =  PATH_OUTPUT_DIR / input_file.parents[0].name
    
    if not output_subdir.exists():
        logging.debug(f"Folder '{str(output_subdir)}' doesn't exist. Creating.")
        output_subdir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_subdir / OUTPUT_FILENAME.format(input_file.name)

    try:
        if output_file.exists():
            logging.info(f"Overwriting output file '{output_file}'")
        else:
            logging.info(f"Writing new output file '{output_file}'")
        
        with gzip.open(output_file.absolute(), mode='wt') as gzf:
            for reward_key, records in rewarded_records.items():
                for record in records:
                    gzf.write((json.dumps(record) + "\n"))
    
    except Exception as e:
        logging.error(
            f'An error occurred while trying to write the gzipped file:'
            f'{str(output_file)}'
            f'{e}')
        raise e


def identify_dirs_to_process(input_dir, node_id: int, node_count: int):
    """
    Identify which dirs should this worker process.

    Args:
        input_dir : Path object towards the input folder.
        node_id   : int representing the id of the target node (zero-indexed)
        node_count: int representing the number of total nodes of the cluster
    
    Returns:
        List of Path objects representing folders
    """
    
    dirs_to_process = []
    for d in input_dir.iterdir():
        if d.is_dir():
            directory_int = mmh3.hash(d.name[:2], signed=False)
            if (directory_int % node_count) == node_id:
                dirs_to_process.append(d)
    
    return dirs_to_process


def identify_files_to_process(dirs_to_process):
    """
    Return a list of Path objects representing files that need to be processed.

    Args:
        dirs_to_process: List of Path objects representing folders
    
    Returns:
        List of Path objects representing files
    """

    files_to_process = []
    for input_dir in dirs_to_process:
        output_dir = PATH_OUTPUT_DIR / input_dir.name
        
        # If output dir doesn't exist, add all files to the to-process list
        if not output_dir.exists():
            for f_in in input_dir.glob('*.jsonl'):
                files_to_process.append(f_in)
            continue

        output_files = {name_no_ext(f) : f for f in output_dir.glob('*.gz')}
        
        for f_in in input_dir.glob('*.jsonl'):
            f_out = output_files.get(name_no_ext(f_in))
            
            # If no output file, add the input file to the to-process list
            if not f_out:
                files_to_process.append(f_in)
                continue
            
            logging.debug(
                f"{f_in.name}: {datetime.fromtimestamp(f_in.stat().st_mtime).strftime('%Y-%m-%d-%H:%M:%S')}; "
                f"{f_out.name}: {datetime.fromtimestamp(f_out.stat().st_mtime).strftime('%Y-%m-%d-%H:%M:%S')}")
            
            if name_no_ext(f_in) == name_no_ext(f_out):
                if f_in.stat().st_mtime > f_out.stat().st_mtime:
                    logging.debug("Adding file to process")
                    files_to_process.append(f_in)

    return files_to_process


def delete_output_files(dirs_to_process, delete_all=False):
    """
    Delete files and/or directories from the output directory.

    Args:
        delete_all: boolean
          - True : delete all output files
          - False: delete output files without corresponding input file 
    """

    PATH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if delete_all:
        for output_dir in PATH_OUTPUT_DIR.iterdir():
            if output_dir.is_dir():
                try:
                    shutil.rmtree(output_dir)
                    logging.info(f"Deleting directory '{output_dir.name}'.")
                except Exception as e:
                    logging.exception(
                        f"Error when trying to delete "
                        f"the directory tree '{output_dir.name}'")
    
    else:
        for output_dir in PATH_OUTPUT_DIR.iterdir():
            if not output_dir.is_dir():
                continue
            
            input_dir = PATH_INPUT_DIR / output_dir.name

            if not input_dir.exists():
                try:
                    shutil.rmtree(output_dir)
                    logging.info(f"Deleting directory '{output_dir.name}'.")
                except Exception as e:
                    logging.exception(
                        f"Error when trying to delete "
                        f"the directory tree '{output_dir.name}'")
                continue

            input_files = {name_no_ext(f) : f for f in input_dir.glob('*.jsonl')}
            for output_file in output_dir.glob('*.gz'):
                if not input_files.get(name_no_ext(output_file)):
                    try:
                        output_file.unlink() # Delete file
                        logging.info(f"Deleting file '{output_file.name}'.")
                    except Exception as e:
                        logging.exception(
                            f"Error when trying to delete "
                            f"file '{output_file.name}'")


def worker():
    """
    Identify the relevant folders that this worker should process, identify 
    the files that need to be processed and write the gzipped results.
    There are two modes:
        - All output files and all input files reprocessed.
        - Only input files with a last modification time newer than their 
          counterpart in the output folder will be processed.
    """

    logging.info(f"Starting AWS Batch Array job.")

    node_id       = int(os.environ['AWS_BATCH_JOB_ARRAY_INDEX'])
    node_count    = int(os.environ['JOIN_REWARDS_JOB_ARRAY_SIZE'])
    reprocess_all = True if os.environ['JOIN_REWARDS_REPROCESS_ALL'].lower() == 'true' else False

    dirs_to_process = identify_dirs_to_process(PATH_INPUT_DIR, node_id, node_count)
    delete_output_files(dirs_to_process, delete_all=reprocess_all)
    files_to_process = identify_files_to_process(dirs_to_process)

    logging.debug(
        f"This instance (node {node_id}) will process the folders: "
        f"{', '.join([d.name for d in dirs_to_process])}")
    
    logging.debug(
        f"This instance (node {node_id}) will process the files: "
        f"{', '.join([f.name for f in files_to_process])}")

    for f in files_to_process:
        handle_signals()
        sorted_records = load_sorted_records(str(f))
        rewarded_records = assign_rewards_to_decisions(sorted_records)
        gzip_records(f, rewarded_records)

    logging.info(f"AWS Batch Array (node {node_id}) finished.")

    # While we make every effort to provide this warning as soon as possible, 
    # it is possible that your Spot Instance is terminated before the warning 
    # can be made available. 
    # Test your application to ensure that it handles an unexpected instance 
    # termination gracefully, even if you are testing for interruption notices.
    # You can do so by running the application using an On-Demand Instance and
    # then terminating the On-Demand Instance yourself. 


def handle_signals():
    if SIGTERM:
        logging.info('SIGTERM SIGNAL received, quitting.')
        sys.exit()


def signal_handler(signalNumber, frame):
    global SIGTERM
    SIGTERM = True
    logging.info("SIGTERM received.")
    return


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    worker()