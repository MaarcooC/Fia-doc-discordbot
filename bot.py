import discord
import requests
from bs4 import BeautifulSoup
import asyncio
import os

# Set your token and Discord channel ID
DISCORD_TOKEN = '' # Enter your discord token
CHANNEL_ID =  # Enter the Discord channel ID
FIA_URL = "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071"
BASE_URL = "https://www.fia.com"  # Base URL to concatenate for full document links

# Create a set to store already sent documents
sent_documents = set()

client = discord.Client(intents=discord.Intents.default())

async def download_and_send_file(url, title, channel):
    """Download the file and send it as an attachment."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Write the file to temporary disk storage
        filename = title + ".pdf"  # Use document title as filename
        with open(filename, 'wb') as f:
            f.write(response.content)

        # Send the file as an attachment
        with open(filename, 'rb') as f:
            await channel.send(
                content=f"📄 Document: **{title}**",
                file=discord.File(f, filename=filename)
            )

        # Remove the temporary file
        os.remove(filename)

    except Exception as e:
        print(f"Error during file download or sending: {e}")

async def initialize_sent_documents():
    """Populate sent_documents with existing documents and send at least one as an example."""
    try:
        response = requests.get(FIA_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Modify the selector to extract documents from the new structure
        document_links = soup.select('.document-row a')  # Select links inside document rows

        if document_links:
            # Get the first existing document and send it
            first_doc = document_links[0]
            doc_url = first_doc['href']  # Get the document link
            # Concatenate the domain with the relative URL to get the full link
            full_doc_url = BASE_URL + doc_url
            doc_title = first_doc.find('div', class_='title').get_text(strip=True)  # Get the title

            # Add the document to the set of sent documents
            sent_documents.add(full_doc_url)

            # Get the Discord channel
            channel = client.get_channel(CHANNEL_ID)

            # Send the file
            await download_and_send_file(full_doc_url, doc_title, channel)

            # Add all existing documents to sent_documents to avoid duplicates
            for link in document_links:
                full_url = BASE_URL + link['href']
                sent_documents.add(full_url)

        print("Initial documents loaded. The bot will now monitor only new documents.")

    except requests.RequestException as e:
        print(f"Error connecting to the FIA website: {e}")

async def check_fia_documents():
    """Check for new documents on the FIA website and send them to the Discord channel."""
    global sent_documents
    try:
        response = requests.get(FIA_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Modify the selector to extract documents from the new structure
        document_links = soup.select('.document-row a')  # Select links inside document rows

        # Print found documents for debugging
        print(f"Found {len(document_links)} documents.")

        new_documents = []
        for link in document_links:
            doc_url = link['href']
            # Concatenate the domain with the relative URL to get the full link
            full_doc_url = BASE_URL + doc_url
            doc_title = link.find('div', class_='title').get_text(strip=True)  # Get the title

            # Check if the document has already been sent
            if full_doc_url not in sent_documents:
                sent_documents.add(full_doc_url)
                new_documents.append((doc_title, full_doc_url))

        channel = client.get_channel(CHANNEL_ID)

        if new_documents:
            for title, url in new_documents:
                await download_and_send_file(url, title, channel)
        # **Remove the part that sends "No new documents found"**

    except requests.RequestException as e:
        print(f"Error connecting to the FIA website: {e}")

@client.event
async def on_ready():
    print(f'Bot connected as {client.user}!')
    # Initialize the list of already existing documents and send an example document
    await initialize_sent_documents()
    # Check for new documents every 5 seconds
    while True:
        await check_fia_documents()
        await asyncio.sleep(5)  # Wait 5 seconds before checking again

client.run(DISCORD_TOKEN)
