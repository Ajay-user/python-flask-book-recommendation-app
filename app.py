from flask import Flask, render_template, redirect, request, json, make_response
import pandas as pd
import pickle
from fuzzywuzzy import process
from dataclasses import dataclass




BOOK = ''


def read_df(url):
    df = pd.read_csv(url)
    return df


def load_pkl(url):
    return pickle.load(open(url, 'rb'))


# read json
title_map = json.load(open('./title_map.json'))
title_inv_map = json.load(open('./title_inv_map.json'))
titles = list(title_map)


# loading pickle files
similarity_matrix = load_pkl("./similarity_matrix.pkl")



# loading CSV files
popular_books = read_df('./popular_books.csv')
filtered_books = read_df('./filtered_books.csv')


chatbox_init = [
    dict(origin="ai",text="Hello, welcome to book shop"), 
    dict(origin='ai',text="Which book are you looking for today?")
]


def recommend_books(book_idx, top_k=10):
    score = similarity_matrix[book_idx]
    score = list(enumerate(score))
    score = sorted(score, key=lambda x : x[1], reverse=True)
    return score[:top_k]

def find_book_title(query):
    return process.extractOne(query=query, choices=titles)

app = Flask(import_name=__name__)


# home route
@app.route(rule='/', methods=['GET'])
def home():
    return render_template('index.html', popular_books=popular_books)


@app.route(rule='/chat', methods=['GET'])
def chat():
    if request.args.get('chatbox'):
        chatbox = json.loads(request.args.get('chatbox'))
    else:
        chatbox = chatbox_init
    response = make_response(render_template('chat.html', chats=chatbox, cookies=request.cookies))
    response.set_cookie("chat_box", json.dumps(chatbox), samesite=None)
    return response




@app.route(rule='/chat', methods=['POST'])
def recommend():
    prompt = request.form.get(key='prompt')
    print(prompt)
    chatbox=json.loads(request.cookies['chat_box'])
    if prompt.strip().lower() in ['yes', 'y', 'yeah', 'yup', 'ya', 'n', 'no', 'nope', 'na', 'nei'] :
        if prompt.strip().lower() in ['yes', 'y', 'yeah', 'yup', 'ya']:
            book_name = chatbox[-2]['text'][1:]
            mask = filtered_books['book_title'] ==  book_name
            avg_rating = filtered_books[mask]['Book-Rating'].mean()
            details = filtered_books[mask].iloc[0]
            chatbox.append(dict(origin='ai', text="Here are some additional information about the book"))
            chatbox.append(dict(origin='ai',text=f"Book-Author : {str(details['Book-Author'])}"))
            chatbox.append(dict(origin='ai', text=f"Ratings : {avg_rating :0.2f}"))
            chatbox.append(dict(origin='ai', text=f"ISBN :, {details['ISBN']}"))


            chatbox.append(dict(origin='ai', text='We have some recommendations for you'))
            recommendation = recommend_books(book_idx=title_map[book_name])

            for i in recommendation:
                chatbox.append(dict(origin='ai', text=f"👉{str(title_inv_map[str(i[0])])}"))

        else:
            chatbox.append(dict(origin='ai', text="Sorry we couldn't find a match for you."))
            chatbox.append(dict(origin='ai', text='Try typing the book name alone and be more specific'))
            chatbox.append(dict(origin='ai', text="Check our popular books for ideas"))
        
        chatbox.append(dict(origin='ai', text="Enter the book name :"))
    
        return redirect(f'/chat?chatbox={json.dumps(chatbox)}')

    chatbox.append(dict(origin='user', text=prompt))
    book_title = find_book_title(prompt)
    BOOK = str(book_title[0])
    chatbox.append(dict(origin='ai', text=f"This is the closest match we found in our database"))
    chatbox.append(dict(origin="ai", text=f"👉{BOOK}"))
    chatbox.append(dict(origin="ai", text="Is this the book you are looking for ? Type Y or N"))


    return redirect(f'/chat?chatbox={json.dumps(chatbox)}')





if __name__ == "__main__":
    app.run(debug=True)
