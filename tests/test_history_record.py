# Built-in imports
from pathlib import Path
from copy import deepcopy
from assign_rewards.history_record import PROPERTIES_KEY, VALUE_KEY

# External imports
import pytest
from pytest_cases import fixture
from pytest_cases import parametrize_with_cases
from pytest_cases import parametrize
from dateutil.parser import parse

# Local imports
from src.train.constants import MODEL_NAME_REGEXP
from history_record import HistoryRecord
from history_record import MESSAGE_ID_KEY, TIMESTAMP_KEY, TYPE_KEY
from history_record import MODEL_KEY
from history_record import REWARD_KEY, VARIANT_KEY, GIVENS_KEY, COUNT_KEY, RUNNERS_UP_KEY, SAMPLE_KEY
from history_record import MissingTimestampError, InvalidTimestampError
import config


def get_record(
    msg_val   = "A",
    ts_val    = "2021-10-07T07:24:06.126+02:00",
    type_val  = "decision",
    model_val = "messages-2.0",
    count_val = 1):
    """Return a default valid record """

    return {
        MESSAGE_ID_KEY : msg_val,
        TIMESTAMP_KEY  : ts_val,
        TYPE_KEY       : type_val,
        MODEL_KEY      : model_val,
        COUNT_KEY      : count_val,
        VARIANT_KEY    : { "text": "Have the courage to surrender to what happens next." },
        GIVENS_KEY     : {
            "app"                      : "#Mindful",
            "device"                   : "iPhone",
            "since_session_start"      : 323723.807,
            "since_midnight"           : 26646.122,
            "improve_version"          : 6000,
            "screen_height"            : 2532,
            "language"                 : "nb",
            "app_version"              : 7009,
            "country"                  : "NO",
            "device_version"           : 13003,
            "share_ratio"              : 0.0030716722831130028,
            "os"                       : "ios",
            "screen_width"             : 1170,
            "session_count"            : 1,
            "build_version"            : 2574000,
            "screen_pixels"            : 2962440,
            "carrier"                  : "Telenor",
            "since_born"               : 792140.915,
            "timezone"                 : 2,
            "os_version"               : 14007.001,
            "page"                     : 2462,
            "weekday"                  : 4.3084,
            "decision_count"           : 25,
            "since_last_session_start" : 792140.914,
            "shared" : {
                "This moment is happening anyway. Stop trying to control it.": 1,
                "There's no need to try so hard.": 1,
                "Don't forget to love yourself.": 1,
                "This is it.": 1
            },
        },
        RUNNERS_UP_KEY  : [ { "text": "You are safe." } ],
        SAMPLE_KEY      : { "text": "Remember when you wanted what you now have?" },
    }


class CasesRecords:

    def case_valid_record(self):
        return get_record()
    
    def case_missing_variant(self):
        r = get_record()
        del r[VARIANT_KEY]
        return r
    
    # A missing timestamp raises an error and that's tested elsewhere
    # def case_missing_timestamp(self):
    #     pass


@parametrize_with_cases("r", cases=CasesRecords)
def test_to_rewarded_decision_dict(r, current_cases):
    """
    Test a decision record's generated dict representation is correct.

    Parameters
    ----------
    r: pytest-cases' a case parameter
    current_cases: pytest-cases fixture
    """

    # Access the case details
    case_id, fun, params = current_cases["r"]
    
    record = HistoryRecord(r)
    result = record.to_rewarded_decision_dict()
    
    if case_id == "missing_variant":
        assert result[VARIANT_KEY] is None

    elif case_id == "valid_record":        
        assert isinstance(result, dict)

        # Assert all these keys are present in the result
        FIXED_KEYS = [TIMESTAMP_KEY, REWARD_KEY, VARIANT_KEY]
        OTHER_KEYS = [GIVENS_KEY, COUNT_KEY, RUNNERS_UP_KEY, SAMPLE_KEY]
        for key in FIXED_KEYS+OTHER_KEYS: assert key in result

        # Assert types
        assert isinstance(result[TIMESTAMP_KEY], str)
        assert isinstance(result[REWARD_KEY], int) or isinstance(result[REWARD_KEY], float)
        assert isinstance(result[GIVENS_KEY], dict)
        # assert isinstance(result[VARIANT_KEY], whatever) # All variant types are valid
        assert isinstance(result[COUNT_KEY], int) 
        assert isinstance(result[RUNNERS_UP_KEY], list) 
        # assert isinstance(result[SAMPLE_KEY], whatever) # All sample types are valid

        # Assert these values are in the dict
        assert result[TIMESTAMP_KEY]  == "2021-10-07T07:24:06.126000+02:00"
        assert result[REWARD_KEY]     == 0
        assert result[VARIANT_KEY]    == r[VARIANT_KEY]
        assert result[GIVENS_KEY]     == r[GIVENS_KEY]
        assert result[COUNT_KEY]      == r[COUNT_KEY]
        assert result[RUNNERS_UP_KEY] == r[RUNNERS_UP_KEY]
        assert result[SAMPLE_KEY]     == r[SAMPLE_KEY]


class CasesTimestamps:

    record_base = {
        TIMESTAMP_KEY   : "2021-10-07T07:00:00.126+0{h}:00",
    }

    def case_in_window_same_tz(self):
        ts = self.record_base[TIMESTAMP_KEY].format(h=0)
        return {
            TIMESTAMP_KEY : (parse(ts) + config.REWARD_WINDOW/2).isoformat(),
        }

    def case_in_window_limit_same_tz(self):
        ts = self.record_base[TIMESTAMP_KEY].format(h=0)
        return {
            TIMESTAMP_KEY : (parse(ts) + config.REWARD_WINDOW).isoformat(),
        }

    def case_in_window_different_tz(self):
        ts = self.record_base[TIMESTAMP_KEY].format(h=5)
        return {
            TIMESTAMP_KEY : (parse(ts) + config.REWARD_WINDOW/2).isoformat(),
        }

    def case_out_of_window_same_tz(self):
        ts = self.record_base[TIMESTAMP_KEY].format(h=0)
        return {
            TIMESTAMP_KEY : (parse(ts) + config.REWARD_WINDOW*1.1).isoformat(),
        }

    def case_out_of_window_different_tz(self):
        ts = self.record_base[TIMESTAMP_KEY].format(h=5)
        return {
            TIMESTAMP_KEY : (parse(ts) + config.REWARD_WINDOW*1.1).isoformat(),
        }


@parametrize_with_cases("r", cases=CasesTimestamps)
def test_reward_window_contains(r, current_cases):
    """
    Test that a timestamp falls or not within a time window with 
    respect to another timestamp.

    Parameters
    ----------
    r: pytest-cases' a case parameter
    current_cases: pytest-cases fixture
    """
    record_base = CasesTimestamps.record_base
    record_base[TIMESTAMP_KEY] = record_base[TIMESTAMP_KEY].format(h=0)
    record1 = HistoryRecord(record_base)
    record2 = HistoryRecord(r)

    # Access the case details
    case_id, fun, params = current_cases["r"]

    if case_id == "in_window_same_tz":
        assert record1.reward_window_contains(record2) == True

    if case_id == "case_in_window_limit_same_tz":
        assert record1.reward_window_contains(record2) == True
    
    elif case_id == "in_window_different_tz":
        assert record1.reward_window_contains(record2) == True

    elif case_id == "out_of_window_same_tz":
        assert record1.reward_window_contains(record2) == False
    
    elif case_id == "out_of_window_different_tz":
        assert record1.reward_window_contains(record2) == False


def test_record_type():
    """ Test is_event_record and is_decision_record for different types"""

    r = get_record(type_val="decision")
    record = HistoryRecord(r)
    assert record.is_event_record() == False
    assert record.is_decision_record() == True
    
    r = get_record(type_val="event")
    record = HistoryRecord(r)
    assert record.is_event_record() == True
    assert record.is_decision_record() == False

    
class CasesValidInvalidRecords:
    """

    Case invalid_empty: empty dict
    Case invalid_msg: invalid message_id
    Case invalid_ts : invalid timestamps
    Cases invalid_missing_message: missing message_id key
    Cases invalid_missing_ts: missing timestamp key
    Cases invalid_missing_type: missing type key
    Cases invalid_model: missing model key
    Cases invalid_missing_count: missing count key
    Cases valid: all valid cases
    """

    def case_invalid_empty(self):
        return {}
    
    @parametrize("msg_val", [None])
    def case_invalid_msg(self,msg_val):
        return get_record(msg_val=msg_val)

    @parametrize("ts_val", [None, "2021-99-99T07:24:06.126+02:00"])
    def case_invalid_timestamp(self, ts_val):
        return get_record(ts_val=ts_val)

    @parametrize("type_val", [None])
    def case_invalid_type(self, type_val):
        return get_record(type_val=type_val)

    @parametrize("model_val", ["", None])
    def case_invalid_model(self, model_val):
        return get_record(type_val="decision", model_val=model_val)

    @parametrize("count_val", ["", None, -1.1, -1, 0, 0.0, 0.1, 1.1, "1", "0"])
    def case_invalid_count(self, count_val):
        return get_record(type_val="decision", count_val=count_val)

    def case_invalid_missing_timestamp(self):
        r = get_record()
        del r[TIMESTAMP_KEY]
        return r

    def case_invalid_missing_message(self):
        r = get_record()
        del r[MESSAGE_ID_KEY]
        return r

    def case_invalid_missing_type(self):
        r = get_record()
        del r[TYPE_KEY]
        return r

    def case_invalid_missing_count(self):
        r = get_record(type_val="decision")
        del r[COUNT_KEY]
        return r

    def case_invalid_missing_type(self):
        r = get_record(type_val="decision")
        del r[MODEL_KEY]
        return r

    @parametrize("type_val", ["decision", "event"])
    def case_valid(self, type_val):
        return get_record(type_val=type_val)


@parametrize_with_cases("r", cases=CasesValidInvalidRecords)
def test_is_valid(r, current_cases):
    """Test the validity of valid/invalid records """
    
    # Access the case details
    case_id, fun, params = current_cases["r"]

    if case_id.startswith("invalid"):

        if TIMESTAMP_KEY not in r:
            with pytest.raises(MissingTimestampError):
                record = HistoryRecord(r)
        
        elif case_id == "invalid_timestamp" and r.get(TIMESTAMP_KEY) is None:
            with pytest.raises(MissingTimestampError):
                record = HistoryRecord(r)

        elif case_id == "invalid_timestamp" and r.get(TIMESTAMP_KEY) is not None:
            with pytest.raises(InvalidTimestampError):
                record = HistoryRecord(r)
        
        else:
            record = HistoryRecord(r)
            assert record.is_valid() == False

    elif case_id.startswith("valid"):
        record = HistoryRecord(r)
        assert record.is_valid() == True


def test_history_record():
    """Test other internal properties of HistoryRecord"""
    
    r = get_record(type_val="event")
    
    record = HistoryRecord(r)
    assert record.value == config.DEFAULT_EVENT_VALUE

    r[PROPERTIES_KEY] = {VALUE_KEY : 1}
    record = HistoryRecord(r)
    assert record.value == 1