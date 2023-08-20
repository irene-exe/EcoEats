import io
import os
from google.cloud import vision

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/Irene/Python/ZeroWasteRecipes/client_file_vision_ai.json'

# Initiate a client
client = vision.ImageAnnotatorClient()

# Define keywords to filter out
keywords_to_filter = ["store name", "address", "total", "subtotal", "phone", "website","special","loyalty","cash","change","net","kg","date"]

def extract_text_from_receipt(image_path):
    # Prepare the image (local source)
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    # Perform text detection on the image
    response = client.text_detection(image=image)
    texts = response.text_annotations

    # Extract and return the detected text
    extracted_text = ""
    for text in texts:
        line = text.description.strip()
        if not any(keyword in line.lower() for keyword in keywords_to_filter):
            words = line.split(',')
            for elem in words:
                if elem.isalpha():
                    extracted_text += elem + '\n'
    return extracted_text

receipt_image_path = '/Users/Irene/Python/ZeroWasteRecipes/reciept.jpeg'

# Extract text from the receipt image
extracted_receipt_text = extract_text_from_receipt(receipt_image_path)

# Make a list for extracted receipt text without filtered keywords
output_list= extracted_receipt_text.split('\n')
output_list=[i.lower() for a,i in enumerate(output_list)]

#Print list
print(output_list)

