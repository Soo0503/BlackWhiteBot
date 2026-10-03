import os
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from dotenv import load_dotenv

from database import (
    init_database,
    add_player,
    get_players,
    delete_player,
    update_player
)

from lounge import get_lounge_name


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()

bot = discord.Client(
    intents=intents
)

tree = app_commands.CommandTree(bot)


# =========================================================
# 日本時間の今日の日付
# =========================================================

def get_today():
    return datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).strftime("%Y/%m/%d")


# =========================================================
# Bot起動
# =========================================================

@bot.event
async def on_ready():
    init_database()

    await tree.sync()

    print(f"ログイン成功: {bot.user}")
    print("スラッシュコマンドを同期しました")


# =========================================================
# Black List表示
# =========================================================

@tree.command(
    name="black_list",
    description="Blackリストを表示します"
)
async def black_list(
    interaction: discord.Interaction
):
    players = get_players("B")

    if not players:
        await interaction.response.send_message(
            "🖤 Blackリストは現在空です。"
        )
        return

    embed = discord.Embed(
        title="🖤 Black List",
        color=discord.Color.dark_red()
    )

    for (
        player_id,
        registered_name,
        lounge_id,
        reason,
        registered_date
    ) in players:

        lounge_name = get_lounge_name(lounge_id)

        if lounge_name is None:
            lounge_name = "取得失敗"

        profile_url = (
            "https://lounge.mkcentral.com/mk8dx/"
            f"PlayerDetails/{lounge_id}"
        )

        embed.add_field(
            name=registered_name,
            value=(
                f"Lounge Name："
                f"[{lounge_name}]({profile_url})\n"
                f"理由：{reason or 'なし'}\n"
                f"登録日：{registered_date}\n"
                f"\u200b"
            ),
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# Black List登録
# =========================================================

@tree.command(
    name="register_black",
    description="Blackリストにプレイヤーを登録します"
)
@app_commands.describe(
    登録名="登録後も変更されない固定の名前",
    loungeプロフィールid="LoungeプロフィールのID",
    理由="登録理由（任意）"
)
async def register_black(
    interaction: discord.Interaction,
    登録名: str,
    loungeプロフィールid: str,
    理由: str | None = None
):
    registered_date = get_today()

    add_player(
        list_type="B",
        registered_name=登録名,
        lounge_id=loungeプロフィールid,
        reason=理由,
        registered_date=registered_date
    )

    await interaction.response.send_message(
        f"Blackリストに登録しました。\n"
        f"登録名: {登録名}\n"
        f"LoungeプロフィールID: {loungeプロフィールid}\n"
        f"理由: {理由 or 'なし'}\n"
        f"登録日: {registered_date}"
    )


# =========================================================
# Black List削除確認
# =========================================================

class BlackDeleteConfirmView(
    discord.ui.View
):

    def __init__(self, player_id):
        super().__init__(timeout=60)
        self.player_id = player_id

    @discord.ui.button(
        label="削除する",
        style=discord.ButtonStyle.danger
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        delete_player(self.player_id)

        await interaction.response.edit_message(
            content="🗑️ Blackリストから削除しました。",
            embed=None,
            view=None
        )

    @discord.ui.button(
        label="キャンセル",
        style=discord.ButtonStyle.secondary
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="キャンセルしました。",
            embed=None,
            view=None
        )


# =========================================================
# Black List削除プルダウン
# =========================================================

class BlackDeleteSelect(
    discord.ui.Select
):

    def __init__(self, players):

        options = []

        for (
            player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) in players:

            lounge_name = get_lounge_name(lounge_id)

            if lounge_name is None:
                lounge_name = "取得失敗"

            options.append(
                discord.SelectOption(
                    label=registered_name[:100],
                    description=(
                        f"Lounge Name: {lounge_name}"
                    )[:100],
                    value=str(player_id)
                )
            )

        super().__init__(
            placeholder="削除するプレイヤーを選択",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        player_id = int(self.values[0])

        players = get_players("B")

        selected_player = None

        for player in players:
            if player[0] == player_id:
                selected_player = player
                break

        if selected_player is None:
            await interaction.response.send_message(
                "そのプレイヤーは見つかりませんでした。",
                ephemeral=True
            )
            return

        (
            _player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) = selected_player

        lounge_name = get_lounge_name(lounge_id)

        if lounge_name is None:
            lounge_name = "取得失敗"

        embed = discord.Embed(
            title="🗑️ Black List削除確認",
            description=(
                f"以下のプレイヤーを削除しますか？\n\n"
                f"**登録名：** {registered_name}\n"
                f"**Lounge Name：** {lounge_name}\n"
                f"**理由：** {reason or 'なし'}\n"
                f"**登録日：** {registered_date}"
            ),
            color=discord.Color.dark_red()
        )

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=BlackDeleteConfirmView(player_id)
        )


class BlackDeleteView(
    discord.ui.View
):

    def __init__(self, players):
        super().__init__(timeout=60)

        self.add_item(
            BlackDeleteSelect(players)
        )


# =========================================================
# /delete_black
# =========================================================

@tree.command(
    name="delete_black",
    description="Blackリストからプレイヤーを削除します"
)
async def delete_black(
    interaction: discord.Interaction
):

    players = get_players("B")

    if not players:
        await interaction.response.send_message(
            "🖤 Blackリストは現在空です。",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🗑️ 削除するプレイヤーを選択してください。",
        view=BlackDeleteView(players),
        ephemeral=True
    )


# =========================================================
# Black List編集モーダル
# =========================================================

class BlackEditModal(
    discord.ui.Modal,
    title="Black List 編集"
):

    登録名 = discord.ui.TextInput(
        label="登録名",
        placeholder="登録名を入力してください",
        required=True,
        max_length=100
    )

    loungeプロフィールid = discord.ui.TextInput(
        label="LoungeプロフィールID",
        placeholder="LoungeプロフィールIDを入力してください",
        required=True,
        max_length=50
    )

    理由 = discord.ui.TextInput(
        label="理由",
        placeholder="登録理由を入力してください",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )

    def __init__(
        self,
        player_id,
        registered_name,
        lounge_id,
        reason
    ):
        super().__init__()

        self.player_id = player_id

        self.登録名.default = registered_name
        self.loungeプロフィールid.default = lounge_id
        self.理由.default = reason or ""

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        new_registered_name = self.登録名.value.strip()
        new_lounge_id = self.loungeプロフィールid.value.strip()
        new_reason = self.理由.value.strip()

        if not new_reason:
            new_reason = None

        update_player(
            player_id=self.player_id,
            registered_name=new_registered_name,
            lounge_id=new_lounge_id,
            reason=new_reason
        )

        await interaction.response.send_message(
            f"✏️ Blackリストを更新しました。\n\n"
            f"登録名: {new_registered_name}\n"
            f"LoungeプロフィールID: {new_lounge_id}\n"
            f"理由: {new_reason or 'なし'}\n"
            f"登録日は変更していません。"
        )


# =========================================================
# Black List編集プルダウン
# =========================================================

class BlackEditSelect(
    discord.ui.Select
):

    def __init__(self, players):

        options = []

        for (
            player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) in players:

            lounge_name = get_lounge_name(lounge_id)

            if lounge_name is None:
                lounge_name = "取得失敗"

            options.append(
                discord.SelectOption(
                    label=registered_name[:100],
                    description=(
                        f"Lounge Name: {lounge_name}"
                    )[:100],
                    value=str(player_id)
                )
            )

        super().__init__(
            placeholder="編集するプレイヤーを選択",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        player_id = int(self.values[0])

        players = get_players("B")

        selected_player = None

        for player in players:
            if player[0] == player_id:
                selected_player = player
                break

        if selected_player is None:
            await interaction.response.send_message(
                "そのプレイヤーは見つかりませんでした。",
                ephemeral=True
            )
            return

        (
            _player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) = selected_player

        await interaction.response.send_modal(
            BlackEditModal(
                player_id,
                registered_name,
                lounge_id,
                reason
            )
        )


class BlackEditView(
    discord.ui.View
):

    def __init__(self, players):
        super().__init__(timeout=60)

        self.add_item(
            BlackEditSelect(players)
        )


# =========================================================
# /edit_black
# =========================================================

@tree.command(
    name="edit_black",
    description="Blackリストの登録内容を編集します"
)
async def edit_black(
    interaction: discord.Interaction
):

    players = get_players("B")

    if not players:
        await interaction.response.send_message(
            "🖤 Blackリストは現在空です。",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "✏️ 編集するプレイヤーを選択してください。",
        view=BlackEditView(players),
        ephemeral=True
    )


# =========================================================
# White List表示
# =========================================================

@tree.command(
    name="white_list",
    description="Whiteリストを表示します"
)
async def white_list(
    interaction: discord.Interaction
):
    players = get_players("W")

    if not players:
        await interaction.response.send_message(
            "🤍 Whiteリストは現在空です。"
        )
        return

    embed = discord.Embed(
        title="🤍 White List",
        color=discord.Color.light_grey()
    )

    for (
        player_id,
        registered_name,
        lounge_id,
        reason,
        registered_date
    ) in players:

        lounge_name = get_lounge_name(lounge_id)

        if lounge_name is None:
            lounge_name = "取得失敗"

        profile_url = (
            "https://lounge.mkcentral.com/mk8dx/"
            f"PlayerDetails/{lounge_id}"
        )

        embed.add_field(
            name=registered_name,
            value=(
                f"Lounge Name："
                f"[{lounge_name}]({profile_url})\n"
                f"理由：{reason or 'なし'}\n"
                f"登録日：{registered_date}\n"
                f"\u200b"
            ),
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# White List登録
# =========================================================

@tree.command(
    name="register_white",
    description="Whiteリストにプレイヤーを登録します"
)
@app_commands.describe(
    登録名="登録後も変更されない固定の名前",
    loungeプロフィールid="LoungeプロフィールのID",
    理由="登録理由（任意）"
)
async def register_white(
    interaction: discord.Interaction,
    登録名: str,
    loungeプロフィールid: str,
    理由: str | None = None
):
    registered_date = get_today()

    add_player(
        list_type="W",
        registered_name=登録名,
        lounge_id=loungeプロフィールid,
        reason=理由,
        registered_date=registered_date
    )

    await interaction.response.send_message(
        f"Whiteリストに登録しました。\n"
        f"登録名: {登録名}\n"
        f"LoungeプロフィールID: {loungeプロフィールid}\n"
        f"理由: {理由 or 'なし'}\n"
        f"登録日: {registered_date}"
    )


# =========================================================
# White List削除確認
# =========================================================

class WhiteDeleteConfirmView(
    discord.ui.View
):

    def __init__(self, player_id):
        super().__init__(timeout=60)
        self.player_id = player_id

    @discord.ui.button(
        label="削除する",
        style=discord.ButtonStyle.danger
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        delete_player(self.player_id)

        await interaction.response.edit_message(
            content="🗑️ Whiteリストから削除しました。",
            embed=None,
            view=None
        )

    @discord.ui.button(
        label="キャンセル",
        style=discord.ButtonStyle.secondary
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="キャンセルしました。",
            embed=None,
            view=None
        )


# =========================================================
# White List削除プルダウン
# =========================================================

class WhiteDeleteSelect(
    discord.ui.Select
):

    def __init__(self, players):

        options = []

        for (
            player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) in players:

            lounge_name = get_lounge_name(lounge_id)

            if lounge_name is None:
                lounge_name = "取得失敗"

            options.append(
                discord.SelectOption(
                    label=registered_name[:100],
                    description=(
                        f"Lounge Name: {lounge_name}"
                    )[:100],
                    value=str(player_id)
                )
            )

        super().__init__(
            placeholder="削除するプレイヤーを選択",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        player_id = int(self.values[0])

        players = get_players("W")

        selected_player = None

        for player in players:
            if player[0] == player_id:
                selected_player = player
                break

        if selected_player is None:
            await interaction.response.send_message(
                "そのプレイヤーは見つかりませんでした。",
                ephemeral=True
            )
            return

        (
            _player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) = selected_player

        lounge_name = get_lounge_name(lounge_id)

        if lounge_name is None:
            lounge_name = "取得失敗"

        embed = discord.Embed(
            title="🗑️ White List削除確認",
            description=(
                f"以下のプレイヤーを削除しますか？\n\n"
                f"**登録名：** {registered_name}\n"
                f"**Lounge Name：** {lounge_name}\n"
                f"**理由：** {reason or 'なし'}\n"
                f"**登録日：** {registered_date}"
            ),
            color=discord.Color.light_grey()
        )

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=WhiteDeleteConfirmView(player_id)
        )


class WhiteDeleteView(
    discord.ui.View
):

    def __init__(self, players):
        super().__init__(timeout=60)

        self.add_item(
            WhiteDeleteSelect(players)
        )


# =========================================================
# /delete_white
# =========================================================

@tree.command(
    name="delete_white",
    description="Whiteリストからプレイヤーを削除します"
)
async def delete_white(
    interaction: discord.Interaction
):

    players = get_players("W")

    if not players:
        await interaction.response.send_message(
            "🤍 Whiteリストは現在空です。",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🗑️ 削除するプレイヤーを選択してください。",
        view=WhiteDeleteView(players),
        ephemeral=True
    )


# =========================================================
# White List編集モーダル
# =========================================================

class WhiteEditModal(
    discord.ui.Modal,
    title="White List 編集"
):

    登録名 = discord.ui.TextInput(
        label="登録名",
        placeholder="登録名を入力してください",
        required=True,
        max_length=100
    )

    loungeプロフィールid = discord.ui.TextInput(
        label="LoungeプロフィールID",
        placeholder="LoungeプロフィールIDを入力してください",
        required=True,
        max_length=50
    )

    理由 = discord.ui.TextInput(
        label="理由",
        placeholder="登録理由を入力してください",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )

    def __init__(
        self,
        player_id,
        registered_name,
        lounge_id,
        reason
    ):
        super().__init__()

        self.player_id = player_id

        self.登録名.default = registered_name
        self.loungeプロフィールid.default = lounge_id
        self.理由.default = reason or ""

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        new_registered_name = self.登録名.value.strip()
        new_lounge_id = self.loungeプロフィールid.value.strip()
        new_reason = self.理由.value.strip()

        if not new_reason:
            new_reason = None

        update_player(
            player_id=self.player_id,
            registered_name=new_registered_name,
            lounge_id=new_lounge_id,
            reason=new_reason
        )

        await interaction.response.send_message(
            f"✏️ Whiteリストを更新しました。\n\n"
            f"登録名: {new_registered_name}\n"
            f"LoungeプロフィールID: {new_lounge_id}\n"
            f"理由: {new_reason or 'なし'}\n"
            f"登録日は変更していません。"
        )


# =========================================================
# White List編集プルダウン
# =========================================================

class WhiteEditSelect(
    discord.ui.Select
):

    def __init__(self, players):

        options = []

        for (
            player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) in players:

            lounge_name = get_lounge_name(lounge_id)

            if lounge_name is None:
                lounge_name = "取得失敗"

            options.append(
                discord.SelectOption(
                    label=registered_name[:100],
                    description=(
                        f"Lounge Name: {lounge_name}"
                    )[:100],
                    value=str(player_id)
                )
            )

        super().__init__(
            placeholder="編集するプレイヤーを選択",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        player_id = int(self.values[0])

        players = get_players("W")

        selected_player = None

        for player in players:
            if player[0] == player_id:
                selected_player = player
                break

        if selected_player is None:
            await interaction.response.send_message(
                "そのプレイヤーは見つかりませんでした。",
                ephemeral=True
            )
            return

        (
            _player_id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        ) = selected_player

        await interaction.response.send_modal(
            WhiteEditModal(
                player_id,
                registered_name,
                lounge_id,
                reason
            )
        )


class WhiteEditView(
    discord.ui.View
):

    def __init__(self, players):
        super().__init__(timeout=60)

        self.add_item(
            WhiteEditSelect(players)
        )


# =========================================================
# /edit_white
# =========================================================

@tree.command(
    name="edit_white",
    description="Whiteリストの登録内容を編集します"
)
async def edit_white(
    interaction: discord.Interaction
):

    players = get_players("W")

    if not players:
        await interaction.response.send_message(
            "🤍 Whiteリストは現在空です。",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "✏️ 編集するプレイヤーを選択してください。",
        view=WhiteEditView(players),
        ephemeral=True
    )


# =========================================================
# Bot起動
# =========================================================

bot.run(TOKEN)