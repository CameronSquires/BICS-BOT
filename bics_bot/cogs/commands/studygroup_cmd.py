import nextcord
from nextcord.ext import commands
from nextcord import application_command, Interaction

from bics_bot.embeds.logger_embed import WARNING_LEVEL, LoggerEmbed
from bics_bot.config.server_ids import GUILD_BICS_ID, GUILD_BICS_CLONE_ID, CATEGORY_STUDY_GROUPS


class StudyGroupCmd(commands.Cog):
    """This class represents the command </create_study_group>

    The </create_study_group> command will let students create private text and voice 
    channels for their study groups.

    Attributes:
        client: Required by the API, not directly utilized.
    """

    def __init__(self, client):
        self.client = client

    @application_command.slash_command(
        guild_ids=[GUILD_BICS_ID, GUILD_BICS_CLONE_ID],
        description="Example: /create_study_group Awesome-LA1-Study-Group John D, Jane D, Adam S",
    )
    async def create_study_group(
        self,
        interaction: Interaction,
        group_name: str = nextcord.SlashOption(description="Try to make it unique to avoid overlapping. Example: use member names in the group name.", required=True),
        names: str = nextcord.SlashOption(description="Use server names. Separate names with a comma and a space. (', ')", required=True),
    ) -> None:
        """
        The </create_study_group> command will let students create private text and voice 
        channels for their study groups.

        Args:
            interaction: Required by the API. Gives meta information about
                the interaction.
            create: Bool value indicating if the student wants to create a 
                group or delete a group.

        Returns:
            None
        """
        if len(interaction.user.roles) == 1:
            # The user has no roles. So he must first use this command
            msg = "You haven't yet introduced yourself! Make sure you use the **/intro** command first"
            await interaction.response.send_message(
                embed=LoggerEmbed("Warning", msg, WARNING_LEVEL),
                ephemeral=True,
            )
            return
        elif nextcord.utils.get(interaction.user.roles, name="Incoming"):
            # The user has the incoming role and thus not allowed to use this command
            msg = "You are not allowed to create study groups, you aren't a student :)"
            await interaction.response.send_message(
                embed=LoggerEmbed("Warning", msg, WARNING_LEVEL),
                ephemeral=True,
            )
            return
        
        group_name = group_name.lower()
        
        # identical group name check
        for channel in interaction.guild.get_channel(CATEGORY_STUDY_GROUPS).channels:
            if channel.name == group_name:
                await interaction.response.send_message(
                    embed=LoggerEmbed("Warning", "Group name already in use. Enter a more unique group name.", WARNING_LEVEL),
                    ephemeral=True,
                )
                return
        
        member_count = len(names.split(", "))
        members = await self.get_members(interaction, names)
        if len(members) != member_count:
            await interaction.response.send_message(
                embed=LoggerEmbed("Warning", "Check the names you entered, and the format in which you entered them.", WARNING_LEVEL),
                ephemeral=True,
            )
            return

        topic = f"Study group {group_name} for {names}."
        category = interaction.guild.get_channel(CATEGORY_STUDY_GROUPS)
        text_overwrites, voice_overwrites = self.get_overwrites(interaction, members)
        text_channel: nextcord.TextChannel = await interaction.guild.create_text_channel(group_name, topic=topic, category=category, overwrites=text_overwrites)
        voice_channel: nextcord.VoiceChannel = await interaction.guild.create_voice_channel(group_name, category=category, overwrites=voice_overwrites)
        
        await interaction.response.send_message(
                embed=LoggerEmbed("Confirmation", f"Text channel <{text_channel.name}> and voice channel <{voice_channel.name}> have been created. Users {names} have been given access", WARNING_LEVEL),
                ephemeral=True,
        )

        return
    
    @application_command.slash_command(
        guild_ids=[GUILD_BICS_ID, GUILD_BICS_CLONE_ID],
        description="Example: /delete_study_group Awesome-LA1-Study-Group",
    )
    async def delete_study_group(
        self,
        interaction: Interaction,
        group_name: str = nextcord.SlashOption(description="Enter the name of the text channel or the voice channel", required=True),
    ) -> None:
        """
        The </delete_study_group> command will let students remove their private text and voice 
        channels for their study groups. The user must be in the group to delete the group.

        Args:
            interaction: Required by the API. Gives meta information about
                the interaction.
            group_name: Name of the study group to be removed

        Returns:
            None
        """

        if len(interaction.user.roles) == 1:
            # The user has no roles. So he must first use this command
            msg = "You haven't yet introduced yourself! Make sure you use the **/intro** command first"
            await interaction.response.send_message(
                embed=LoggerEmbed("Warning", msg, WARNING_LEVEL),
                ephemeral=True,
            )
            return
        elif nextcord.utils.get(interaction.user.roles, name="Incoming"):
            # The user has the incoming role and thus not allowed to use this command
            msg = "You are not allowed to create study groups, you aren't a student :)"
            await interaction.response.send_message(
                embed=LoggerEmbed("Warning", msg, WARNING_LEVEL),
                ephemeral=True,
            )
            return
        
        group_name = group_name.lower()

        studygroup_category = interaction.guild.get_channel(CATEGORY_STUDY_GROUPS)
        channels = []
        for channel in studygroup_category.channels:
            if channel.name == group_name:
                channels.append(channel)

        if interaction.user not in channels[0].overwrites.keys():
            await interaction.response.send_message(
                embed=LoggerEmbed("Warning", f"You are not a part of this study group. You cannot delete it.", WARNING_LEVEL),
                ephemeral=True,
            )
            # report_incident()
            return
        
        for channel in channels:
            await channel.delete()

        await interaction.response.send_message(
                embed=LoggerEmbed("Confirmation", f"Study group {group_name} has been deleted. Farewell.", WARNING_LEVEL),
                ephemeral=True,
        )

    
    async def get_members(self, interaction: Interaction, names: str) -> list[Interaction.user]:
        members: list[Interaction.user] = []
        for name in names.split(", "):
            for member in interaction.guild.members:
                if name == member.display_name:
                    members.append(member)
                    break
        return members
    
    def get_overwrites(self, interaction: Interaction, members: list[Interaction.user]):
        text_overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True)
        }
        for member in members:
            text_overwrites[interaction.guild.get_member(member.id)] = nextcord.PermissionOverwrite(read_messages=True)
        
        voice_overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            interaction.guild.me: nextcord.PermissionOverwrite(view_channel=True)
        }
        for member in members:
            voice_overwrites[interaction.guild.get_member(member.id)] = nextcord.PermissionOverwrite(view_channel=True)

        return (text_overwrites, voice_overwrites)
        

def setup(client):
    """Function used to setup nextcord cogs"""
    client.add_cog(StudyGroupCmd(client))