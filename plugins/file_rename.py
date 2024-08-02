@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    try:
        new_name = update.message.text
        new_filename = new_name.split(":-")[1]
        file_path = f"downloads/{new_filename}"
        file = update.message.reply_to_message

        # Update the message to reflect the new text
        ms = await update.message.edit("anime beast tamil trying to downloading....")

        # Download the file
        path = await bot.download_media(
            message=file,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("anime beast tamil download started....", ms, time.time())
        )

        # Extract metadata (if available)
        metadata = extractMetadata(createParser(file_path))
        duration = 0
        if metadata and metadata.has("duration"):
            duration = metadata.get('duration').seconds

        # Get user-defined caption and thumbnail (if available)
        user_id = int((link unavailable))
        c_caption = await db.get_caption(user_id)
        c_thumb = await db.get_thumbnail(user_id)

        # Prepare the caption
        if c_caption:
            try:
                caption = c_caption.format(
                    filename=new_filename,
                    filesize=humanbytes(file.media.file_size),
                    duration=convert(duration)
                )
            except Exception as e:
                await ms.edit(f"Caption formatting error: {e}")
                return
        else:
            caption = f"{new_filename}"

        # Prepare the thumbnail
        ph_path = None
        if file.media.thumbs or c_thumb:
            if c_thumb:
                ph_path = await bot.download_media(c_thumb)
            else:
                ph_path = await bot.download_media(file.media.thumbs[0].file_id)

            # Add watermark to the thumbnail (if it exists)
            if ph_path:
                watermark_path = 'downloads/watermarked_thumbnail.jpg'
                try:
                    add_watermark(ph_path, "@anime_beast_tamil", watermark_path)
                    ph_path = watermark_path
                except Exception as e:
                    print(f"Watermarking error: {e}")

        # Upload the file
        await ms.edit("anime beast tamil trying to uploading....")
        file_type = update.data.split("_")[1]
        try:
            if file_type == "document":
                await bot.send_document(
                    (link unavailable),
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
                    (link unavailable),
                    video=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload started....", ms, time.time())
                )
            elif file_type == "audio":
                await bot.send_audio(
                    (link unavailable),
                    audio=file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload started....", ms, time.time())
                )
        except Exception as e:
            await ms.edit(f"Upload error: {e}")
            os.remove(file_path)
            if ph_path:
                os.remove(ph_path)
    except Exception as e:
        await ms.edit(f"An error occurred: {e}")
