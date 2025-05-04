import discord
from discord.ext import commands
import asyncio
import random

intents = discord.Intents.all()

client = discord.Client(intents=intents)

BOT_PREFIX = "?"

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    print(f'Bot ID: {client.user.id}')
    print('------')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.startswith(BOT_PREFIX):
        return

    if message.guild is None and message.content[len(BOT_PREFIX):].split(' ')[0] in ['nuke', 'clear', 'webhookspam']:
         await message.channel.send("This command can only be used in a server.")
         return

    args = message.content[len(BOT_PREFIX):].split(' ')
    command = args[0].lower()

    if command == 'help':
        embed = discord.Embed(
            title="Prada Wizz Bot Help Menu",
            description="Here are all the available commands:",
            color=0x3498db
        )
        
        embed.add_field(
            name="📋 General Commands",
            value=f"`{BOT_PREFIX}help` - Shows this help menu\n"
                  f"`{BOT_PREFIX}ping` - Check the bot's latency\n"
                  f"`{BOT_PREFIX}echo <message>` - Repeat the message you send",
            inline=False
        )
        
        embed.add_field(
            name="🛡️ Moderation/Utility",
            value=f"`{BOT_PREFIX}clear <amount>` - Clear a specified number of messages (requires Manage Messages)\n"
                  f"`{BOT_PREFIX}nuke` - **Deletes ALL channels and roles** (requires Admin)\n"
                  f"`{BOT_PREFIX}wizz <name> <amount>` - **Deletes ALL channels/roles, then creates new ones** (requires Admin)",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Spam Commands (Use Responsibly!)",
            value=f"`{BOT_PREFIX}spam <message> <amount>` - Spams a message (requires Send Messages). Max 50\n"
                  f"`{BOT_PREFIX}webhookspam <message> <amount>` - Spams via a temporary webhook (requires Manage Webhooks). Max 50",
            inline=False
        )
        
        embed.add_field(
            name="😈 Troll Commands",
            value=f"`{BOT_PREFIX}rickroll` - Never gonna give you up...\n"
                  f"`{BOT_PREFIX}fakeping` - Simulate a high ping\n"
                  f"`{BOT_PREFIX}reverse <message>` - Reverses your message",
            inline=False
        )
        
        embed.set_footer(text="/\\_/\\\n( o.o )\n > ^ <")
        
        await message.channel.send(embed=embed)

    elif command == 'spam':
        if not message.channel.permissions_for(message.guild.me).send_messages:
            await message.channel.send("I don't have permission to send messages here.")
            return

        if len(args) < 3:
            await message.channel.send(f'Usage: {BOT_PREFIX}spam <message> <amount>')
            return

        try:
            amount = int(args[-1])
            msg = ' '.join(args[1:-1])
            if not msg:
                 await message.channel.send(f'Usage: {BOT_PREFIX}spam <message> <amount>')
                 return
        except ValueError:
            await message.channel.send('Amount must be a number.')
            return
        except IndexError:
             await message.channel.send(f'Usage: {BOT_PREFIX}spam <message> <amount>')
             return

        amount = min(amount, 50)

        for i in range(amount):
            try:
                await message.channel.send(msg)
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                await message.channel.send("I lost permission to send messages.")
                break
            except discord.HTTPException as e:
                await message.channel.send(f"An error occurred: {e}. Stopping spam.")
                break

    elif command == 'nuke':
        if not message.guild.me.guild_permissions.manage_channels:
             await message.channel.send("I need the 'Manage Channels' permission to execute the nuke.")
             return
        if not message.guild.me.guild_permissions.manage_roles:
             await message.channel.send("I need the 'Manage Roles' permission to execute the nuke.")
             return
        if not message.author.guild_permissions.administrator:
             await message.channel.send("You need Administrator permissions to use this command.")
             return

        guild = message.guild
        author = message.author
        reason = f'Server nuked by {author} (ID: {author.id})'

        await message.channel.send(f"**WARNING:** Nuke initiated by {author.mention}. Deleting all channels and roles...")
        print(f"--- Nuke initiated by {author} in guild {guild.name} ({guild.id}) ---")

        print("Starting concurrent deletion of channels and roles...")

        async def _delete_channel_task(channel_to_delete):
            try:
                await channel_to_delete.delete(reason=reason)
                print(f"  Deleted channel: #{channel_to_delete.name} ({channel_to_delete.id})")
                return True
            except discord.Forbidden:
                print(f"  Failed to delete channel #{channel_to_delete.name}: Missing Permissions")
                return False
            except discord.HTTPException as e:
                print(f"  Failed to delete channel #{channel_to_delete.name}: {e} (HTTP {e.status})")
                if e.status == 429: await asyncio.sleep(e.retry_after if hasattr(e, 'retry_after') else 2)
                return False
            except Exception as e:
                 print(f"  Unexpected error deleting channel #{channel_to_delete.name}: {e}")
                 return False

        async def _delete_role_task(role_to_delete, bot_top_role_pos):
            if role_to_delete.is_default() or role_to_delete.is_managed() or role_to_delete.position >= bot_top_role_pos:
                return None
            try:
                await role_to_delete.delete(reason=reason)
                print(f"  Deleted role: @{role_to_delete.name} ({role_to_delete.id})")
                return True
            except discord.Forbidden:
                print(f"  Failed to delete role @{role_to_delete.name}: Missing Permissions")
                return False
            except discord.HTTPException as e:
                print(f"  Failed to delete role @{role_to_delete.name}: {e} (HTTP {e.status})")
                if e.status == 429: await asyncio.sleep(e.retry_after if hasattr(e, 'retry_after') else 2)
                return False
            except Exception as e:
                 print(f"  Unexpected error deleting role @{role_to_delete.name}: {e}")
                 return False

        channels_to_delete = list(guild.channels)
        roles_to_delete = list(guild.roles)
        try:
            bot_top_role_position = guild.me.top_role.position
        except AttributeError:
             print("  Error accessing bot's top role, likely permissions changed. Cannot delete roles.")
             bot_top_role_position = -1

        channel_delete_tasks = [_delete_channel_task(ch) for ch in channels_to_delete]
        role_delete_tasks = []
        if bot_top_role_position != -1:
             role_delete_tasks = [_delete_role_task(r, bot_top_role_position) for r in roles_to_delete]
        else:
             print("Skipping role deletion due to permission issue.")

        all_delete_tasks = channel_delete_tasks + role_delete_tasks
        if not all_delete_tasks:
             print("No channels or roles found/eligible for deletion.")
        else:
            results = await asyncio.gather(*all_delete_tasks, return_exceptions=True)

            deleted_channels = sum(1 for i, res in enumerate(results) if i < len(channel_delete_tasks) and res is True)
            deleted_roles = sum(1 for i, res in enumerate(results) if i >= len(channel_delete_tasks) and res is True)
            skipped_roles = sum(1 for i, res in enumerate(results) if i >= len(channel_delete_tasks) and res is None)
            failed_channels = sum(1 for i, res in enumerate(results) if i < len(channel_delete_tasks) and res is False)
            failed_roles = sum(1 for i, res in enumerate(results) if i >= len(channel_delete_tasks) and res is False)
            exceptions_count = sum(1 for res in results if isinstance(res, Exception))

            print(f"Finished concurrent deletion.")
            print(f"  Channels: {deleted_channels} deleted, {failed_channels} failed.")
            print(f"  Roles: {deleted_roles} deleted, {failed_roles} failed, {skipped_roles} skipped.")
            if exceptions_count > 0:
                 print(f"  Encountered {exceptions_count} unexpected exceptions during deletion.")

        print(f"--- Nuke completed for guild {guild.name} ---")

    elif command == 'webhookspam':
        if not message.channel.permissions_for(message.guild.me).manage_webhooks:
            await message.channel.send("I need the 'Manage Webhooks' permission for this command.")
            return

        if len(args) < 3:
            await message.channel.send(f'Usage: {BOT_PREFIX}webhookspam <message> <amount>')
            return

        try:
            amount = int(args[-1])
            msg = ' '.join(args[1:-1])
            if not msg:
                 await message.channel.send(f'Usage: {BOT_PREFIX}webhookspam <message> <amount>')
                 return
        except ValueError:
            await message.channel.send('Amount must be a number.')
            return
        except IndexError:
             await message.channel.send(f'Usage: {BOT_PREFIX}webhookspam <message> <amount>')
             return

        amount = min(amount, 50)
        webhooks = []
        num_webhooks = 5
        try:
            print(f"Creating {num_webhooks} webhooks...")
            for i in range(num_webhooks):
                try:
                    webhook = await message.channel.create_webhook(name=f"SpamHook-{random.randint(1,10000)}")
                    webhooks.append(webhook)
                    print(f"  Created webhook {i+1}/{num_webhooks}")
                    await asyncio.sleep(0.5)
                except discord.HTTPException as e:
                    print(f"  Failed to create webhook {i+1}: {e}. Continuing with fewer webhooks.")
                    await asyncio.sleep(1)
                except discord.Forbidden:
                     await message.channel.send("I don't have permission to create webhooks. Aborting.")
                     for wh in webhooks:
                         try: await wh.delete()
                         except: pass
                     return

            if not webhooks:
                 await message.channel.send("Failed to create any webhooks.")
                 return

            print(f"Starting spam with {len(webhooks)} webhooks...")
            for i in range(amount):
                webhook_to_use = webhooks[i % len(webhooks)]
                try:
                    await webhook_to_use.send(msg)
                except discord.HTTPException as e:
                    print(f"  Error sending message with webhook {webhook_to_use.name}: {e}")
                    await asyncio.sleep(1)
                except Exception as e:
                     print(f"  Unexpected error sending message with webhook {webhook_to_use.name}: {e}")
                     await asyncio.sleep(1)

            print("Finished spamming.")

        except discord.Forbidden:
             await message.channel.send("I seem to have lost permission related to webhooks.")
        except discord.HTTPException as e:
            await message.channel.send(f"An HTTP error occurred during webhook spam: {e}")
        except Exception as e:
             await message.channel.send(f"An unexpected error occurred: {e}")
             print(f"Unexpected error in webhookspam: {e}")
        finally:
            print("Cleaning up webhooks...")
            deleted_count = 0
            for webhook in webhooks:
                try:
                    await webhook.delete()
                    deleted_count += 1
                    await asyncio.sleep(0.5)
                except discord.HTTPException as e:
                    print(f"  Failed to delete webhook {webhook.name}: {e}")
                except Exception as e:
                    print(f"  Unexpected error deleting webhook {webhook.name}: {e}")
            print(f"Finished cleanup. Deleted {deleted_count}/{len(webhooks)} webhooks.")

    elif command == 'wizz':
        if len(args) != 3:
            await message.channel.send(f"Usage: {BOT_PREFIX}wizz <name> <amount>")
            return
        name_base = args[1]
        try:
            amount = int(args[2])
            if amount <= 0:
                await message.channel.send("Amount must be a positive number.")
                return
            amount = min(amount, 50)
        except ValueError:
            await message.channel.send("Amount must be a number.")
            return

        if not message.guild.me.guild_permissions.manage_channels:
             await message.channel.send("I need the 'Manage Channels' permission to execute the wizz.")
             return
        if not message.guild.me.guild_permissions.manage_roles:
             await message.channel.send("I need the 'Manage Roles' permission to execute the wizz.")
             return
        if not message.author.guild_permissions.administrator:
             await message.channel.send("You need Administrator permissions to use this command.")
             return

        guild = message.guild
        author = message.author
        reason_delete = f'Server wizzed (delete phase) by {author} (ID: {author.id})'
        reason_create = f'Server wizzed (create phase) by {author} (ID: {author.id})'

        try:
            await message.channel.send(f"**EXTREME WARNING:** Wizz initiated by {author.mention}. Deleting ALL channels & roles, then creating {amount} new channels/roles named `{name_base}-X`...")
        except discord.HTTPException:
            print("Warning: Could not send initial wizz warning message (channel might be deleted).")

        print(f"--- Wizz initiated by {author} in guild {guild.name} ({guild.id}) ---")
        print(f"  Target name: {name_base}, Amount: {amount}")

        print("Starting channel deletion...")
        channels_to_delete = list(guild.channels)
        deleted_channel_count = 0
        for channel in channels_to_delete:
            try:
                await channel.delete(reason=reason_delete)
                print(f"  Deleted channel: #{channel.name} ({channel.id})")
                deleted_channel_count += 1
                await asyncio.sleep(0.2)
            except discord.Forbidden:
                print(f"  Failed to delete channel #{channel.name}: Missing Permissions")
            except discord.HTTPException as e:
                print(f"  Failed to delete channel #{channel.name}: {e}")
            except Exception as e:
                 print(f"  Unexpected error deleting channel #{channel.name}: {e}")
        print(f"Finished channel deletion. Deleted {deleted_channel_count}/{len(channels_to_delete)}.")

        print("Starting role deletion...")
        roles_to_delete = list(guild.roles)
        deleted_role_count = 0
        try:
            bot_top_role_position = guild.me.top_role.position
            for role in roles_to_delete:
                if role.is_default() or role.is_managed() or role.position >= bot_top_role_position:
                    print(f"  Skipping role: {role.name} (default/managed/higher)")
                    continue
                try:
                    await role.delete(reason=reason_delete)
                    print(f"  Deleted role: @{role.name} ({role.id})")
                    deleted_role_count += 1
                    await asyncio.sleep(0.2)
                except discord.Forbidden:
                    print(f"  Failed to delete role @{role.name}: Missing Permissions")
                except discord.HTTPException as e:
                    print(f"  Failed to delete role @{role.name}: {e}")
                except Exception as e:
                     print(f"  Unexpected error deleting role @{role.name}: {e}")
        except AttributeError:
             print("  Error accessing bot's top role, likely permissions changed. Stopping role deletion.")
        except Exception as e:
             print(f"  Unexpected error during role deletion setup: {e}")
        print(f"Finished role deletion. Deleted {deleted_role_count} roles.")

        print(f"Starting concurrent creation of {amount} channels and {amount} roles...")

        async def _create_channel_task(index):
            channel_name = f"{name_base}-{index+1}"
            try:
                current_guild = discord.utils.get(client.guilds, id=guild.id)
                if not current_guild:
                    print(f"  Guild unavailable, cannot create channel {channel_name}")
                    return False
                await current_guild.create_text_channel(name=channel_name, reason=reason_create)
                print(f"  Created channel: #{channel_name}")
                return True
            except discord.Forbidden:
                print(f"  Failed to create channel #{channel_name}: Missing Permissions.")
                return False
            except discord.HTTPException as e:
                print(f"  Failed to create channel #{channel_name}: {e} (HTTP {e.status})")
                if e.status == 429: await asyncio.sleep(e.retry_after if hasattr(e, 'retry_after') else 2)
                return False
            except Exception as e:
                print(f"  Unexpected error creating channel #{channel_name}: {e}")
                return False

        async def _create_role_task(index):
            role_name = f"{name_base}-{index+1}"
            try:
                current_guild = discord.utils.get(client.guilds, id=guild.id)
                if not current_guild:
                    print(f"  Guild unavailable, cannot create role {role_name}")
                    return False
                await current_guild.create_role(name=role_name, reason=reason_create)
                print(f"  Created role: @{role_name}")
                return True
            except discord.Forbidden:
                print(f"  Failed to create role @{role_name}: Missing Permissions.")
                return False
            except discord.HTTPException as e:
                print(f"  Failed to create role @{role_name}: {e} (HTTP {e.status})")
                if e.status == 429: await asyncio.sleep(e.retry_after if hasattr(e, 'retry_after') else 2)
                return False
            except Exception as e:
                print(f"  Unexpected error creating role @{role_name}: {e}")
                return False

        channel_tasks = [_create_channel_task(i) for i in range(amount)]
        role_tasks = [_create_role_task(i) for i in range(amount)]

        all_tasks = channel_tasks + role_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        created_channels = sum(1 for i, res in enumerate(results) if i < amount and res is True)
        created_roles = sum(1 for i, res in enumerate(results) if i >= amount and res is True)
        exceptions_count = sum(1 for res in results if isinstance(res, Exception))

        print(f"Finished concurrent creation.")
        print(f"  Successfully created channels: {created_channels}/{amount}")
        print(f"  Successfully created roles: {created_roles}/{amount}")
        if exceptions_count > 0:
             print(f"  Encountered {exceptions_count} exceptions during creation (check logs above).")

        print(f"--- Wizz completed for guild {guild.name} ---")

    elif command == 'ping':
        latency = client.latency * 1000
        await message.channel.send(f'Pong! Latency is {latency:.2f} ms')

    elif command == 'echo':
        if len(args) < 2:
            await message.channel.send(f"Usage: {BOT_PREFIX}echo <message>")
            return
        msg = ' '.join(args[1:])
        if client.http.token in msg:
             await message.channel.send("I cannot echo that.")
             return
        await message.channel.send(msg)

    elif command == 'clear':
        if not message.channel.permissions_for(message.guild.me).manage_messages:
            await message.channel.send("I need the 'Manage Messages' permission to clear messages.")
            return
        if not message.channel.permissions_for(message.author).manage_messages:
             await message.channel.send("You need the 'Manage Messages' permission to use this command.")
             return

        if len(args) != 2:
            await message.channel.send(f'Usage: {BOT_PREFIX}clear <amount>')
            return
        try:
            amount = int(args[1])
        except ValueError:
            await message.channel.send('Amount must be a number.')
            return

        if amount <= 0:
             await message.channel.send('Please provide a positive number.')
             return

        try:
            deleted = await message.channel.purge(limit=amount + 1)
            await message.channel.send(f'Deleted {len(deleted) - 1} messages.', delete_after=5)
        except discord.Forbidden:
            await message.channel.send("I don't have permission to delete messages here.")
        except discord.HTTPException as e:
            await message.channel.send(f"An error occurred: {e}")

    elif command == 'rickroll':
        await message.channel.send("Never gonna give you up, never gonna let you down...")
        await message.channel.send("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        try:
            await message.delete()
        except discord.Forbidden:
            pass

    elif command == 'fakeping':
        fake_latency = random.randint(300, 2000)
        await message.channel.send(f'Pong! Latency is {fake_latency:.2f} ms')

    elif command == 'reverse':
        if len(args) < 2:
            await message.channel.send(f"Usage: {BOT_PREFIX}reverse <message>")
            return
        original_message = ' '.join(args[1:])
        reversed_message = original_message[::-1]
        await message.channel.send(reversed_message)

TOKEN = "YOUR_TOKEN_HERE"

try:
    print("Attempting to connect with the provided token...")
    client.run(TOKEN.strip())
except discord.LoginFailure:
    print("Error: Invalid Discord Token. Please check the token.")
except discord.HTTPException as e:
    print(f"HTTP Exception: {e}")
except Exception as e:
    print(f"An unexpected error occurred while running the bot: {e}")
