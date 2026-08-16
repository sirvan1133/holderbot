from pyrogram import *
from pyrogram.types import *
from pyrogram.errors.exceptions import *


from Function.db import *
from Function.keyboards import *
from Function.qr import *
from Function.search import *
from Function.admins import *
from Function.users import *
from Function.nodes import *
from Function.create import *
from Function.stase import *
from Function.myfeatures import *

DEF_FEATURES_INIT()

from datetime import datetime
import re , os , asyncio

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


app = Client( 
    "holder",      
    api_id=26410400,
    api_hash="408bf51732560cb81a0e32533b858cbf",
    bot_token=DEF_GET_BOT_TOKEN()) #from db , bot table


async def DEF_RUN_PROGRESS(client, chatid, wait_msg, func, *args):
    """Run a blocking func(*args, progress_cb) in a thread while editing
    `wait_msg` every ~2s with the live progress. Returns func's result."""
    progress = {"done": 0, "total": 0}

    def cb(done, total):
        progress["done"] = done
        progress["total"] = total

    task = asyncio.create_task(asyncio.to_thread(func, *args, cb))
    last = -1
    while not task.done():
        await asyncio.sleep(2)
        d, t = progress["done"], progress["total"]
        if t and d != last:
            last = d
            pct = int(d * 100 / t) if t else 0
            try:
                await client.edit_message_text(
                    chatid, wait_msg.id,
                    f"<b>⏳️ Progress: {d}/{t}  ({pct}%)</b>",
                    parse_mode=enums.ParseMode.HTML)
            except Exception:
                pass
    return await task


@app.on_message(filters.private)
async def holderbot(client: Client, message: Message) :
    
    MESSAGE_CHATID = message.chat.id 

    if DEF_CHECK_BOSS(MESSAGE_CHATID):
    
        if message.caption :
            MESSAGE_TEXT = message.caption
        elif message.text :
            MESSAGE_TEXT = message.text
        else :
            return
                        
        if MESSAGE_TEXT in ["🔙 cancel" , "/cancel" , "cancel" , "❌ NO ,forget."]  :
            await client.send_message(chat_id=MESSAGE_CHATID , text=f"🏛" , reply_markup=KEYBOARD_HOME)
            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
            return
        
        
        CHECK_STEP = DEF_CHECK_STEP(MESSAGE_CHATID)
        if CHECK_STEP == "None" :

            if MESSAGE_TEXT == "/start" :
                TEXT = "<b>Hello boss,I'm HolderBot (version 4.7.0)\n\nI am an open-source Telegram bot designed to provide unique and special features. All my commands are clear, but you can still refer to the <a href='https://github.com/sirvan1133/holderbot/wiki'>Wiki</a> for tutorials and guidance, open an <a href='https://github.com/sirvan1133/holderbot/issues'>issue</a> for bugs and suggestions, and join the <a href='https://t.me/ErfjabHolderbot'>channel</a> for important news.\n\nBy the way, boss, to enhance my capabilities, you can help my developer by forking the project on GitHub. Even if you're not familiar with coding, you can still contribute by <a href='https://github.com/sirvan1133/holderbot'>starring</a> the project. Either way, thank you.</b>"
                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True)

            elif MESSAGE_TEXT == "💬 Help" :
                TEXT = "<b>Hello boss, It seems you've encountered an issue! Don't worry, first check the <a href='https://github.com/sirvan1133/holderbot/wiki'>Github Wiki</a> or <a href='https://t.me/ErfjabHolderbot'>Telegram channel</a>. If your problem persists, open an <a href='https://github.com/sirvan1133/holderbot/issues'>issue on Github</a> so that my developer can respond to you promptly.\n\nAdditionally, a file containing my logs has been sent to you, which my developer needs for debugging and resolving the issue. Thank you for your cooperation, boss.</b>"
                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True)
                await client.send_document(chat_id=MESSAGE_CHATID , document="nohup.out" , file_name="holderlogs.txt" , caption=f'<b>{datetime.now().strftime("%d/%m/%Y, %H:%M")}</b>' , parse_mode=enums.ParseMode.HTML )

            elif MESSAGE_TEXT == "🖼 QR Code" :
                TEXT = "<b>Please send your link.</b>"
                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"qrcode | wait to send link")

            elif MESSAGE_TEXT == "🔍 Search" :
                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please send me the words.</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"search | wait to send words")

            elif MESSAGE_TEXT == "👨🏻‍💻 Admins" :
                KEYBOARD_ADMINS = KEYBOARD_ADMINS_LIST(MESSAGE_CHATID)
                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please select an admin or add a new admin?</b>" , reply_markup=KEYBOARD_ADMINS , parse_mode=enums.ParseMode.HTML)
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"admins | wait to select or add admin")

            elif MESSAGE_TEXT == "👤 Users" :
                WAIT_MESSGAE = await client.send_message(chat_id=MESSAGE_CHATID, text=f"<b>⏳️ in progress...</b>" , reply_markup=ReplyKeyboardRemove() , parse_mode=enums.ParseMode.HTML)
                TEXT = DEF_ALL_USERS(MESSAGE_CHATID)
                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_USERS , parse_mode=enums.ParseMode.HTML)               
                await WAIT_MESSGAE.delete()
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"users | wait to select list")

            elif MESSAGE_TEXT == "🎗 Nodes" :
                KEYBOARD_NODES_LIST = DEF_NODES_LIST(MESSAGE_CHATID)
                await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>Please select node.</b>" , reply_markup=KEYBOARD_NODES_LIST, parse_mode=enums.ParseMode.HTML)
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"nodes | wait to select node")

            elif MESSAGE_TEXT == "🎛 Monitoring" :
                BOSS_CHATID , NODE_STATUS , CHECK_NORMAL , CHECK_ERROR = DEF_MONITORING_DATA()
                if NODE_STATUS == "off" :
                    TEXT = f"<b>🔴 Monitoring is <code>off</code></b>"
                    KEYBOARD_MONITORING = KEYBOARD_OFF_MONITORING
                else :
                    TEXT = f"<b>🟢 Monitoring is <code>on</code>\nMonitoring timer : <code>{CHECK_NORMAL} second</code>\nError timer : <code>{CHECK_ERROR} second</code></b>"
                    KEYBOARD_MONITORING = KEYBOARD_ON_MONITORING  
                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_MONITORING , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"monitoring | wait to select command")
                
            elif MESSAGE_TEXT == "🗃 Templates" :
                KEYBOARD_TEMPLATES = KEYBOARD_TEMPLATES_LIST()
                await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>Please select a templates or add a new templates?</b>" , reply_markup=KEYBOARD_TEMPLATES , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"templates | wait to select command")
            
            elif MESSAGE_TEXT == "🚀 Create User" :
                KEYBOARD_TEMPLATES = KEYBOARD_CREATE_LIST()
                await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>Please select a template or create user manually.</b>" , reply_markup=KEYBOARD_TEMPLATES , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"create | wait to select command")

            elif MESSAGE_TEXT == "🎖 Notice" :
                await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>Welcome to the Messages section! This feature has been added with sponsorship the <a href='https://t.me/GrayServer'>Gray</a> collection.❤️ You can visit the Gray collection channel and bot for purchasing servers on an hourly and monthly basis, with a wide variety of locations and specifications, accompanied by clean IPs at the lowest prices.\n\nTo utilize this feature, you first need to create an inbound according to the tutorial on GitHub Wiki or the Telegram channel tutorial for Holderbot. Then, in the host setting section of that inbound, write down the texts you desire to be displayed to the user upon completion of the configuration update.\n\nYour Messages is <code>{DEF_GET_MESSAGE_STATUS(MESSAGE_CHATID)}</code></b>" , reply_markup=KEYBOARD_MESSAGES , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"message | wait to select command")

            elif MESSAGE_TEXT == "💰 Billing" :
                WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ in progress...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                KEYBOARD = await asyncio.to_thread(KEYBOARD_BILLING_ADMINS, MESSAGE_CHATID)
                await client.send_message(chat_id=MESSAGE_CHATID, text="<b>👤 Please select an admin:</b>", reply_markup=KEYBOARD, parse_mode=enums.ParseMode.HTML)
                await WAIT.delete()
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"billing | select admin")

            elif MESSAGE_TEXT == "🛠 Protocol" :
                WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ in progress...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                KEYBOARD = await asyncio.to_thread(KEYBOARD_PROTO_ADMINS, MESSAGE_CHATID)
                await client.send_message(chat_id=MESSAGE_CHATID, text="<b>🛠 Protocol management\n\n👤 Select an admin (or all admins):</b>", reply_markup=KEYBOARD, parse_mode=enums.ParseMode.HTML)
                await WAIT.delete()
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"protocol | select admin")

            elif MESSAGE_TEXT == "📅 Give Date" :
                WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ in progress...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                KEYBOARD = await asyncio.to_thread(KEYBOARD_DATE_ADMINS, MESSAGE_CHATID)
                await client.send_message(chat_id=MESSAGE_CHATID, text="<b>📅 Give expire date to time-unlimited users\n\n👤 Select an admin:</b>", reply_markup=KEYBOARD, parse_mode=enums.ParseMode.HTML)
                await WAIT.delete()
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"date | select admin")

            elif MESSAGE_TEXT == "♾ Unlimited" :
                WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ in progress...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                KEYBOARD = await asyncio.to_thread(KEYBOARD_UNLIMITED_ADMINS, MESSAGE_CHATID)
                await client.send_message(chat_id=MESSAGE_CHATID, text="<b>♾ Find unlimited users\n\n👤 Select an admin (or all admins):</b>", reply_markup=KEYBOARD, parse_mode=enums.ParseMode.HTML)
                await WAIT.delete()
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"unlimited | select admin")

            elif MESSAGE_TEXT == "🔄 Reset Alert" :
                STATUS = DEF_RESET_ALERT_STATUS()
                emoji = "🟢 on" if STATUS == "on" else "🔴 off"
                await client.send_message(chat_id=MESSAGE_CHATID, text=f"<b>🔄 Reset traffic alert is {emoji}</b>\n\n<b>When a user's traffic is reset, you'll get a notification.</b>", reply_markup=KEYBOARD_RESET_ALERT(STATUS), parse_mode=enums.ParseMode.HTML)
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"reset | toggle")

            else :
                if MESSAGE_TEXT == "🧨" or ("boss of one") in MESSAGE_TEXT or "set the messages." in MESSAGE_TEXT or "(Checker)" in MESSAGE_TEXT :
                    return
                TEXT , KEYBOARD_UPDATE_STASE = DEF_STASE_USER (MESSAGE_CHATID , MESSAGE_TEXT , KEYBOARD_HOME)
                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_UPDATE_STASE , parse_mode=enums.ParseMode.HTML)
                return      

        else :
            MESSAGES_SPLIT = MESSAGE_TEXT.strip().split(" ")
            STEP_SPLIT = CHECK_STEP.strip().split(" ")


            if CHECK_STEP.startswith("qrcode") :
                if CHECK_STEP == "qrcode | wait to send link" :
                    QRCODE_IMG = DEF_CREATE_QRCODE(MESSAGE_TEXT)
                    await client.send_photo(chat_id=MESSAGE_CHATID , photo=QRCODE_IMG,caption=f"<pre>{MESSAGE_TEXT}</pre>" , reply_markup=KEYBOARD_HOME)
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


            elif CHECK_STEP.startswith("billing") :
                if CHECK_STEP == "billing | select admin" :
                    # expects "bill: ADMINNAME"
                    if MESSAGE_TEXT.startswith("bill: ") :
                        ADMIN = MESSAGE_TEXT[len("bill: "):].strip()
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>👤 Admin :</b> <code>{ADMIN}</code>\n\n<b>🔢 Send the start point (number or exact username).\nExample: 100 or user101</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID , f"billing | start {ADMIN}")
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Please pick an admin from the list.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")

                elif CHECK_STEP.startswith("billing | start ") :
                    ADMIN = CHECK_STEP[len("billing | start "):].strip()
                    WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ calculating...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                    RES = await asyncio.to_thread(DEF_BILLING_CALC, MESSAGE_CHATID, ADMIN, MESSAGE_TEXT.strip())
                    if "error" in RES :
                        TEXT = f"<b>❌ {RES['error']}</b>"
                    else :
                        TEXT = (f"<b>📊 Billing summary</b>\n\n"
                                f"<b>👤 Admin :</b> <code>{RES['admin']}</code>\n"
                                f"<b>📍 From :</b> <code>{RES['from_user']}</code> (#{RES['from_idx']})\n"
                                f"<b>📍 To :</b> <code>{RES['to_user']}</code> (#{RES['to_idx']})\n"
                                f"<b>👥 Count :</b> <code>{RES['count']}</code>\n\n"
                                f"<b>📤 Allocated :</b> <code>{RES['allocated_gb']} GB</code>\n"
                                f"<b>📥 Used :</b> <code>{RES['used_gb']} GB</code>\n"
                                f"<b>💧 Left :</b> <code>{RES['left_gb']} GB</code>")
                    await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                    await WAIT.delete()
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


            elif CHECK_STEP.startswith("protocol") :
                # Step A: pick admin
                if CHECK_STEP == "protocol | select admin" :
                    if MESSAGE_TEXT == "🌐 All admins" :
                        ADMIN = "*all*"
                    elif MESSAGE_TEXT.startswith("padmin: ") :
                        ADMIN = MESSAGE_TEXT[len("padmin: "):].strip()
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Please pick an admin.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                        return
                    await client.send_message(chat_id=MESSAGE_CHATID , text="<b>👥 Apply to which group?</b>" , reply_markup=KEYBOARD_PROTO_GROUP , parse_mode=enums.ParseMode.HTML)
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID , f"protocol | select group {ADMIN}")

                # Step B: pick group
                elif CHECK_STEP.startswith("protocol | select group ") :
                    ADMIN = CHECK_STEP[len("protocol | select group "):].strip()
                    if MESSAGE_TEXT == "🟢 Active + OnHold" :
                        GROUP = "active_onhold"
                    elif MESSAGE_TEXT == "🕰 Expired" :
                        GROUP = "expired"
                    elif MESSAGE_TEXT == "🪫 Limited" :
                        GROUP = "limited"
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Please pick a group.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                        return
                    WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ loading protocols...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                    KEYBOARD, _ = await asyncio.to_thread(KEYBOARD_PROTOCOLS, MESSAGE_CHATID)
                    await client.send_message(chat_id=MESSAGE_CHATID, text="<b>🛠 Pick protocol\n\n➕ = add | ➖ = remove</b>", reply_markup=KEYBOARD, parse_mode=enums.ParseMode.HTML)
                    await WAIT.delete()
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID , f"protocol | select proto {ADMIN} {GROUP}")

                # Step C: pick protocol + action
                elif CHECK_STEP.startswith("protocol | select proto ") :
                    PARTS = CHECK_STEP[len("protocol | select proto "):].strip().split(" ")
                    ADMIN = PARTS[0]
                    GROUP = PARTS[1]
                    if "proto: " in MESSAGE_TEXT :
                        ACTION = "add" if MESSAGE_TEXT.startswith("➕") else "remove"
                        PROTO = MESSAGE_TEXT.split("proto: ", 1)[1].strip()
                        STATUSES = {"active_onhold": ("active","on_hold"), "expired": ("expired",), "limited": ("limited",)}[GROUP]
                        ADMIN_ARG = None if ADMIN == "*all*" else ADMIN
                        WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ counting target users...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                        COUNT = await asyncio.to_thread(DEF_PROTOCOL_COUNT_TARGETS, MESSAGE_CHATID, STATUSES, ADMIN_ARG, PROTO, ACTION)
                        action_txt = "ADD ➕" if ACTION == "add" else "REMOVE ➖"
                        admin_txt = "All admins" if ADMIN == "*all*" else ADMIN
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>⚠️ Confirm</b>\n\n<b>Admin :</b> <code>{admin_txt}</code>\n<b>Group :</b> <code>{GROUP}</code>\n<b>Action :</b> {action_txt}\n<b>Protocol :</b> <code>{PROTO}</code>\n<b>Target users :</b> <code>{COUNT}</code>\n\n<b>Are you sure?</b>" , reply_markup=KEYBOARD_YES_NO_SIMPLE , parse_mode=enums.ParseMode.HTML)
                        await WAIT.delete()
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID , f"protocol | confirm {ADMIN} {GROUP} {ACTION} {PROTO}")
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Please pick a protocol from the list.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")

                # Step D: confirm + apply
                elif CHECK_STEP.startswith("protocol | confirm ") :
                    if MESSAGE_TEXT == "✅ YES , sure!" :
                        PARTS = CHECK_STEP[len("protocol | confirm "):].strip().split(" ", 3)
                        ADMIN, GROUP, ACTION, PROTO = PARTS[0], PARTS[1], PARTS[2], PARTS[3]
                        STATUSES = {"active_onhold": ("active","on_hold"), "expired": ("expired",), "limited": ("limited",)}[GROUP]
                        ADMIN_ARG = None if ADMIN == "*all*" else ADMIN
                        PROTOS = await asyncio.to_thread(DEF_PROTOCOLS, MESSAGE_CHATID)
                        TAGS = PROTOS.get(PROTO, [])
                        WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ applying... this may take a while.</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                        OK, FAIL, SKIPPED = await DEF_RUN_PROGRESS(client, MESSAGE_CHATID, WAIT, DEF_PROTOCOL_APPLY, MESSAGE_CHATID, PROTO, TAGS, ACTION, STATUSES, ADMIN_ARG)
                        done_txt = "added" if ACTION == "add" else "removed"
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ Done</b>\n\n<b>Protocol <code>{PROTO}</code> {done_txt}.</b>\n<b>✅ Success :</b> <code>{OK}</code>\n<b>⏭ Skipped (already had it) :</b> <code>{SKIPPED}</code>\n<b>❌ Failed :</b> <code>{FAIL}</code>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        await WAIT.delete()
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Cancelled.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


            elif CHECK_STEP.startswith("date") :
                # Step A: pick admin
                if CHECK_STEP == "date | select admin" :
                    if MESSAGE_TEXT.startswith("dateadmin: ") :
                        ADMIN = MESSAGE_TEXT[len("dateadmin: "):].strip()
                        WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ counting time-unlimited users...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                        COUNT = await asyncio.to_thread(DEF_GIVE_DATE_COUNT, MESSAGE_CHATID, ADMIN)
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>📅 Admin <code>{ADMIN}</code> has <code>{COUNT}</code> time-unlimited users.\n\n🔢 How many days to give them? (send a number)</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                        await WAIT.delete()
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID , f"date | days {ADMIN}")
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Please pick an admin.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")

                # Step B: enter days + apply
                elif CHECK_STEP.startswith("date | days ") :
                    ADMIN = CHECK_STEP[len("date | days "):].strip()
                    if not MESSAGE_TEXT.strip().isdigit() :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Please send a number (days).</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                    else :
                        DAYS = int(MESSAGE_TEXT.strip())
                        WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ applying dates...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                        OK, FAIL, SKIPPED = await DEF_RUN_PROGRESS(client, MESSAGE_CHATID, WAIT, DEF_GIVE_DATE_APPLY, MESSAGE_CHATID, ADMIN, DAYS)
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ Done</b>\n\n<b>Gave <code>{DAYS}</code> days to time-unlimited users of <code>{ADMIN}</code>.</b>\n<b>✅ Success :</b> <code>{OK}</code>\n<b>⏭ Skipped (already had date) :</b> <code>{SKIPPED}</code>\n<b>❌ Failed :</b> <code>{FAIL}</code>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        await WAIT.delete()
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


            elif CHECK_STEP.startswith("unlimited") :
                if CHECK_STEP == "unlimited | select admin" :
                    if MESSAGE_TEXT == "🌐 All admins" :
                        ADMIN_ARG = None
                        admin_txt = "All admins"
                    elif MESSAGE_TEXT.startswith("unladmin: ") :
                        ADMIN_ARG = MESSAGE_TEXT[len("unladmin: "):].strip()
                        admin_txt = ADMIN_ARG
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ Please pick an admin.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                        return
                    WAIT = await client.send_message(chat_id=MESSAGE_CHATID, text="<b>⏳️ searching...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
                    TIME_UNL, DATA_UNL = await asyncio.to_thread(DEF_FIND_UNLIMITED, MESSAGE_CHATID, ADMIN_ARG)
                    def _fmt(lst):
                        if not lst:
                            return "—"
                        shown = lst[:50]
                        txt = "\n".join(f"• {n}" for n in shown)
                        if len(lst) > 50:
                            txt += f"\n... (+{len(lst)-50} more)"
                        return txt
                    TEXT = (f"<b>♾ Unlimited users — {admin_txt}</b>\n\n"
                            f"<b>🕰 Time-unlimited (no expire): {len(TIME_UNL)}</b>\n{_fmt(TIME_UNL)}\n\n"
                            f"<b>📊 Data-unlimited (no limit): {len(DATA_UNL)}</b>\n{_fmt(DATA_UNL)}")
                    await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                    await WAIT.delete()
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


            elif CHECK_STEP.startswith("reset") :
                if CHECK_STEP == "reset | toggle" :
                    if MESSAGE_TEXT in ("🟢 Enable reset alert", "🔴 Disable reset alert") :
                        NEW = DEF_RESET_ALERT_TOGGLE()
                        emoji = "🟢 on" if NEW == "on" else "🔴 off"
                        extra = "\n\n<b>First cycle builds a baseline; alerts start from the next check.</b>" if NEW == "on" else ""
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>🔄 Reset alert is now {emoji}</b>{extra}" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                    else :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="🏛" , reply_markup=KEYBOARD_HOME)
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


            elif CHECK_STEP.startswith("search") :
                if CHECK_STEP == "search | wait to send words" :
                    WAIT_MESSGAE = await client.send_message(chat_id=MESSAGE_CHATID, text=f"<b>⏳️ in progress...</b>" , reply_markup=ReplyKeyboardRemove() ,  parse_mode=enums.ParseMode.HTML)
                    TEXT = DEF_SEARCH_USERS(MESSAGE_CHATID , MESSAGE_TEXT)
                    await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)               
                    await WAIT_MESSGAE.delete()


            elif CHECK_STEP.startswith("admins") :

                if CHECK_STEP == "admins | wait to select or add admin" :

                    if re.search(r"- (SUDO|N\.SUDO)", MESSAGE_TEXT) and len(MESSAGES_SPLIT) == 3 :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please select command.</b>" , reply_markup=KEYBOARD_ADMIN , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"admins | selected admin {MESSAGES_SPLIT[0]} {MESSAGES_SPLIT[2]}")
                    
                    elif MESSAGE_TEXT == "➕ Add new admin" :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter new admin username :</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"admins | add admin")

                else :

                    if CHECK_STEP.startswith("admins | selected") :

                        if CHECK_STEP.startswith("admins | selected admin") :
                            ADMIN_NAME , ADMIN_SUDO = STEP_SPLIT[4:]

                            if MESSAGE_TEXT == "🔐 Change pass" :
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>What is the new password of this admin?</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"admins | selected change password {ADMIN_NAME} {ADMIN_SUDO}")
                            
                            elif MESSAGE_TEXT == "🔐 Change sudo" :
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>are you sure?</b>" , reply_markup=KEYBOARD_YES_OR_NOO , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"admins | selected change sudo {ADMIN_NAME} {ADMIN_SUDO}")

                            elif MESSAGE_TEXT == "🗑 Delete admin" :
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>What!!! are you really?</b>" , reply_markup=KEYBOARD_YES_OR_NOO , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"admins | selected delete this {ADMIN_NAME} {ADMIN_SUDO}")
                        
                        else :
        
                            ADMIN_NAME , ADMIN_SUDO = STEP_SPLIT[5:]
                            if CHECK_STEP.startswith("admins | selected change password") :
                                TEXT = DEF_CHANGE_PASSWORD(MESSAGE_CHATID , ADMIN_NAME , ADMIN_SUDO , MESSAGE_TEXT)
                                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")

                            elif CHECK_STEP.startswith("admins | selected change sudo") :
                                if MESSAGE_TEXT == "✅ YES , sure!" :
                                    TEXT = DEF_CHANGE_SUDO(MESSAGE_CHATID,ADMIN_NAME,ADMIN_SUDO,MESSAGE_TEXT)
                                    await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                            
                            elif CHECK_STEP.startswith("admins | selected delete this") :
                                if MESSAGE_TEXT == "✅ YES , sure!" :
                                    TEXT = DEF_DELETE_ADMIN(MESSAGE_CHATID,ADMIN_NAME)
                                    await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                    
                    elif CHECK_STEP.startswith("admins | add admin") :
                        
                        if len(STEP_SPLIT) == 4 :
                            await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter new admin password :</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"admins | add admin {MESSAGE_TEXT}")
                        
                        elif len(STEP_SPLIT) == 5 :
                            ADMIN_NAME = STEP_SPLIT[4] 
                            await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please select admin is sudo or not?</b>" , reply_markup=KEYBOARD_SUDO , parse_mode=enums.ParseMode.HTML)
                            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"admins | add admin {ADMIN_NAME} {MESSAGE_TEXT}")

                        elif len(STEP_SPLIT) == 6 :
                            ADMIN_NAME = STEP_SPLIT[4] 
                            ADMIN_PASS = STEP_SPLIT[5]
                            ADMIN_SUDO = MESSAGE_TEXT == "✅ YES , is sudo!"
                            TEXT = DEF_ADD_ADMIN(MESSAGE_CHATID,ADMIN_NAME,ADMIN_PASS,ADMIN_SUDO)
                            await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                

            elif CHECK_STEP.startswith("users") :

                if CHECK_STEP == "users | wait to select list" :
                
                    if MESSAGE_TEXT in ["✅ Active" , "❌ Disabled" , "🕰 Expired" , "🪫 Limited" , "🔌 On Hold"] :
                        WAIT_MESSGAE = await client.send_message(chat_id=MESSAGE_CHATID, text=f"<b>⏳️ in progress...</b>" , reply_markup=ReplyKeyboardRemove())
                        USERS_LIST = DEF_USERS_LIST_STATUS(MESSAGE_TEXT , MESSAGE_CHATID)
                
                        if not USERS_LIST :
                            await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ I not find any user.</b>" , reply_markup=KEYBOARD_USERS)
                            await WAIT_MESSGAE.delete()
                            return
                
                        else :
                            PDF_NAME = DEF_CREATE_PDF(USERS_LIST)
                            await client.send_document(chat_id=MESSAGE_CHATID , document=PDF_NAME ,caption=f"<b>List of {len(USERS_LIST)} users</b>" ,file_name=f"holderbot.pdf" , reply_markup=KEYBOARD_USERS)
                            await WAIT_MESSGAE.delete()
                            if os.path.exists(PDF_NAME):
                                os.remove(PDF_NAME)   
                
                    elif MESSAGE_TEXT in [ "👀 Online time list" , "📡 Sub Update list"] :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please select time.</b>" , reply_markup=KEYBOARD_LIST_TIMES)
                        CATAGORY = {"📡 Sub Update list": "sub_updated_at", "👀 Online time list": "online_at"}.get(MESSAGE_TEXT)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID, f"users | wait to time {CATAGORY}")                

                    elif MESSAGE_TEXT in ["💻 Clients"] :
                        WAIT_MESSGAE = await client.send_message(chat_id=MESSAGE_CHATID, text=f"<b>⏳️ in progress...</b>" , reply_markup=ReplyKeyboardRemove() ,  parse_mode=enums.ParseMode.HTML)
                        await client.send_message(chat_id=MESSAGE_CHATID , text=DEF_GET_CLIENTS(MESSAGE_CHATID) , reply_markup=KEYBOARD_USERS , parse_mode=enums.ParseMode.HTML)
                        await WAIT_MESSGAE.delete()
                        return   
                else :

                    if CHECK_STEP.startswith("users | wait to time") :
                        

                        if re.match(r'^\d+\s(min|hour|day)$' , MESSAGE_TEXT) :
                            TIME = DEF_CONVERT_TO_SECEND(MESSAGE_TEXT)
                            CATAGORY = STEP_SPLIT[5]
                            WAIT_MESSGAE = await client.send_message(chat_id=MESSAGE_CHATID, text=f"<b>⏳️ in progress...</b>" , reply_markup=ReplyKeyboardRemove())
                            USERS_LIST_BACK ,  NOT_USER_LIST = DEF_USERS_TIME_LIST(MESSAGE_CHATID , CATAGORY , TIME)
                            
                            if not USERS_LIST_BACK :
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ I not find any user.</b>" , reply_markup=KEYBOARD_LIST_TIMES)
                            else :
                                USERS_LIST_BACK_PDF = DEF_CREATE_PDF(USERS_LIST_BACK)
                                await client.send_document(chat_id=MESSAGE_CHATID , document=USERS_LIST_BACK_PDF ,caption=f"<b>List of {len(USERS_LIST_BACK)} users</b>" ,file_name=f"holderbot.pdf" , reply_markup=KEYBOARD_LIST_TIMES)
                                if os.path.exists(USERS_LIST_BACK_PDF):
                                    os.remove(USERS_LIST_BACK_PDF)
                            
                            if not NOT_USER_LIST :
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>❌ I not find any user.</b>" , reply_markup=KEYBOARD_LIST_TIMES)
                            else :
                                NOT_IN_LIST_PDF = DEF_CREATE_PDF(NOT_USER_LIST)
                                await client.send_document(chat_id=MESSAGE_CHATID , document=NOT_IN_LIST_PDF ,caption=f"<b>other List of {len(NOT_USER_LIST)} users</b>" ,file_name=f"holderbot.pdf" , reply_markup=KEYBOARD_LIST_TIMES)
                                if os.path.exists(NOT_IN_LIST_PDF):
                                    os.remove(NOT_IN_LIST_PDF)
                            
                            await WAIT_MESSGAE.delete()


            elif CHECK_STEP.startswith("nodes") :

                if CHECK_STEP == "nodes | wait to select node" :
                    
                    if re.match(r"\(\s*(\d+)\s*\)\s*([^-]+)\s*-\s*([^-]+)", MESSAGE_TEXT):
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>You have chosen {MESSAGES_SPLIT[3]} server.\nwhat operation do you need?</b>" , reply_markup=KEYBOARD_NODE)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"nodes | select node {MESSAGES_SPLIT[1]}")

                else :

                    if CHECK_STEP.startswith("nodes | select node") :
                        NODE_ID = int(STEP_SPLIT[4])

                        if MESSAGE_TEXT == "🔏 Usage Coefficient" :
                            TEXT = "<b>Plase enter a float (0.0) number.\nlike this :</b> <code>0.4</code> , <code>1.2</code> , <code>3.5</code> , <code>8.0</code>"
                            await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"nodes | Usage Coefficient {NODE_ID}")
                            
                        else :

                            if MESSAGE_TEXT == "📊 Status" :
                                TEXT = DEF_STASE_NODE(MESSAGE_CHATID , NODE_ID)
                            elif MESSAGE_TEXT == "✅ Activate" :
                                TEXT = DEF_ACTIVE_NODE(MESSAGE_CHATID , NODE_ID)
                            elif MESSAGE_TEXT == "⚡️ Reconnect" :
                                TEXT = DEF_RECONNECT_NODE(MESSAGE_CHATID , NODE_ID)
                            elif MESSAGE_TEXT == "❌ Disable" :
                                TEXT = DEF_DISABLED_NODE(MESSAGE_CHATID , NODE_ID)

                            await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_NODE , parse_mode=enums.ParseMode.HTML)

                    else :

                        if CHECK_STEP.startswith("nodes | Usage Coefficient") :
                            NODE_ID = int(STEP_SPLIT[4])
                            
                            if len(MESSAGES_SPLIT) == 1 and re.match(r'^-?\d+\.\d+$', MESSAGE_TEXT) :
                                TEXT = DEF_USAGE_COEFFICIENT(float(MESSAGE_TEXT) , MESSAGE_CHATID , NODE_ID)
                                await client.send_message(chat_id=MESSAGE_CHATID , text=TEXT , reply_markup=KEYBOARD_NODE , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"nodes | select node {NODE_ID}")


            elif CHECK_STEP.startswith("monitoring") :

                if CHECK_STEP == "monitoring | wait to select command" :

                    if MESSAGE_TEXT == "🔴 Disable monitoring" :
                        CHANGE = DEF_CHANGE_NODE_STATUS(MESSAGE_CHATID,"off")
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>✅ Your Monitoring is disabled.</b>" , reply_markup=KEYBOARD_OFF_MONITORING , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )

                    elif MESSAGE_TEXT == "🟢 Monitoring activation" :
                        CHANGE = DEF_CHANGE_NODE_STATUS(MESSAGE_CHATID,"on")
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>✅ Your Monitoring is activated.</b>" , reply_markup=KEYBOARD_ON_MONITORING , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                    
                    elif MESSAGE_TEXT == "⏱ Normal timer" :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Enter the time you want in seconds.</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"monitoring | timer check_normal")

                    elif MESSAGE_TEXT == "⏱ Error timer" :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Enter the time you want in seconds.</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"monitoring | timer check_error")
                
                else :

                    if CHECK_STEP.startswith("monitoring | timer") :
                        DB_ROW = STEP_SPLIT[3]
                        if len(MESSAGES_SPLIT) == 1 and MESSAGE_TEXT.isnumeric() :
                            CHANGE = DEF_NODE_STATUS(MESSAGE_CHATID , DB_ROW , MESSAGE_TEXT)
                            await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ Your {DB_ROW} timer is changed.</b>" , reply_markup=KEYBOARD_ON_MONITORING , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"monitoring | wait to select command")
                

            elif CHECK_STEP.startswith("templates") :

                if CHECK_STEP == "templates | wait to select command" :

                    if re.match(r'(\w+) - ([0-9.]+) GB (\d+) days' , MESSAGE_TEXT) :
                        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>You want delete {MESSAGES_SPLIT[0]} template?</b>" , reply_markup=KEYBOARD_YES_OR_NOO , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"templates | delete {MESSAGES_SPLIT[0]}")

                    elif MESSAGE_TEXT == "➕ Add new tempalte" :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter template name.\n(just text , no space no number no icon!)\nlike :</b> <code>Test</code> ,<code>Ali</code>, <code>Bulk</code>, <code>Free</code>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"templates | add template")

                else :

                    if CHECK_STEP.startswith("templates | delete") :
                        TEMPLATE_NAME = STEP_SPLIT[3]
                        if MESSAGE_TEXT == "✅ YES , sure!" :
                            CHANGE = DEF_TEMPLATES_DELETE(TEMPLATE_NAME)
                            await client.send_message(chat_id=MESSAGE_CHATID , text="<b>✅ Your template is deleted.</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")

                    else :

                        if CHECK_STEP.startswith("templates | add template") :
                            print(STEP_SPLIT)
                            if len(STEP_SPLIT) == 4 and len(MESSAGES_SPLIT) == 1 and re.match("^[A-Za-z]+$" , MESSAGE_TEXT) :
                                if DEF_CHECK_TEMPLATES_NAME(MESSAGE_TEXT) :
                                    return
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter data limit (GB).\nlike : <code>25.5</code>, <code>15</code>, <code>0.5</code>, <code>100</code></b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"templates | add template {MESSAGE_TEXT}")
                            
                            elif len(STEP_SPLIT) == 5 and len(MESSAGES_SPLIT) == 1 and re.match(r"^\d*\.?\d+$", MESSAGE_TEXT):
                                TEMPLATE_NAME = STEP_SPLIT[4]
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter date limit (days).\nLike : <code>1</code>, <code>15</code>, <code>75</code>, <code>150</code></b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"templates | add template {TEMPLATE_NAME} {float(MESSAGE_TEXT)}")

                            elif len(STEP_SPLIT) == 6 and len(MESSAGES_SPLIT) == 1 and MESSAGE_TEXT.isnumeric() :
                                TEMPLATE_NAME , TEMPLATE_DATA = STEP_SPLIT[4:]
                                global INBOUNDS_ALL , INBOUNDS_SELECT
                                INBOUNDS , INBOUNDS_ALL ,INBOUNDS_SELECT = DEF_GET_INBOUNDS(MESSAGE_CHATID)
                                KEYBOARD_INBOUNDS = KEYBOARD_ALL_INBOUNDS(INBOUNDS_ALL , INBOUNDS_SELECT , None , "templates")
                                await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>Please select inbounds :</b>" , reply_markup=KEYBOARD_INBOUNDS , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"templates | add template {TEMPLATE_NAME} {TEMPLATE_DATA} {MESSAGE_TEXT}")


            elif CHECK_STEP.startswith("create") :

                if CHECK_STEP == "create | wait to select command" :

                    if MESSAGE_TEXT == "🚀 Manual" :
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter username :</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"create | manual")

                    elif re.match(r'(\w+) - ([0-9.]+) GB (\d+) days' , MESSAGE_TEXT) :
                        TEMPLATE_NAME = MESSAGES_SPLIT[0]
                        await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter username :</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"create | select {TEMPLATE_NAME}")
                    
                else :

                    if CHECK_STEP.startswith("create | select") :
                        TEMPLATE_NAME = STEP_SPLIT[3]
                        
                        if len(MESSAGES_SPLIT) == 1 and len(STEP_SPLIT) == 4 :
                            await client.send_message(chat_id=MESSAGE_CHATID , text="<b>how many do you want?</b>" , reply_markup=KEYBOARD_CREATE_MUCH , parse_mode=enums.ParseMode.HTML)
                            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"create | select {TEMPLATE_NAME} {MESSAGE_TEXT}")
                        
                        elif len(MESSAGES_SPLIT) == 1 and len(STEP_SPLIT) == 5 and MESSAGE_TEXT.isnumeric() :
                            USERNAME = STEP_SPLIT[4]
                            NAME , DATA , DATE , PROXIES , INBOUNDS = DEF_TEMPLATES_DATA_ALL(TEMPLATE_NAME)
                            if int(MESSAGE_TEXT) == 1 :
                                USER_SUB = DEF_CREATE_USER(MESSAGE_CHATID , USERNAME , DATA , DATE , json.loads(PROXIES) , json.loads(INBOUNDS))
                                if not "❌" in USER_SUB :
                                    QRCODE_IMG = DEF_CREATE_QRCODE(USER_SUB)
                                    #await client.send_photo(chat_id=MESSAGE_CHATID , photo=QRCODE_IMG,caption=DEF_SEND_QR_TEXT(USER_SUB , USERNAME , DATA , DATE) , reply_markup=KEYBOARD_HOME)
                                    #await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ <code>{USERNAME}</code> | {DATA} GB | {DATE} Days</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                                    await client.send_photo(chat_id=MESSAGE_CHATID, photo=QRCODE_IMG, caption=f"<b>👨🏻‍💻 <code>{USERNAME}</code> \n {DATA} GB | {DATE} Days </br></br> \n{USER_SUB} </br></b>")
                                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                                else :
                                    await client.send_message(chat_id=MESSAGE_CHATID , text=USER_SUB , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                            else :
                                USERNAMES = DEF_USERNAME_STARTER(USERNAME , int(MESSAGE_TEXT))
                                for USERNAME in USERNAMES :
                                    USER_SUB = DEF_CREATE_USER(MESSAGE_CHATID , USERNAME , DATA , DATE , json.loads(PROXIES) , json.loads(INBOUNDS))
                                    if not "❌" in USER_SUB :
                                        QRCODE_IMG = DEF_CREATE_QRCODE(USER_SUB)
                                        #await client.send_photo(chat_id=MESSAGE_CHATID , photo=QRCODE_IMG,caption=DEF_SEND_QR_TEXT(USER_SUB , USERNAME , DATA , DATE) , reply_markup=ReplyKeyboardRemove())
                                        #await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ <code>{USERNAME}</code> | {DATA} GB | {DATE} Days</b>" , reply_markup=ReplyKeyboardRemove() , parse_mode=enums.ParseMode.HTML)
                                        await client.send_photo(chat_id=MESSAGE_CHATID, photo=QRCODE_IMG, caption=f"<b>👨🏻‍💻 <code>{USERNAME}</code> \n {DATA} GB | {DATE} Days </br></br> \n{USER_SUB} </br></b>")
                                    else :
                                        await client.send_message(chat_id=MESSAGE_CHATID , text=USER_SUB , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                                        break
                                await client.send_message(chat_id=MESSAGE_CHATID , text=f"🏛" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")

                    else :

                        if CHECK_STEP.startswith("create | manual") :

                            if len(MESSAGES_SPLIT) == 1 and len(STEP_SPLIT) == 3 and len(MESSAGE_TEXT) > 2 :
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter data limit (GB).\nlike : <code>25.5</code>, <code>15</code>, <code>0.5</code>, <code>100</code></b></b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"create | manual {MESSAGE_TEXT}")

                            elif len(MESSAGES_SPLIT) == 1 and len(STEP_SPLIT) == 4 and re.match(r"^\d*\.?\d+$", MESSAGE_TEXT):
                                USERNAME = STEP_SPLIT[3]
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>Please enter date limit (days).\nLike : <code>1</code>, <code>15</code>, <code>75</code>, <code>150</code></b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"create | manual {USERNAME} {MESSAGE_TEXT}")
                            
                            elif len(MESSAGES_SPLIT) == 1 and len(STEP_SPLIT) == 5 and MESSAGE_TEXT.isnumeric() :
                                USERNAME , DATA_LIMIT = STEP_SPLIT[3:]
                                await client.send_message(chat_id=MESSAGE_CHATID , text="<b>how many do you want?</b>" , reply_markup=KEYBOARD_CANCEL , parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"create | manual {USERNAME} {DATA_LIMIT} {MESSAGE_TEXT}")

                            elif len(MESSAGES_SPLIT) == 1 and len(STEP_SPLIT) == 6 and MESSAGE_TEXT.isnumeric() :
                                USERNAME , DATA_LIMIT , DATE_LIMIT = STEP_SPLIT[3:]
                                global INBOUNDS__ALL , INBOUNDS__SELECT
                                INBOUNDS , INBOUNDS__ALL ,INBOUNDS__SELECT = DEF_GET_INBOUNDS(MESSAGE_CHATID)
                                KEYBOARD_INBOUNDS = KEYBOARD_ALL_INBOUNDS(INBOUNDS__ALL , INBOUNDS__SELECT , None , "create")
                                await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>Please select inbounds :</b>" , reply_markup=KEYBOARD_INBOUNDS,  parse_mode=enums.ParseMode.HTML)
                                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,f"create | manual {USERNAME} {DATA_LIMIT} {DATE_LIMIT} {MESSAGE_TEXT}")


            elif CHECK_STEP.startswith("message") :
                
                if CHECK_STEP == "message | wait to select command" :
                    if MESSAGE_TEXT == "👀 change status" :
                        await client.send_message(chat_id=MESSAGE_CHATID , text=DEF_CHANGE_MESSAGER_STATUS(MESSAGE_CHATID) , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML , disable_web_page_preview=True )
                        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


@app.on_callback_query(filters.regex(r'^templates'))
async def handle_callback_create(client: Client, query: CallbackQuery ):
    
    MESSAGE_CHATID = query.message.chat.id
    CALLBACK_DATA = query.data
    CHECK_STEP = DEF_CHECK_STEP(MESSAGE_CHATID)
    STEP_SPLIT = CHECK_STEP.strip().split(" ")
    global INBOUNDS_ALL , INBOUNDS_SELECT
        
    if CALLBACK_DATA.startswith("templates tag") :

        SELECTED_TAG = CALLBACK_DATA[14:]
        KEYBOARD_INBOUNDS = KEYBOARD_ALL_INBOUNDS(INBOUNDS_ALL, INBOUNDS_SELECT, SELECTED_TAG , "templates")
        await query.edit_message_text(text="<b>Please select inbounds :</b>" , reply_markup=KEYBOARD_INBOUNDS , parse_mode=enums.ParseMode.HTML)

    elif CALLBACK_DATA == "templates yes" :

        INBOUNDS , PUCH1 , PUCH2  = DEF_GET_INBOUNDS(MESSAGE_CHATID)
        INBOUND_FINAL , PROXIES_FINAL = DEF_SELECT_INBOUNDS_AND_PROXIES(INBOUNDS , INBOUNDS_SELECT)
        TEMPLATE_NAME , TEMPLATE_DATA , TEMPLATE_DATE = STEP_SPLIT[4:]
        CHANGE = DEF_TEMPLATES_ADD(TEMPLATE_NAME, TEMPLATE_DATA, TEMPLATE_DATE, PROXIES_FINAL, INBOUND_FINAL)
        await query.message.delete()
        await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ Template is added.</b>" , reply_markup=KEYBOARD_HOME)
        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")

    elif CALLBACK_DATA == "templates no" :

        await query.message.delete()
        await client.send_message(chat_id=MESSAGE_CHATID , text=f"🏛" , reply_markup=KEYBOARD_HOME)
        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


@app.on_callback_query(filters.regex(r'^create'))
async def handle_callback_create(client: Client, query: CallbackQuery ):
    
    MESSAGE_CHATID = query.message.chat.id
    CALLBACK_DATA = query.data
    CHECK_STEP = DEF_CHECK_STEP(MESSAGE_CHATID)
    STEP_SPLIT = CHECK_STEP.strip().split(" ")
    global INBOUNDS__ALL , INBOUNDS__SELECT
        
    if CALLBACK_DATA.startswith("create tag") :

        SELECTED_TAG = CALLBACK_DATA[11:]
        KEYBOARD_INBOUNDS = KEYBOARD_ALL_INBOUNDS(INBOUNDS__ALL, INBOUNDS__SELECT, SELECTED_TAG , "create")
        await query.edit_message_text(text="<b>Please select inbounds :</b>" , reply_markup=KEYBOARD_INBOUNDS , parse_mode=enums.ParseMode.HTML)

    elif CALLBACK_DATA == "create yes" :

        INBOUNDS , PUCH1 , PUCH2  = DEF_GET_INBOUNDS(MESSAGE_CHATID)
        INBOUND_FINAL , PROXIES_FINAL = DEF_SELECT_INBOUNDS_AND_PROXIES(INBOUNDS , INBOUNDS__SELECT)
        USERNAME , DATA_LIMIT , DATE_LIMIT , HOW_MANY = STEP_SPLIT[3:]
        if int(HOW_MANY) == 1 :
            USER_SUB = DEF_CREATE_USER(MESSAGE_CHATID , USERNAME , DATA_LIMIT , DATE_LIMIT , PROXIES_FINAL , INBOUND_FINAL)
            await query.message.delete()
            if not "❌" in USER_SUB :
                QRCODE_IMG = DEF_CREATE_QRCODE(USER_SUB)
                #await client.send_photo(chat_id=MESSAGE_CHATID , photo=QRCODE_IMG,caption=DEF_SEND_QR_TEXT(USER_SUB , USERNAME , DATA_LIMIT , DATE_LIMIT) , reply_markup=KEYBOARD_HOME)
                #await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ <code>{USERNAME}</code> | {DATA_LIMIT} GB | {DATE_LIMIT} Days</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                await client.send_photo(chat_id=MESSAGE_CHATID, photo=QRCODE_IMG, caption=f"<b>👨🏻‍💻 <code>{USERNAME}</code> \n {DATA_LIMIT} GB | {DATE_LIMIT} Days </br></br> \n{USER_SUB} </br></b>")
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
            else :
                await client.send_message(chat_id=MESSAGE_CHATID , text=USER_SUB , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
        else :
            USERNAMES = DEF_USERNAME_STARTER(USERNAME , int(HOW_MANY))
            for USERNAME in USERNAMES :
                USER_SUB = DEF_CREATE_USER(MESSAGE_CHATID , USERNAME , DATA_LIMIT , DATE_LIMIT , PROXIES_FINAL , INBOUND_FINAL)
                if not "❌" in USER_SUB :
                    QRCODE_IMG = DEF_CREATE_QRCODE(USER_SUB)
                    #await client.send_photo(chat_id=MESSAGE_CHATID , photo=QRCODE_IMG,caption=DEF_SEND_QR_TEXT(USER_SUB , USERNAME , DATA_LIMIT , DATE_LIMIT) , reply_markup=ReplyKeyboardRemove())
                    #await client.send_message(chat_id=MESSAGE_CHATID , text=f"<b>✅ <code>{USERNAME}</code> | {DATA_LIMIT} GB | {DATE_LIMIT} Days</b>" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                    await client.send_photo(chat_id=MESSAGE_CHATID, photo=QRCODE_IMG, caption=f"<b>👨🏻‍💻 <code>{USERNAME}</code> \n {DATA_LIMIT} GB | {DATE_LIMIT} Days </br></br> \n{USER_SUB} </br></b>")
                else :
                    await client.send_message(chat_id=MESSAGE_CHATID , text=USER_SUB , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
                    UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
                    break
            await client.send_message(chat_id=MESSAGE_CHATID , text=f"🏛" , reply_markup=KEYBOARD_HOME , parse_mode=enums.ParseMode.HTML)
            UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")
        
    elif CALLBACK_DATA == "create no" :

        await query.message.delete()
        await client.send_message(chat_id=MESSAGE_CHATID , text=f"🏛" , reply_markup=KEYBOARD_HOME)
        UPDATE_STEP = DEF_UPDATE_STEP(MESSAGE_CHATID,"None")


@app.on_callback_query(filters.regex(r'^user info'))
async def handle_callback_user_info(client: Client, query: CallbackQuery):
    CHECK_BOSS = DEF_CHECK_BOSS(query.from_user.id)
    if CHECK_BOSS :
        CALLBACK_DATA = query.data
        PANEL_USER, PANEL_PASS, PANEL_DOMAIN = DEF_IMPORT_DATA (query.from_user.id)
        PANEL_TOKEN = DEF_PANEL_ACCESS(PANEL_USER, PANEL_PASS, PANEL_DOMAIN)
        MESSAGES_SPLIT = CALLBACK_DATA.strip().split(" ")
        CB_USERNAME = MESSAGES_SPLIT[3]
        
        if CALLBACK_DATA.startswith("user info QRCODE") :
            URL = f"{PANEL_DOMAIN}/api/user/{CB_USERNAME}"
            RESPONCE = requests.get(url=URL , headers=PANEL_TOKEN , verify=False)
            if RESPONCE.status_code == 200 :
                RESPONCE_DATA = json.loads(RESPONCE.text)
            else :
                await query.answer(text=f"<b>❌ I can'n find user.</b>")
                return
            RD_SUB_URL = RESPONCE_DATA.get("subscription_url")
            QRCODE_IMG = DEF_CREATE_QRCODE(RD_SUB_URL)
            await client.send_photo(chat_id=query.from_user.id, photo=QRCODE_IMG,caption=f"<pre>{RD_SUB_URL}</pre>")


        elif CALLBACK_DATA.startswith("user info UPDATE") or CALLBACK_DATA.startswith("user info NO") :
            try :
                TEXT , KEYBOARD_UPDATE_STASE = DEF_STASE_USER (query.from_user.id , CB_USERNAME , KEYBOARD_HOME)
                await query.edit_message_text(text=TEXT , reply_markup=KEYBOARD_UPDATE_STASE)
                return 
            except MessageNotModified :
                await query.answer("your info is not changed.")
                return
            
        elif CALLBACK_DATA.startswith("user info DELETE") :
            if CALLBACK_DATA.startswith("user info DELETE_SURE") :
                URL = f"{PANEL_DOMAIN}/api/user/{CB_USERNAME}"
                RESPONCE = requests.delete(url=URL , headers=PANEL_TOKEN , verify=False)
                if RESPONCE.status_code == 200 :
                    RESPONCE_DATA = json.loads(RESPONCE.text)
                else :
                    await query.edit_message_text(text=f"<b>❌ I can'n find user.</b>")
                    return
                await query.edit_message_text(text=f"<b>✅ User is deleted.</b>")
            else :
                KEYBOARD_DELETE = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ YES", callback_data=f'user info DELETE_SURE {CB_USERNAME}'),
                    InlineKeyboardButton("🚫 NO", callback_data=f'user info NO {CB_USERNAME}')]])                
                await query.edit_message_text(text=f"<b>Are you sure delete <code>{CB_USERNAME}</code> user ?!</b>", reply_markup=KEYBOARD_DELETE)


app.run()
