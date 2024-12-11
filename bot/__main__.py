from aiofiles import open as aiopen
from aiofiles.os import (
    path as aiopath,
    remove
)
from asyncio import (
    create_subprocess_exec,
    gather
)
from nekozee.filters import command
from nekozee.handlers import MessageHandler
from os import execl as osexecl
from signal import (
    SIGINT,
    signal
)
from sys import executable
from time import time

from bot import (
    LOGGER,
    bot,
    config_dict,
    intervals,
    pkg_info,
    scheduler,
)
from .helper.ext_utils.bot_utils import (
    create_help_buttons,
    new_task,
    set_commands,
    sync_to_async
)
from .helper.ext_utils.db_handler import database
from .helper.ext_utils.files_utils import (
    clean_all,
    exit_clean_up
)
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.listeners.aria2_listener import start_aria2_listener
from .helper.task_utils.rclone_utils.serve import rclone_serve_booter
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.message_utils import (
    auto_delete_message,
    edit_message,
    send_file,
    send_message
)
from .modules import (
    anonymous,
    authorize,
    bot_settings,
    cancel_task,
    clone,
    exec,
    force_start,
    file_selector,
    gd_count,
    gd_delete,
    gd_search,
    help,
    leech_del,
    mirror_leech,
    rmdb,
    shell,
    status,
    users_settings,
    ytdlp,
)


@new_task
async def restart(_, message):
    intervals["stopAll"] = True
    restart_message = await send_message(
        message,
        "Restarting..."
    )
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if qb := intervals["qb"]:
        qb.cancel()
    if st := intervals["status"]:
        for intvl in list(st.values()):
            intvl.cancel()
    await sync_to_async(clean_all)
    proc1 = await create_subprocess_exec(
        "pkill",
        "-9",
        "-f",
        f"gunicorn|{pkg_info["pkgs"][-1]}"
    )
    proc2 = await create_subprocess_exec(
        "python3",
        "update.py"
    )
    await gather(
        proc1.wait(),
        proc2.wait()
    )
    async with aiopen(
        ".restartmsg",
        "w"
    ) as f:
        await f.write(f"{restart_message.chat.id}\n{restart_message.id}\n") # type: ignore
    osexecl(
        executable,
        executable,
        "-m",
        "bot"
    )


@new_task
async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await send_message(
        message,
        "Starting Ping"
    )
    end_time = int(round(time() * 1000))
    await edit_message(
        reply,
        f"{end_time - start_time} ms"
    )


@new_task
async def log(_, message):
    await send_file(
        message,
        "Zee_Logs.txt"
    )


help_string = f"""
<b>╭─《 🤖 BOT COMMANDS 》</b>

<b>╭─《 📤 MIRROR COMMANDS 》</b>
<b>├ /{BotCommands.MirrorCommand[0]}</b> or <b>/{BotCommands.MirrorCommand[1]}</b>
<b>├</b> Start mirroring to cloud
<b>├ /{BotCommands.QbMirrorCommand[0]}</b> or <b>/{BotCommands.QbMirrorCommand[1]}</b>
<b>├</b> Start Mirroring using qBittorrent
<b>├ /{BotCommands.YtdlCommand[0]}</b> or <b>/{BotCommands.YtdlCommand[1]}</b>
<b>╰</b> Mirror yt-dlp supported link

<b>╭─《 📥 LEECH COMMANDS 》</b>
<b>├ /{BotCommands.LeechCommand[0]}</b> or <b>/{BotCommands.LeechCommand[1]}</b>
<b>├</b> Start leeching to Telegram
<b>├ /{BotCommands.QbLeechCommand[0]}</b> or <b>/{BotCommands.QbLeechCommand[1]}</b>
<b>├</b> Start leeching using qBittorrent
<b>├ /{BotCommands.YtdlLeechCommand[0]}</b> or <b>/{BotCommands.YtdlLeechCommand[1]}</b>
<b>╰</b> Leech yt-dlp supported link

<b>╭─《 ☁️ GDRIVE COMMANDS 》</b>
<b>├ /{BotCommands.CloneCommand}</b> [drive_url]
<b>├</b> Copy file/folder to Google Drive
<b>├ /{BotCommands.CountCommand}</b> [drive_url]
<b>├</b> Count file/folder of Google Drive
<b>├ /{BotCommands.ListCommand}</b> [query]
<b>├</b> Search in Google Drive(s)
<b>├ /{BotCommands.DeleteCommand}</b> [drive_url]
<b>╰</b> Delete file from Drive [ADMIN]

<b>╭─《 🛠️ BOT SETTINGS 》</b>
<b>├ /{BotCommands.UserSetCommand[0]}</b> or <b>/{BotCommands.UserSetCommand[1]}</b>
<b>├</b> User Settings Panel
<b>├ /{BotCommands.BotSetCommand[0]}</b> or <b>/{BotCommands.BotSetCommand[1]}</b>
<b>├</b> Bot Settings Panel [ADMIN]
<b>├ /{BotCommands.UsersCommand}</b>
<b>╰</b> Show Users Settings [ADMIN]

<b>╭─《 ⚡️ TASK COMMANDS 》</b>
<b>├ /{BotCommands.StatusCommand[0]}</b>
<b>├</b> Show Downloads Status
<b>├ /{BotCommands.StatsCommand[0]}</b>
<b>├</b> Show Bot Stats [ADMIN]
<b>├ /{BotCommands.CancelTaskCommand[0]}</b> or <b>/{BotCommands.CancelTaskCommand[1]}</b>
<b>├</b> Cancel task by gid/reply
<b>├ /{BotCommands.CancelAllCommand}</b>
<b>╰</b> Cancel all tasks [ADMIN]

<b>╭─《 🔍 MISC COMMANDS 》</b>
<b>├ /{BotCommands.SelectCommand}</b>
<b>├</b> Select files from torrents
<b>├ /{BotCommands.SearchCommand}</b>
<b>├</b> Search for torrents
<b>├ /{BotCommands.PingCommand[0]}</b>
<b>├</b> Check Bot Alive [ADMIN]
<b>├ /{BotCommands.ForceStartCommand[0]}</b> or <b>/{BotCommands.ForceStartCommand[1]}</b>
<b>╰</b> Force Start Task

<b>╭─《 🔐 AUTH COMMANDS 》</b>
<b>├ /{BotCommands.AuthorizeCommand}</b>
<b>├</b> Auth chat/user [ADMIN]
<b>├ /{BotCommands.UnAuthorizeCommand}</b>
<b>├</b> Unauth chat/user [ADMIN]
<b>├ /{BotCommands.AddSudoCommand}</b>
<b>├</b> Add Sudo User [OWNER]
<b>├ /{BotCommands.RmSudoCommand}</b>
<b>╰</b> Remove Sudo [OWNER]

<b>╭─《 🛠️ MAINTAINANCE 》</b>
<b>├ /{BotCommands.RestartCommand[0]}</b>
<b>├</b> Restart Bot [ADMIN]
<b>├ /{BotCommands.LogCommand}</b>
<b>├</b> Get Bot Logs [ADMIN]
<b>├ /{BotCommands.ShellCommand}</b>
<b>├</b> Run Shell CMD [OWNER]
<b>├ /{BotCommands.AExecCommand}</b>
<b>├</b> Run Async Func [OWNER]
<b>├ /{BotCommands.ExecCommand}</b>
<b>├</b> Run Sync Func [OWNER]
<b>├ /{BotCommands.ClearLocalsCommand}</b>
<b>╰</b> Clear Locals [OWNER]

<b>╭─《 📰 RSS FEED 》</b>
<b>╰ /{BotCommands.RssCommand}</b>
<b>  └</b> RSS Menu

<b>📝 Note:</b> Click on any command to see more details.
"""

@new_task
async def bot_help(_, message):
    hmsg = await send_message(
        message,
        help_string
    )
    await auto_delete_message(
        message,
        hmsg
    )



async def restart_notification():
    if await aiopath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            (
                chat_id,
                msg_id
            ) = map(
                int,
                f
            )
    else:
        (
            chat_id,
            msg_id
        ) = (
            0,
            0
        )

    async def send_incomplete_task_message(cid, msg):
        try:
            if msg.startswith("Restarted Successfully!"):
                await bot.edit_message_text( # type: ignore
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=msg
                )
                await remove(".restartmsg")
            else:
                await bot.send_message( # type: ignore
                    chat_id=cid,
                    text=msg,
                    disable_web_page_preview=True,
                    disable_notification=True,
                )
        except Exception as e:
            LOGGER.error(e)

    if config_dict["INCOMPLETE_TASK_NOTIFIER"] and config_dict["DATABASE_URL"]:
        if notifier_dict := await database.get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                msg = (
                    "Restarted Successfully!"
                    if cid == chat_id
                    else "Bot Restarted!"
                )
                for tag, links in data.items():
                    msg += f"\n\n👤 {tag} Do your tasks again. \n"
                    for index, link in enumerate(
                        links,
                        start=1
                    ):
                        msg += f" {index}: {link} \n"
                        if len(msg.encode()) > 4000:
                            await send_incomplete_task_message(
                                cid,
                                msg
                            )
                            msg = ""
                if msg:
                    await send_incomplete_task_message(
                        cid,
                        msg
                    )
        if config_dict["STOP_DUPLICATE_TASKS"]:
            await database.clear_download_links()

    if await aiopath.isfile(".restartmsg"):
        try:
            await bot.edit_message_text( # type: ignore
                chat_id=chat_id,
                message_id=msg_id,
                text="Restarted Successfully!"
            )
        except:
            pass
        await remove(".restartmsg")


async def main():
    if config_dict["DATABASE_URL"]:
        await database.db_load()
    await gather(
        sync_to_async(clean_all),
        bot_settings.initiate_search_tools(),
        restart_notification(),
        telegraph.create_account(),
        rclone_serve_booter(),
        sync_to_async(
            start_aria2_listener,
            wait=False
        ),
        set_commands(bot),
    )
    create_help_buttons()

    bot.add_handler( # type: ignore
        MessageHandler(
            log,
            filters=command(
                BotCommands.LogCommand,
                case_sensitive=True
            ) & CustomFilters.sudo
        )
    )
    bot.add_handler( # type: ignore
        MessageHandler(
            restart,
            filters=command(
                BotCommands.RestartCommand,
                case_sensitive=True
            ) & CustomFilters.sudo
        )
    )
    bot.add_handler( # type: ignore
        MessageHandler(
            ping,
            filters=command(
                BotCommands.PingCommand,
                case_sensitive=True
            ) & CustomFilters.sudo
        )
    )
    bot.add_handler( # type: ignore
        MessageHandler(
            bot_help,
            filters=command(
                BotCommands.HelpCommand,
                case_sensitive=True
            ) & CustomFilters.authorized,
        )
    )
    LOGGER.info("Bot Started Successfully!")
    signal(
        SIGINT,
        exit_clean_up
    )


bot.loop.run_until_complete(main()) # type: ignore
bot.loop.run_forever() # type: ignore
