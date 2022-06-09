import requests
from bs4 import BeautifulSoup


def blockscan_url(wallet_address: str) -> str:
    return "https://blockscan.com/address/" + wallet_address


def blockchainscan_networks(address: str):
    BLOCKCHAINSCAN_BASE_URL = 'https://blockscan.com/address/'
    # address = '0x8fd379246834eac74B8419FfdA202CF8051F7A03'
    blockchainscan_url = BLOCKCHAINSCAN_BASE_URL + address
    # print(blockchainscan_url)
    soup = BeautifulSoup(requests.get(blockchainscan_url).content, "html.parser")
    # search_result_divs = soup.find_all("div", class_='search-result')
    search_result_a = soup.find_all("a", class_='search-result-list')
    # print(search_result_a)
    network_details = []
    for a_tag in search_result_a:
        # network_details.append({'network': a_tag.find_next('h4').text.strip(), 'url': a_tag['href']})  # Changed?
        network_details.append({'network': a_tag.find_next('h3').text.strip(), 'url': a_tag['href']})
    network_count = len(network_details)
    # print(f"Address found on {network_count} networks.")
    # print(network_details)
    return network_count, network_details
