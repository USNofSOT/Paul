# Remove voyages, and hosted on message deletion
@bot.event
async def on_message_delete(message):
    if message.channel.id == int(voyage_log_channel_id):
            log_id = message.id
            host_id = message.author.id
            participant_ids = [user.id for user in message.mentions]

            # Decrement hosted count
            db_manager.decrement_count(host_id, "hosted_count")
            db_manager.remove_hosted_entry( log_id)

            # Decrement voyage counts for participants
            for participant_id in participant_ids:
                db_manager.decrement_count(participant_id, "voyage_count")
                print(f"Voyage count deleted: {participant_id}")
            # Remove entries from VoyageLog table (if necessary)
            db_manager.remove_voyage_log_entries(log_id)
            print(f"Voyage log deleted: {log_id}")
    else:
        # allows bot to process commands in messages
        await bot.process_commands(message)