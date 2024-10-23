import tkinter.messagebox
import customtkinter as ctk
import requests
import os
import threading
import mysql.connector
import tkinter.messagebox
from io import BytesIO
from PIL import Image
from newspaper import Article

# window settings
app = ctk.CTk(fg_color="#141414")
ctk.set_appearance_mode("dark")
app.geometry("500x500")
app.title("Infostellar")

# MySQL database initialisation code
con_obj = mysql.connector.connect(
    user="root",
    host="localhost",
    password=ctk.CTkInputDialog(
        title="MySQL Password", text="Enter your MySQL password").get_input(),
)
cursor = con_obj.cursor()
cursor.execute("create database if not exists infostellar")
cursor.execute("use infostellar")

# API requests
apod_info = requests.get("https://api.nasa.gov/planetary/apod?date=2023-1-4&api_key=DEMO_KEY").json()
news = requests.get("https://api.spaceflightnewsapi.net/v4/articles/").json()["results"]

# functions
def saved_apods():
    cursor.execute(
        "create table if not exists apods(title varchar(100) unique, date date, url varchar(200), copyright varchar(50))"
    )
    apods = ctk.CTkToplevel()
    apods.title("Saved APODs")
    apods.geometry("500x500")
    ctk.CTkLabel(apods, text="Saved APODs", font=("Consolas", 50)).pack()
    apods_frame = ctk.CTkScrollableFrame(apods, 1000, 500)
    cursor.execute("select * from apods")
    for apod_data in cursor.fetchall():
        title = apod_data[0]
        date = apod_data[1]
        url = apod_data[2]
        copyright = apod_data[3]
        apod_frame = ctk.CTkFrame(apods_frame, 800, 400, 10, fg_color="#5a5b5c")
        apod = ctk.CTkImage(
            dark_image=Image.open(BytesIO(requests.get(url).content)), size=(300, 300)
        )
        ctk.CTkLabel(apod_frame, text="", image=apod).place(relx=0.05, rely=0.15)
        ctk.CTkLabel(
            apod_frame, text=f"Title: {title}", font=("Consolas", 20), wraplength=400
        ).place(relx=0.5, rely=0.15)
        ctk.CTkLabel(apod_frame, text=f"Date: {date}", font=("Consolas", 20)).place(
            relx=0.5, rely=0.3
        )
        ctk.CTkLabel(
            apod_frame, text=f"Copyright: {copyright}", font=("Consolas", 20)
        ).place(relx=0.5, rely=0.4)

        apod_frame.pack_propagate(False)
        apod_frame.pack(pady=10)
    apods_frame.pack()


def save_apod_info():
    cursor.execute(
        "create table if not exists apods(title varchar(100) unique, date date, url varchar(200), copyright varchar(50))"
    )
    title = apod_info.get("title", "null")
    date = apod_info.get("date", "null")
    url = apod_info.get("hdurl", "null")
    copyright = apod_info.get("copyright", "null")
    if url != "null":
        cursor.execute(
            f"insert ignore into apods values('{title}', '{date}', '{url}', '{copyright}')"
        )
        con_obj.commit()
        download_image()
    else:
        tkinter.messagebox.showerror(
            "APOD info not available", "APOD info cannot be saved :/"
        )


def download_image():
    image_title = apod_info["title"]
    if not os.path.exists("downloaded-images"):
        os.mkdir("downloaded-images")

    for char in image_title:
        if char in '[<>:"/\\|?*]':
            image_title = str(image_title.replace(char, "-"))

    try:
        apod = requests.get(apod_info["hdurl"]).content
        with open("downloaded-images/" + image_title + ".png", "wb") as image:
            image.write(apod)
    except:
        tkinter.messagebox.showerror(
            "Image not available", "This image cannot be downloaded :/"
        )


def start_downloading_image():
    thread = threading.Thread(target = download_image)
    thread.start()


def read_more(article_number):
    full_article = ctk.CTkToplevel()
    full_article.geometry("500x500")
    full_article.title(news[article_number]["title"])
    ctk.CTkLabel(
        full_article,
        text=news[article_number]["title"],
        font=("Consolas", 25),
        wraplength=1000,
    ).pack(pady=10)
    news[article_number]["published_at"] = news[article_number]["published_at"].replace("T", " ")
    news[article_number]["published_at"] = news[article_number]["published_at"].strip("Z")
    ctk.CTkLabel(
        full_article, text=news[article_number]["published_at"], font=("Consolas", 15)
    ).place(relx=0.88, rely=0.01)
    try:
        article_image = ctk.CTkImage(
            dark_image=Image.open(
                BytesIO(requests.get(news[article_number]["image_url"]).content)
            ),
            size=(400, 400),
        )
        article_text_frame = ctk.CTkScrollableFrame(full_article, 1000, 500)
        ctk.CTkLabel(full_article, text="", image=article_image).pack(pady=10)
        article_text = Article(news[article_number]["url"])
        article_text.download()
        article_text.parse()
        article_text = article_text.text
        ctk.CTkLabel(
            article_text_frame, text=article_text, wraplength=800, font=("Consolas", 15)
        ).pack(pady=10)
        article_text_frame.pack()
    except:
        ctk.CTkLabel(
            full_article,
            text="Sorry, this article is not available for viewing :/",
            wraplength=800,
        ).pack(pady=10)


def save_article(article_number):
    news[article_number]["published_at"] = news[article_number]["published_at"].replace("T", " ")
    news[article_number]["published_at"] = news[article_number]["published_at"].strip("Z")
    cursor.execute(
        "create table if not exists news(title varchar(100) unique, url varchar(200), summary varchar(500), image_url varchar(200), published_at datetime)"
    )
    cursor.execute(
        f"""insert ignore into news values
            (
                '{news[article_number]['title']}',
                '{news[article_number]['url']}',
                '{news[article_number]['summary']}',
                '{news[article_number]['image_url']}',
                '{news[article_number]['published_at']}'
            )"""
    )
    con_obj.commit()


def read_more_saved_articles(title, url, image_url, published_at):
    full_article = ctk.CTkToplevel()
    full_article.geometry("500x500")
    full_article.title(title)
    ctk.CTkLabel(
        full_article, text = title, font=("Consolas", 25), wraplength=1000
    ).pack(pady=10)
    ctk.CTkLabel(full_article, text = published_at, font=("Consolas", 15)).place(
        relx=0.88, rely=0.01
    )
    try:
        article_image = ctk.CTkImage(
            dark_image=Image.open(BytesIO(requests.get(image_url).content)),
            size=(400, 400),
        )
        article_text_frame = ctk.CTkScrollableFrame(full_article, 1000, 500)
        ctk.CTkLabel(full_article, text="", image=article_image).pack(pady=10)
        article_text = Article(url)
        article_text.download()
        article_text.parse()
        article_text = article_text.text
        ctk.CTkLabel(
            article_text_frame, text=article_text, wraplength=800, font=("Consolas", 15)
        ).pack(pady=10)
        article_text_frame.pack()
    except:
        ctk.CTkLabel(
            full_article,
            text="Sorry, this article is not available for viewing :/",
            wraplength=800,
        ).pack(pady=10)


def saved_articles():
    articles = ctk.CTkToplevel()
    articles.title("Saved News")
    articles.geometry("500x500")
    ctk.CTkLabel(articles, text="Saved News", font=("Consolas", 50)).pack()
    articles_frame = ctk.CTkScrollableFrame(articles, 1000, 500)
    cursor.execute("select * from news")
    for article_info in cursor.fetchall():
        title = article_info[0]
        url = article_info[1]
        summary = article_info[2]
        image_url = article_info[3]
        published_at = article_info[4]
        article_frame = ctk.CTkFrame(articles_frame, 800, 200, 10, fg_color="#5a5b5c")
        ctk.CTkLabel(
            article_frame, text=title, font=("Consolas", 20), wraplength=600
        ).pack(pady=10)
        ctk.CTkLabel(
            article_frame, text=summary, font=("Consolas", 15), wraplength=800
        ).pack(pady=10)
        ctk.CTkButton(
            article_frame,
            200,
            20,
            text="Read More...",
            font=("Consolas", 15),
            fg_color="#2881e0",
            command=lambda: read_more_saved_articles(
                title, url, image_url, published_at
            ),
        ).pack()

        article_frame.pack_propagate(False)
        article_frame.pack(pady=10)
    articles_frame.pack()


ctk.CTkLabel(app, 100, 100, text="Infostellar", font=("Consolas", 50)).pack()
ctk.CTkButton(
    app,
    50,
    50,
    50,
    text="",
    image=ctk.CTkImage(dark_image=Image.open("images/image.png"), size=(50, 50)),
    fg_color="#1d1f1d",
    hover_color="#2d2e2e",
    command=saved_apods,
).place(relx=0.01, rely=0.02)
ctk.CTkButton(
    app,
    50,
    50,
    50,
    text="",
    image=ctk.CTkImage(dark_image=Image.open("images/news.png"), size=(50, 50)),
    fg_color="#1d1f1d",
    hover_color="#2d2e2e",
    command=saved_articles,
).place(relx=0.91, rely=0.02)

tab_view = ctk.CTkTabview(app, 1000, 500)


apod_tab = tab_view.add("APOD")
ctk.CTkLabel(
    apod_tab, text="Astronomy Picture of the Day(APOD) - by NASA", font=("Consolas", 30)
).pack(pady=10)
ctk.CTkButton(
    apod_tab,
    20,
    40,
    50,
    text="",
    image=ctk.CTkImage(
        dark_image=Image.open("images/download-image.png"), size=(40, 40)
    ),
    fg_color="#1d1f1d",
    hover_color="#2d2e2e",
    command=start_downloading_image,
).place(relx=0.01)
ctk.CTkButton(
    apod_tab,
    20,
    40,
    50,
    text="",
    image=ctk.CTkImage(dark_image=Image.open("images/save.png"), size=(40, 40)),
    fg_color="#1d1f1d",
    hover_color="#2d2e2e",
    command=save_apod_info,
).place(relx=0.9)
try:
    apod = ctk.CTkImage(
        dark_image=Image.open(BytesIO(requests.get(apod_info["hdurl"]).content)),
        size=(400, 400),
    )
except:
    apod = ctk.CTkImage(
        dark_image=Image.open("images/image-not-available.png"), size=(400, 400)
    )
ctk.CTkLabel(apod_tab, text="", image=apod).pack()
ctk.CTkLabel(apod_tab, text=apod_info["title"], font=("Consolas", 25)).pack(pady=10)
ctk.CTkLabel(
    apod_tab,
    text="Copyright: \n" + apod_info.get("copyright", "None").strip("\n"),
    font=("Consolas", 15),
).place(relx=0.9, rely=0.9)

news_tab = tab_view.add("News")
news_frame = ctk.CTkScrollableFrame(news_tab, 1000, 500)
news_frame.pack()

article_number = 0
for article in news:
    article_frame = ctk.CTkFrame(news_frame, 800, 200, 10, fg_color="#5a5b5c")
    ctk.CTkLabel(
        article_frame, text=article["title"], font=("Consolas", 20), wraplength=600
    ).pack(pady=10)
    ctk.CTkButton(
        article_frame,
        20,
        20,
        50,
        text="",
        image=ctk.CTkImage(dark_image=Image.open("images/save.png"), size=(20, 20)),
        fg_color="#2c2d2e",
        hover_color="#4e4f52",
        command=lambda article_number=article_number: save_article(article_number),
    ).place(relx=0.92, rely=0.05)
    ctk.CTkLabel(
        article_frame, text=article["summary"], font=("Consolas", 15), wraplength=800
    ).pack(pady=10)
    ctk.CTkButton(
        article_frame,
        200,
        20,
        text="Read More...",
        font=("Consolas", 15),
        fg_color="#2881e0",
        command=lambda article_number=article_number: read_more(article_number),
    ).pack()

    article_frame.pack_propagate(False)
    article_frame.pack(pady=10)

    article_number = article_number + 1

tab_view.pack()


app.mainloop()
