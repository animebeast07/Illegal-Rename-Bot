from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
from asyncio import sleep
from PIL import Image, ImageDraw
import os

# Ensure the 'downloads' directory exists
if not os.path.exists('downloads'):
    os.makedirs('downloads')

def add_watermark(image_path, watermark_text, output_path):
    with Image.open(image_path) as img:
        watermark = Image.new("RGBA", img.size)
        watermark_draw = ImageDraw.Draw(watermark)
        watermark_draw.text((10, 10), watermark_text, fill=(255, 255, 255, 128))  # Add watermark
        watermarked = Image.alpha_composite(img.convert("RGBA"), watermark)
        watermarked.save(output_path, "PNG")

@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name
    if file.file_size > 2000 * 1024 * 1024:
        return await message.reply_text("Sorry, this bot doesn't support files larger than 2GB. Contact the bot developer.")

    try:
        await message.reply_text(
            text=f"**Please enter new filename...**\n\n**Old Filename** :- `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**Please enter new filename...**\n\n**Old Filename** :- `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {e}")

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()

        button = [[InlineKeyboardButton("Document", callback_data="upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("Video", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("Audio", callback_data="upload_audio")])
        await message.reply(
            text=f"**Select the output file type**\n**• Filename :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )

@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    data = update.data.split("_")
    file_type = data[1] if len(data) > 1 else "document"
    new_name = update.message.reply_to_message.text.split(":-")[-1].strip()
    file_path = f"downloads/{new_name}"
    file = update.message.reply_to_message

    ms = await update.message.edit("Anime beast tamil Trying to download...")
    try:
        path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=("Download started...", ms, time.time()))
    except Exception as e:
        return await ms.edit(f"Error during download: {e}")

    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata and metadata.has("duration"):
            duration = metadata.get('duration').seconds
    except Exception as e:
        print(f"Error extracting metadata: {e}")

    ph_path = None
    user_id = int(update.message.chat.id)
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    if c_caption:
        try:
            caption = c_caption.format(filename=new_name, filesize=humanbytes(media.file_size), duration=convert(duration))
        except Exception as e:
            return await ms.edit(f"Caption error: {e}")
    else:
        caption = f"**{new_name}**"

    if media.thumbs or c_thumb:
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
        else:
            ph_path = await bot.download_media(media.thumbs[0].file_id)
        with Image.open(ph_path) as img:
            img = img.convert("RGB").resize((320, 320))
            img.save(ph_path, "JPEG")
        watermark_text = "Anime Beast Tamil"
        watermark_path = "downloads/watermarked_" + new_name
        add_watermark(ph_path, watermark_text, watermark_path)
        ph_path = watermark_path

    await ms.edit("Anime beast tamil Trying to upload...")
    try:
        if file_type == "document":
            await bot.send_document(
                update.message.chat.id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("Upload started...", ms, time.time())
            )
        elif file_type == "video":
            await bot.send_video(
                update.message.chat.id,
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload started...", ms, time.time())
            )
        elif file_type == "audio":
            await bot.send_audio(
                update.message.chat.id,
                audio=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload started...", ms, time.time())
            )
    except Exception as e:
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
        return await ms.edit(f"Error during upload: {e}")

    await ms.delete()
    os.remove(file_path)
    if ph_path:
        os.remove(ph_path)
