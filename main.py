import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon import functions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_id = int(os.getenv('API_ID'))  # Your actual API ID
api_hash = os.getenv('API_HASH')  # Your actual API Hash
accounts = {}

async def ask_question(question):
    return input(question)

async def login_with_phone_number():
    phone_number = await ask_question("Please enter your phone number (e.g., +1234567890): ")
    string_session = StringSession()
    client = TelegramClient(string_session, api_id, api_hash)

    await client.start(phone=phone_number)

    print('Logged in successfully')

    session_string = client.session.save()
    session_folder = 'sessions'
    sanitized_phone = ''.join(filter(str.isdigit, phone_number))
    session_file = os.path.join(session_folder, f'{sanitized_phone}.session')

    if not os.path.exists(session_folder):
        os.makedirs(session_folder)

    with open(session_file, 'w') as f:
        f.write(session_string)
    
    print(f'Session saved to {session_file}')
    accounts[phone_number] = client

async def login_with_session_file():
    session_folder = 'sessions'

    if not os.path.exists(session_folder) or not os.listdir(session_folder):
        print('No session files found.')
        return

    session_files = [f for f in os.listdir(session_folder) if f.endswith('.session')]

    print('Select a session file to login with:')
    for index, file in enumerate(session_files):
        print(f'{index + 1}. {file}')

    selected_file_index = int(await ask_question("Enter the session file number (or 0 for all): ")) - 1

    if selected_file_index == -1:
        for file in session_files:
            with open(os.path.join(session_folder, file), 'r') as f:
                session_data = f.read().strip()

            if session_data:
                client = TelegramClient(StringSession(session_data), api_id, api_hash)
                await client.start()
                phone = file.replace('.session', '')
                print(f'Logged in using session file: {file}')
                accounts[phone] = client
            else:
                print(f'Session file {file} is empty or invalid.')
    else:
        selected_file = session_files[selected_file_index]
        with open(os.path.join(session_folder, selected_file), 'r') as f:
            session_data = f.read().strip()

        if session_data:
            client = TelegramClient(StringSession(session_data), api_id, api_hash)
            await client.start()
            phone = selected_file.replace('.session', '')
            print(f'Logged in using session file: {selected_file}')
            accounts[phone] = client
        else:
            print(f'Session file {selected_file} is empty or invalid.')

async def request_webview_for_client(client, phone_number, bot_peer, url):
    try:
        result = await client(functions.messages.RequestWebViewRequest(
            peer=bot_peer,
            bot=bot_peer,
            url=url,
            platform='android'
        ))

        web_app_data = result.url.split('#')[1].split('&')[0].split('=')[1]
        
        # Determine the path to save results in the parent directory
        result_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data.txt')
        
        # Print the path and ask for confirmation
        print(f'The results will be saved to: {result_file_path}')
        proceed = await ask_question("Do you want to proceed with saving the results? (y/n): ")
        
        if proceed.lower() == 'n':
            print("Skipping saving the result.")
            return  # Cancel the saving process
            
            
  # Ask if the user wants to delete the old file or overwrite
        delete_old_file = await ask_question("Do you want to delete the old file before saving? (y/n): ")

        if delete_old_file.lower() == 'y':
            # Delete the old file if it exists
            if os.path.exists(result_file_path):
                os.remove(result_file_path)  # Delete the old file
                print("Old file deleted.")
        
        # Save the result (overwrite if the old file was deleted, append otherwise)
        with open(result_file_path, 'a' if delete_old_file.lower() == 'n' else 'w') as f:
            f.write(f'{web_app_data}\n')  # Save WebAppData


        print(f'WebView result saved to {result_file_path}')
    except Exception as e:
        print("Error requesting WebView:", e)

async def request_webview_for_all_clients():
    if not accounts:
        print('No accounts are logged in.')
        return

    bot_peer = await ask_question("Please enter the bot peer (e.g., @YourBot): ")
    url = await ask_question("Please enter the WebView URL: ")

    for phone_number, client in accounts.items():
        print(f'Processing account: {phone_number}')
        await request_webview_for_client(client, phone_number, bot_peer, url)

async def logout_client(client):
    try:
        await client.log_out()
        print('Logged out successfully.')
    except Exception as e:
        print("Error logging out:", e)

async def main():
    print('Welcome to the Telegram Bot Utility!')

    while True:
        print('1. Login with phone number')
        print('2. Login with session file')
        print('3. Request WebView for all accounts')
        print('4. Logout and exit')

        choice = await ask_question("Please select an option (1/2/3/4): ")

        if choice == '1':
            await login_with_phone_number()
        elif choice == '2':
            await login_with_session_file()
        elif choice == '3':
            await request_webview_for_all_clients()
        elif choice == '4':
            print('Logging out and exiting...')
            for client in accounts.values():
                await logout_client(client)
            break
        else:
            print('Invalid option. Please try again.')

if __name__ == '__main__':
    asyncio.run(main())
