import os
import msal
import requests
import json
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

def test_graph():
    print("--- Loading Environment Variables ---")
    load_dotenv()
    
    tenant_id = os.environ.get('AZURE_TENANT_ID')
    client_id = os.environ.get('AZURE_CLIENT_ID')
    client_secret = os.environ.get('AZURE_CLIENT_SECRET')
    
    if not all([tenant_id, client_id, client_secret]):
        print("ERROR: Missing credentials in .env file.")
        print(f"Tenant ID: {'SET' if tenant_id else 'MISSING'}")
        print(f"Client ID: {'SET' if client_id else 'MISSING'}")
        print(f"Client Secret: {'SET' if client_secret else 'MISSING'}")
        return

    print("SUCCESS: Credentials loaded.")
    
    print("\n--- Milestone 1: Authentication ---")
    authority = f'https://login.microsoftonline.com/{tenant_id}'
    scopes = ['https://graph.microsoft.com/.default']
    
    try:
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret
        )
        
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            print("SUCCESS: Access Token Generated Successfully!")
            token = result["access_token"]
        else:
            print("ERROR: Authentication Failed!")
            print(f"Error: {result.get('error')}")
            print(f"Description: {result.get('error_description')}")
            return
            
    except Exception as e:
        print(f"ERROR: Exception during authentication: {e}")
        return

    print("\n--- Milestone 2: Mailbox Access (Fetch 10 Emails) ---")
    # For testing, we will just read from a generic user mailbox if specified, 
    # or the /users endpoint to verify permissions
    
    mailbox = 'invoices@airowire.com' # The default mailbox we setup
    print(f"Attempting to fetch from mailbox: {mailbox}")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    # Query Graph API for emails, top 10
    endpoint = f'https://graph.microsoft.com/v1.0/users/{mailbox}/messages?$top=10&$select=id,subject,sender,receivedDateTime,conversationId,hasAttachments'
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        print("SUCCESS: Mailbox Access Successful!")
        data = response.json()
        messages = data.get('value', [])
        
        print(f"Emails Found: {len(messages)}")
        
        print("\n--- Message Details ---")
        for idx, msg in enumerate(messages, 1):
            sender_name = msg.get('sender', {}).get('emailAddress', {}).get('name', 'Unknown')
            sender_email = msg.get('sender', {}).get('emailAddress', {}).get('address', 'Unknown')
            print(f"\nMessage {idx}:")
            print(f"  Subject: {msg.get('subject')}")
            print(f"  Sender: {sender_name} <{sender_email}>")
            print(f"  Received: {msg.get('receivedDateTime')}")
            print(f"  Conversation ID: {msg.get('conversationId')}")
            print(f"  Has Attachments: {msg.get('hasAttachments')}")
            
    else:
        print("ERROR: Mailbox Access Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print("\nTroubleshooting:")
        if response.status_code == 403:
            print("- Does the App have 'Mail.Read' Application Permissions?")
            print("- Has Admin Consent been granted?")
        elif response.status_code == 404:
            print(f"- Does the user '{mailbox}' exist in this tenant?")

if __name__ == "__main__":
    test_graph()
