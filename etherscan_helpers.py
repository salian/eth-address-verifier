from etherscan import Etherscan
from json.decoder import JSONDecodeError
from http.client import RemoteDisconnected

from requests.exceptions import SSLError, ConnectionError
from urllib3.exceptions import MaxRetryError, ProtocolError
from tenacity import retry, wait_exponential, retry_if_exception_type, stop_after_attempt
import tenacity

from my_secrets import ETHERSCAN_API_KEY


def etherscan_api_worker(worker_data):
    eth = Etherscan(ETHERSCAN_API_KEY)
    # setup_logging()  # when this is run as a child process, we need a separate logger here.
    addresses_list = worker_data
    # print(f"{len(addresses_list) = }")
    # addresses = worker_data[0]  # if you have to pass in multiple fields, use a tuple or list
    # other_field = worker_data[1]

    # temporarily rename the process with a timestamp, for clearer logging
    # original_process_name = current_process().name
    # current_process().name = current_process().name + "-" + str(time.time())

    account_balances_list = get_eth_balance_multiple_with_retries(addresses_list)
    # assert len(account_balances_list) == 20

    current_process().name = original_process_name
    return account_balances_list


api_retry_exc_types = (JSONDecodeError,
                       MaxRetryError,
                       SSLError,
                       ConnectionError,
                       TimeoutError,
                       ConnectionResetError,
                       ConnectionAbortedError,
                       ProtocolError,
                       RemoteDisconnected,
                       AssertionError)


# api_retry_exc_types = (None,)


def return_last_retry_outcome(retry_state):
    """return the result of the last call attempt"""
    return retry_state.outcome.result()


def my_before_sleep(retry_state):
    print(f"\nRetrying {retry_state.fn}: attempt {retry_state.attempt_number} ended with: {retry_state.outcome}")
    # logging.warning(f"Retrying {retry_state.fn}: attempt {retry_state.attempt_number} ended with: {retry_state.outcome}")


@retry(retry=tenacity.retry_if_exception_type(api_retry_exc_types),
       # wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
       wait=tenacity.wait_random_exponential(multiplier=1, max=5),
       stop=tenacity.stop_after_attempt(5),
       retry_error_callback=return_last_retry_outcome,
       before_sleep=my_before_sleep
       )
def get_eth_balance_multiple_with_retries(address_list, eth=None):
    if eth is None:
        eth = Etherscan(ETHERSCAN_API_KEY)
        # what is faster?
    api_response_list = eth.get_eth_balance_multiple(address_list)
    return api_response_list
