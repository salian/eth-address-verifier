import database_helpers
from main import create_private_keys_from_mnemonic, derive_all_addresses, derive_all_addresses_and_balances
from colorama import init, Fore, Back, Style
# import tkinter as tk
import PySimpleGUI as sg


# def table_update_with_redraw(table, table_widget, table_headings, table_data, char_width):
#     max_col_width = 500
#     all_data = [table_headings] + table_data
#     # Find width in pixel and 2 extra characters for each column
#     col_widths = [min([max(map(len, columns))+2, max_col_width])*char_width for columns in zip(*all_data)]
#     table.update(values=table_data)                   # update all new data
#     # Redraw table to update new size of table if horizontal scrollbar not used, care if widget too large to fit your window or screen.
#     table_widget.pack_forget()
#     for cid, width in zip(headings, col_widths):    # Set width for each column
#         table_widget.column(cid, width=width)
#     table_widget.pack(side='left', fill='both', expand=True)    # Redraw table
#     return True


def process_private_key_list(private_key_list):
    all_addresses = derive_all_addresses(private_key_list=private_key_list)
    print(all_addresses)
    all_addresses_and_balances, positive_account_count, network_presence_count = derive_all_addresses_and_balances(
        all_addresses)
    return all_addresses_and_balances, positive_account_count, network_presence_count


def process_secret_input(key_or_mnemonic):
    # print(key_or_mnemonic)
    assert len(key_or_mnemonic) > 0
    if key_or_mnemonic.count(' ') > 10:
        # let us say this is a mnemonic
        mnemonic = key_or_mnemonic
        private_key_without_0x = ''
        private_key_list = create_private_keys_from_mnemonic(key_or_mnemonic, nonce_start=0, nonce_count=3)
    else:
        # let us say this is a private key
        mnemonic = ''
        if key_or_mnemonic[:2] == "0x":
            # It's pretty standard by 2022 not to prefix private keys with 0x.
            # But some old software could have prefixed 0x (like metamask before 2016)
            # so we strip 0x if present at the beginning of the private key
            private_key_without_0x = key_or_mnemonic[2:]
        else:
            private_key_without_0x = key_or_mnemonic
        private_key_list = list(key_or_mnemonic)

    # Either way we now have a list of private keys
    all_addresses_and_balances, positive_account_count, network_presence_count = process_private_key_list(private_key_list)
    return all_addresses_and_balances, positive_account_count, network_presence_count, mnemonic, private_key_without_0x


if __name__ == '__main__':
    print(f"PySimpleGUI {sg.version}")
    # sg.ChangeLookAndFeel('Default1')
    sg.ChangeLookAndFeel('SystemDefaultForReal')
    # sg.theme('DarkAmber')
    font = ('Courier New', 11)
    # headings = ['Type', 'Nonce', 'Address', 'Balance', 'Networks', 'URL']

    headings = ['type', 'address', 'private_key', 'nonce', 'balance', 'network_count', 'networks']
    data = []  # Empty data
    col_widths = list(map(lambda x: len(x) + 2, headings))  # find the widths of columns in character.
    max_col_width = len('ParameterNameToLongToFitIntoAColumn') + 2  # Set max midth of all columns of data to show

    layout = [
        [sg.Text("Enter the Mnemonic or Private Key:")],
        [sg.Multiline(size=(300, 5),
                      default_text='trust fox genuine future token panda approve swap mask prosper heart ahead',
                      key='textbox')],  # identify the multiline via key option
        # [sg.Multiline(size=(None, None), key='textbox')],  # identify the multiline via key option
        [sg.Button('Verify', size=(200, 1), pad=(215, 0))],
        [sg.Table(values=[[0, 0, 0, 0, 0, 0, 0, 0]], headings=headings, max_col_width=100,
                  auto_size_columns=True,
                  # cols_justification=('left','center','right','c', 'l', 'bad'),       # Added on GitHub only as of June 2022
                  display_row_numbers=False,
                  justification='left',
                  num_rows=5,
                  alternating_row_color='lightblue',
                  key='-TABLE-',
                  selected_row_colors='red on yellow',
                  enable_events=True,
                  expand_x=True,
                  expand_y=True,
                  vertical_scroll_only=False,
                  enable_click_events=True,  # Comment out to not enable header and other clicks
                  tooltip='This is a table')],
        # [sg.Button('Quit')],
        # [sg.Sizegrip()]
        # [sg.Button('Ok'), sg.Button('Quit')]
    ]

    window = sg.Window(title="Convert ETH Mnemonics and Private Keys to Addresses",
                       layout=layout,
                       size=(600, 400),
                       margins=(10, 10),
                       icon='ethereum.ico')

    # window = sg.Window("Convert ETH Mnemonics and Private Keys to Addresses", icon='ethereum.ico').Layout(layout)

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        print(event, values)
        if event in (None, sg.WIN_CLOSED, 'Quit'):  # if user closes window or clicks cancel
            break
        if event in ('Verify',):  # User clicked the Verify button
            # print('You entered in the textbox:')
            # print(values['textbox'])  # get the content of multiline via its unique key
            window['Verify'].set_cursor(cursor='wait')  # Change the mouse pointer
            window['Verify'].update(disabled=True)  # disable the Verify Button?
            all_addresses_and_balances, positive_account_count, network_presence_count, mnemonic, private_key_without_0x = process_secret_input(values['textbox'])
            if len(all_addresses_and_balances) > 0:
                table_headers = list(all_addresses_and_balances[0].keys())
                table_data = []
                for address_data_dict in all_addresses_and_balances:
                    table_data.append(list(address_data_dict.values()))
                print(table_headers)
                print(table_data)
                window['-TABLE-'].update(table_data)
                # Save to Database
                if positive_account_count or network_presence_count:
                    database_helpers.add_to_keystore(mnemonic, private_key_without_0x, all_addresses_and_balances)
            window['Verify'].update(disabled=False)
            window['Verify'].set_cursor(cursor='arrow')

    window.close()

    # sg.Window(title="Convert ETH Mnemonics and Private Keys to Addresses", layout=layout, margins=(100, 50)).read()

    # window = tk.Tk()
    # window.title('Convert ETH Mnemonics and Private Keys to Addresses')
    # window.geometry("600x200")
    # '''
    # widgets are added here
    # '''
    # # Icon set for program window
    # p1 = tk.PhotoImage(file='ethereum.png')
    # window.iconphoto(False, p1)
    # # TextBox Creation
    # inputTextAddress = tk.Text(window, height=5, width=64)
    #
    # button1 = tk.Button(window, text="Python Button 1", state=tk.DISABLED)
    # button2 = tk.Button(window, text="EN/DISABLE Button 1", command=switchButtonState)
    # inputTextAddress.pack()
    # button1.pack()
    # button2.pack()
    # window.mainloop()
