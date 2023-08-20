from flask import Flask, render_template, flash, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from bs4 import BeautifulSoup
import requests
import re
from PIL import Image
import numpy as np
from datetime import timedelta
import io
import os
from google.cloud import vision

app = Flask(__name__)
app.secret_key = "the_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(days=1)

database = SQLAlchemy(app)
usedwords = []
recipenum = 1

recipe_urls = [
    "https://www.delicious.com.au/recipes/oat-dessert-cookies-recipe/2m9xppja?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/no-waste-carrot-gnudi-august/mzcUguMz?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/lamb-minetrone-la-fridge/dNRrkCSQ?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/hot-smoked-trout-kale-feta-tart/TmF7vM68?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/thai-chicken-meatballs/ulXpnxes?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/breakfast-rye-panzanella/Z5VbXPhf?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/kecap-manis-chicken-wraps-del-sunday/y0XQbitF?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/roast-tomatoes-sourdough-gorgonzola-dolce/dWR08z2F?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/chilli-crab-egg-noodles-del-sunday/xgEQ2uaW?r=recipes/collections/uxchdynj",
    "https://www.delicious.com.au/recipes/irish-stew/pbD5w4zH?r=recipes/collections/uxchdynj",
    # Add more URLs here
]


# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/Irene/Python/ZeroWasteRecipes/client_file_vision_ai.json'

# Initiate a client
client = vision.ImageAnnotatorClient()

# Define keywords to filter out
keywords_to_filter = ["store name", "address", "total", "subtotal", "phone", "website","special","loyalty","cash","change","net","kg","date","snow","wed","green","cub","ee","my","of","inst","ra","large","ash","old","sauce","white"]

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
                if elem.isalpha() and (len(elem)>1):
                    extracted_text += elem + '\n'
                    
    print("extracted")
    return extracted_text

class datab(database.Model):
    _id = database.Column("id", database.Integer,primary_key=1)
    name = database.Column("name", database.String(100))
    url = database.Column("url", database.String(100))
    #ingredients = database.Column("ingredients", database.String(500))
    
    def __init__(self, name, url):
        self.name = name
        self.url = url
        #self.ingredients = ingredients

def iterate(key):
    database.session.query(datab).delete()
    database.session.commit()
    set = False
    
    for recipe_url in recipe_urls:
        usedwords=[]
        # Fetch and parse the webpage
        page_to_scrape = requests.get(recipe_url)
        soup = BeautifulSoup(page_to_scrape.text, 'html.parser')
    
        ingr_text = ""
        ingr_elements = soup.find_all("ul", class_="ingredient")
        for ingr in ingr_elements:
            ingr_text += ingr.get_text().replace("  ","").lower()

        ky = key.split(',')
        
        for k in ky:
            if k in ingr_text:
                send = datab(k.capitalize(), recipe_url)
                database.session.add(send)
                set = True
            database.session.commit()
        '''
        if any(word in ingr_text for word in ky):
            #saves the keyword and recipe into the database
            send = datab(key, recipe_url,ingr_text)
            database.session.add(send)
            database.session.commit()
            set = True
        '''
    
    datab.query.filter_by(name="").delete()
    database.session.commit()
    
    if set==False:
        return False

def find_in_db(keyword):
    for i in range(len(usedwords)):
        if keyword == usedwords[i]:
            return True
    return False

#routing
@app.route('/', methods=["POST", "GET"])
def main():
    if request.method == 'GET':
        return render_template('index.html', msg='')

    image = request.files['file']
    img = Image.open(image)
    img.save('/Users/Irene/Python/ZeroWasteRecipes/image.jpg')


    receipt_image_path = '/Users/Irene/Python/ZeroWasteRecipes/image.jpg'
    # Extract text from the receipt image
    files = extract_text_from_receipt(receipt_image_path)
    
        # Make a list for extracted receipt text without filtered keywords
        
    output_list= files.split('\n')
    output_list=[i.lower() for a,i in enumerate(output_list)]
    output_list=','.join(output_list)
    
    print(output_list)
    
    exists = find_in_db(output_list)
    print(exists)
    
    if not exists:
        i = iterate(output_list)
        if i == False:
            print(i)
            return redirect(url_for("nodisplay", keyword=output_list))
    return redirect(url_for("display", keyword=output_list))
    
    
    #return render_template('recipe.html', msg='Your image has been uploaded', recipeName="Yogurt", materials=material)
    
@app.route('/display/<keyword>')
def display(keyword):
    return render_template("display.html", igrnt = keyword, ingredient = datab.query.all())

@app.route('/nodisplay/<keyword>')
def nodisplay(keyword):
    return render_template("nodisplay.html", igrnt = keyword)


if __name__ == "__main__":
    with app.app_context():
        database.create_all()
    app.run(debug=True)