import os
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from urllib.parse import urljoin

# Blob Storage
BLOB_CONN_STR = "DefaultEndpointsProtocol=https;AccountName=<account_name>;AccountKey=<account_key>;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME = "documents"

# Document Intelligence
DOC_INTELLIGENCE_ENDPOINT = "https://<your-document-ai-resource>.cognitiveservices.azure.com/"
DOC_INTELLIGENCE_KEY = "<your-document-ai-key>"

def upload_to_blob(local_file_path: str) -> str:
    """Upload a file to Azure Blob Storage and return its blob URL."""
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

    try:
        container_client.create_container()
    except Exception:
        pass 

    blob_name = os.path.basename(local_file_path)
    blob_client = container_client.get_blob_client(blob_name)

    print(f"Uploading {blob_name}...")
    with open(local_file_path, "rb") as data:
        blob_client.upload_blob(
            data, overwrite=True,
            content_settings=ContentSettings(content_type="image/jpeg")
        )

    blob_url = urljoin(blob_service_client.primary_endpoint, f"{BLOB_CONTAINER_NAME}/{blob_name}")
    print(f"✅ Uploaded to: {blob_url}")
    return blob_url

def analyze_credit_card(blob_url: str):
    """Use Document Intelligence to analyze a credit card image."""
    client = DocumentIntelligenceClient(
        endpoint=DOC_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(DOC_INTELLIGENCE_KEY)
    )
    model_id = "prebuilt-creditCard"

    print("Analyzing document...")
    poller = client.begin_analyze_document_from_url(model_id, blob_url)
    result = poller.result()

    is_credit_card = False
    card_holder = None
    bank_name = None
    expiration_date = None

    for doc in result.documents:
        if "Card Number" in doc.fields or "Document Type" in doc.doc_type:
            is_credit_card = True

        for field_name, field in doc.fields.items():
            name = field_name.lower()
            value = str(field.value) if field.value else None

            if "name" in name or "holder" in name:
                card_holder = value
            elif "bank" in name or "issuer" in name:
                bank_name = value
            elif "expiry" in name or "expiration" in name or "date" in name:
                expiration_date = value

    return {
        "is_credit_card": is_credit_card,
        "holder_name": card_holder,
        "bank_name": bank_name,
        "expiration_date": expiration_date,
    }

def main():
    local_image = "credit_card.jpg" 

    blob_url = upload_to_blob(local_image)
    data = analyze_credit_card(blob_url)

    print("\n--- RESULT ---")
    print(f"Is credit card: {data['is_credit_card']}")
    print(f"Holder name: {data['holder_name']}")
    print(f"Bank name: {data['bank_name']}")
    print(f"Expiration date: {data['expiration_date']}")

if __name__ == "__main__":
    main()
