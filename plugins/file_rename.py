
@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    new_name = update.message.text
    new_filename = new_name.split(":-")[1]
    file_path = f"downloads/{new_filename}"
    file = update.message.reply_to_message

    # Update the message to reflect the new text
    ms = await update.message.edit("anime beast tamil trying to downloading....")
    try:
        path = await bot.download_media(
            message=file,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("anime beast tamil download started....", ms, time.time())
        )
    except Exception as e:
        return await ms.edit(f"Download error: {e}")

    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata and metadata.has("duration"):
            duration = metadata.get('duration').seconds
    except Exception as e:
        print(f"Metadata extraction error: {e}")

    ph_path = None
    user_id = int(update.message.chat.id)
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    if c_caption:
        try:
            caption = c_caption.format(
                filename=new_filename,
                filesize=humanbytes(media.file_size),
                duration=convert(duration)
            )
        except Exception as e:
            return await ms.edit(f"Caption formatting error: {e}")
    else:
        caption = f"{new_filename}"

    if media.thumbs or c_thumb:
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
        else:
            ph_path = await bot.download_media(media.thumbs[0].file_id)

        # Add watermark to the thumbnail if it exists
        if ph_path:
            watermark_path = 'downloads/watermarked_thumbnail.jpg'
            try:
                add_watermark(ph_path, "@anime_beast_tamil", watermark_path)
                ph_path = watermark_path
            except Exception as e:
                print(f"Watermarking error: {e}")

    await ms.edit("anime beast tamil trying to uploading....")
    file_type = update.data.split("_")[1]
    try:
        if file_type == "document":
            await bot.send_document(
                update.message.chat.id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("Upload started....", ms, time.time())
            )
        elif file_type == "video":
            # Add watermark to the video
            watermarked_video_path = 'downloads/watermarked_video.mp4'
            try:
                add_watermark_to_video(file_path, watermarked_video_path)
                file_path = watermarked_video_path
            except Exception as e:
                print(f"Video watermarking error: {e}")

            await bot.send_video(
                update.message.chat.id,
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload started....", ms, time.time())
            )
        elif file_type == "audio":
            await bot.send_audio(
                update.message.chat.id,
                audio=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload started....", ms, time.time())
            )
    except Exception as e:
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
