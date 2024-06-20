from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    Message,
)
from os import environ, remove
from threading import Thread
from json import load
from re import search
import requests
from texts import HELP_TEXT
import bypasser
import freewall
from time import time
from db import DB
from helper_func import subscribed


# bot
with open("config.json", "r") as f:
    DATA: dict = load(f)


def getenv(var):
    return environ.get(var) or DATA.get(var, None)


bot_token = getenv("TOKEN")
api_hash = getenv("HASH")
api_id = getenv("ID")
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
with app:
    app.set_bot_commands(
        [
            BotCommand("start", "Check if bot is alive or not"),
        ]
    )

# DB
db_api = getenv("DB_API")
db_owner = getenv("DB_OWNER")
db_name = getenv("DB_NAME")
try: database = DB(api_key=db_api, db_owner=db_owner, db_name=db_name)
except: 
    print("Database is Not Set")
    database = None


# handle index
def handleIndex(ele: str, message: Message, msg: Message):
    result = bypasser.scrapeIndex(ele)
    try:
        app.delete_messages(message.chat.id, msg.id)
    except:
        pass
    if database and result: database.insert(ele, result)
    for page in result:
        app.send_message(
            message.chat.id,
            page,
            reply_to_message_id=message.id,
            disable_web_page_preview=True,
        )


# loop thread
def loopthread(message: Message, otherss=False):

    urls = []
    if otherss:
        texts = message.caption
    else:
        texts = message.text

    if texts in [None, ""]:
        return
    for ele in texts.split():
        if "http://" in ele or "https://" in ele:
            urls.append(ele)
    if len(urls) == 0:
        return

    if bypasser.ispresent(bypasser.ddl.ddllist, urls[0]):
        msg: Message = app.send_message(
            message.chat.id, "⚡ __generating...__", reply_to_message_id=message.id
        )
    elif freewall.pass_paywall(urls[0], check=True):
        msg: Message = app.send_message(
            message.chat.id, "🕴️ __jumping the wall...__", reply_to_message_id=message.id
        )
    else:
        if "https://olamovies" in urls[0] or "https://psa.wf/" in urls[0]:
            msg: Message = app.send_message(
                message.chat.id,
                "⏳ __this might take some time...__",
                reply_to_message_id=message.id,
            )
        else:
            msg: Message = app.send_message(
                message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id
            )

    strt = time()
    links = ""
    temp = None

    for ele in urls:
        if database: df_find = database.find(ele)
        else: df_find = None
        if df_find:
            print("Found in DB")
            temp = df_find
        elif search(r"https?:\/\/(?:[\w.-]+)?\.\w+\/\d+:", ele):
            handleIndex(ele, message, msg)
            return
        elif bypasser.ispresent(bypasser.ddl.ddllist, ele):
            try:
                temp = bypasser.ddl.direct_link_generator(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        elif freewall.pass_paywall(ele, check=True):
            freefile = freewall.pass_paywall(ele)
            if freefile:
                try:
                    app.send_document(
                        message.chat.id, freefile, reply_to_message_id=message.id
                    )
                    remove(freefile)
                    app.delete_messages(message.chat.id, [msg.id])
                    return
                except:
                    pass
            else:
                app.send_message(
                    message.chat.id, "__Failed to Jump", reply_to_message_id=message.id
                )
        else:
            try:
                temp = bypasser.shortners(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)

        print("bypassed:", temp)
        if temp != None:
            if (not df_find) and ("http://" in temp or "https://" in temp) and database:
                print("Adding to DB")
                database.insert(ele, temp)
            links = links + temp + "\n"

    end = time()
    print("Took " + "{:.2f}".format(end - strt) + "sec")

    if otherss:
        try:
            app.send_photo(
                message.chat.id,
                message.photo.file_id,
                f"__{links}__",
                reply_to_message_id=message.id,
            )
            app.delete_messages(message.chat.id, [msg.id])
            return
        except:
            pass

    try:
        final = []
        tmp = ""
        for ele in links.split("\n"):
            tmp += ele + "\n"
            if len(tmp) > 4000:
                final.append(tmp)
                tmp = ""
        final.append(tmp)
        app.delete_messages(message.chat.id, msg.id)
        tmsgid = message.id
        for ele in final:
            tmsg = app.send_message(
                message.chat.id,
                f"__{ele}__",
                reply_to_message_id=tmsgid,
                disable_web_page_preview=True,
            )
            tmsgid = tmsg.id
    except Exception as e:
        app.send_message(
            message.chat.id,
            f"__Failed to Bypass : {e}__",
            reply_to_message_id=message.id,
        )


@app.on_message(filters.command("start"))
def send_start(client: Client, message: Message):
    app.send_photo(
        chat_id=message.chat.id,
        photo="https://mallucampaign.in/images/img_1717953566.jpg",
        caption="__👋 Hi there! I am Link Terabox  Downloader Bot.__\n\nJust send me any terabox links and I will get you results.Go to chatting group for more info.\n\n Must Join Update Channel",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Developer 🎓", url="https://t.me/TryToLiveAlon"), InlineKeyboardButton("Updates Channel ♻️", url="https://t.me/deathking_worldd")]
        ]),
    )



@app.on_message(filters.command("bp"))
async def tb_command(client, message):
    try:
        # Extract the URL from the message text
        terabox_url = message.text.split()[1]
        api_url = f"https://expressional-leaper.000webhostapp.com/terabox.php?url={terabox_url}"
        
        # Make a request to the API
        response = requests.get(api_url).json()
        
        # Extract the fast download link from the response
        fast_download_link = response.get('response', [{}])[0].get('resolutions', {}).get('Fast Download', '')
        
        # Send the fast download link as a response or handle the case where it's not found
        if fast_download_link:
            await message.reply_text(fast_download_link)
        else:
            await message.reply_text("No fast download link found.")
    except IndexError:
        # Handle the case where the URL is not provided in the message
        await message.reply_text("Please provide a URL in the format: /bp https://teraboxapp.com/s/1RURVVHwUnXVTSQju_AXX8g")
    except Exception as e:
        # Handle any other exceptions
        await message.reply_text(f"An error occurred: {e}")

# help command
@app.on_message(filters.command("help") & subscribed)
def send_help(
    client: Client,
    message: Message,
):
    app.send_message(
        message.chat.id,
        HELP_TEXT,
        reply_to_message_id=message.id,
        disable_web_page_preview=True,
    )


# links
@app.on_message(filters.co.mmand("bp") & subscribed)
def receive(
    client: Client,
    message: Message,
):
    bypass = Thread(target=lambda: loopthread(message), daemon=True)
    bypass.start()


# doc thread
def docthread(message: Message):
    msg: Message = app.send_message(
        message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id
    )
    print("sent DLC file")
    file = app.download_media(message)
    dlccont = open(file, "r").read()
    links = bypasser.getlinks(dlccont)
    app.edit_message_text(
        message.chat.id, msg.id, f"__{links}__", disable_web_page_preview=True
    )
    remove(file)


# files
@app.on_message([filters.document, filters.photo, filters.video])
def docfile(
    client: Client,
    message: Message,
):

    try:
        if message.document.file_name.endswith("dlc"):
            bypass = Thread(target=lambda: docthread(message), daemon=True)
            bypass.start()
            return
    except:
        pass

    bypass = Thread(target=lambda: loopthread(message, True), daemon=True)
    bypass.start()


# server loop
print("Bot Starting")
app.run()
