# doing necessary imports

from flask import Flask, render_template, request
# from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs4
from urllib.request import urlopen as req
import pymongo

app = Flask(__name__)  # initialising the flask app with the name 'app'


@app.route('/', methods=['POST', 'GET'])  # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")  # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db = dbConn['crawlerDB']  # connecting to the database called crawlerDB
            reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
            if reviews.count() > 0:  # if there is a collection with searched keyword and it has records in it
                return render_template('results.html', reviews=reviews)  # show the results to user
            else:
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString
                # preparing the URL to search the product on flipkart
                uClient = req(flipkart_url)  # requesting the webpage from the internet
                flipkartPage = uClient.read()  # reading the webpage
                uClient.close()  # closing the connection to the web server
                flipkart_html = bs4(flipkartPage, "html.parser")  # parsing the webpage as HTML
                boxes = flipkart_html.findAll("div", {
                    "class": "bhgxx2 col-12-12"})  # searching for appropriate tag to redirect to the product link
                del boxes[
                    0:3]  # the first 3 members of the list do not contain relevant information, hence deleting them.
                box = boxes[0]  # taking the first iteration (for demo)
                productLink = "https://www.flipkart.com" + box.div.div.div.a[
                    'href']  # extracting the actual product link
                prodRes = requests.get(productLink)  # getting the product page from server
                prod_html = bs4(prodRes.text, "html.parser")  # parsing the product page as HTML
                commentBoxes = prod_html.find_all('div', {
                    'class': "_3nrCtb"})  # finding the HTML section containing the customer comments

                table = db[searchString]  # creating a collection with the same name as search string.
                # Tables and Collections are analogous.
                # filename = searchString+".csv" #  filename to save the details
                # fw = open(filename, "w") # creating a local file to save the details
                # headers = "Product, Customer Name, Rating, Heading, Comment \n" # providing the heading of the columns
                # fw.write(headers) # writing first the headers to file
                reviews = []  # initializing an empty list for reviews
                #  iterating over the comment section to get the details of customer and their comments
                for commentBox in commentBoxes:
                    try:
                        name = commentBox.div.div.find_all('p', {'class': '_3LYOAd _3sxSiS'})[0].text

                    except Exception as e:
                        name = 'No Name'

                    try:
                        rating = commentBox.div.div.div.div.text

                    except Exception as e:
                        rating = 'No Rating'

                    try:
                        commentHead = commentBox.div.div.div.p.text
                    except Exception as e:
                        commentHead = 'No Comment Heading'
                    try:
                        commentTag = commentBox.div.div.find_all('div', {'class': ''})
                        customerComment = commentTag[0].div.text
                    except Exception as e:
                        customerComment = 'No Customer Comment'
                    # fw.write(searchString+","+name.replace(",", ":")+","+rating + "," +
                    # commentHead.replace(",", ":") + "," + customerComment.replace(",", ":") + "\n")
                    pydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                              "Comment": customerComment}  # saving that detail to a dictionary
                    x = table.insert_one(
                        pydict)  # inserting the dictionary containing the review comments to the collection
                    reviews.append(pydict)  # appending the comments to the review list
                return render_template('results.html', reviews=reviews)  # showing the review to the user
        except Exception as err:
            return 'something is wrong'
            # return render_template('results.html')
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8000, debug=True)  # running the app on the local machine on port 8000
