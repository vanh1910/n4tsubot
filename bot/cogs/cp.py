from discord.ext import commands,tasks
from discord.ext.commands import Context
import discord
import asyncio
import datetime,time
import random
from services.api_handler import CPAPIHANDLER
import os
import json

owner_id = os.getenv('OWNER_ID')

# For some reason, mostly Im too lazy, I vibecoded all the UI related things

class SubmitButton(discord.ui.View):
    def __init__(self, handle, platform, problem) -> None:
        super().__init__(timeout=None)
        self.handle = handle
        self.platform = platform
        self.problem = problem
        self.cp_api = CPAPIHANDLER()
        self.result = False

    @discord.ui.button(label="Done", style=discord.ButtonStyle.blurple)
    async def submit_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
        ):
        # Acknowledge the interaction immediately
        await interaction.response.defer()
        
        try:
            subs = await self.cp_api.fetch_user_submission(self.handle)
            for sub in subs["result"]:
                problem_id = f"{sub['problem']['contestId']}{sub['problem']['index']}"
                expected_id = f"{self.problem['contestId']}{self.problem['index']}"
                
                if problem_id == expected_id and sub["verdict"] == "COMPILATION_ERROR":
                    self.result = True
                    self.stop()
                    return
            
            self.stop()
            #await interaction.followup.send("❌ No compilation error found on this problem. Please try again.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error checking submissions: {str(e)}")
            
        self.stop()

        

        

        




class CP(commands.Cog, name="cp"):
    daily_problem_time = datetime.time(hour=0, minute=10, tzinfo=datetime.timezone.utc)
    # compute recap time safely (combine with a date, subtract timedelta, take .time())
    daily_recap_time = (
        datetime.datetime.combine(datetime.date.today(), daily_problem_time)
        - datetime.timedelta(hours=0,minutes=20)
    ).time()
    """
    init stuff
    """


    def __init__(self, bot) -> None:
        self.bot = bot
        self.cp_api = CPAPIHANDLER()
        self.update_problems.start()
        self.daily_problem.start()
        self.daily_recap.start()

    @commands.hybrid_group(
            name="cp", 
            description="commands for cp grinders"
    )
    async def cp(self, context: Context, *args) -> None:
        """
            Init function for cp cog
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="Please specify a subcommand"
            )
        await context.reply(embed=embed)

    """
    UI stuff
    """

    def __get_rating_color(self, rating):
        if rating < 1200: return 0xCCCCCC # Gray (Newbie)
        if rating < 1400: return 0x77FF77 # Green (Pupil)
        if rating < 1600: return 0x03A89E # Cyan (Specialist)
        if rating < 1900: return 0x0000FF # Blue (Expert)
        if rating < 2100: return 0xAA00AA # Violet (Candidate Master)
        if rating < 2300: return 0xFF8C00 # Orange (Master)
        if rating < 2400: return 0xFF8C00 # Orange (International Master) - CF dùng chung màu cam
        if rating < 2600: return 0xFF0000 # Red (Grandmaster)
        return 0xFF0000 # Red (Legendary GM)
    

    def __embedding_cf(self, problem):
        if (problem["platform"] == "cf"):
            problem_link = f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}"
            thumbnail = "https://sta.codeforces.com/s/70808/images/codeforces-telegram-square.png"
        else:
            problem_link = f"https://atcoder.jp/contests/{problem['contestId']}/tasks/{problem['contestId']}_{problem['index'].lower()}"
            thumbnail = "https://img.atcoder.jp/assets/atcoder.png"
        embed = discord.Embed(
            title=f"{problem['contestId']}{problem['index']} - {problem['name']}",
            url=problem_link, # Click vào tiêu đề sẽ mở link
            color=self.__get_rating_color(int(problem.get('rating', 0))) # Set màu theo rating
        )
        embed.add_field(name="📊 Rating", value=f"`{problem.get('rating', 'Unrated')}`", inline=True)
        embed.set_thumbnail(url=thumbnail)
        return embed





    


    """
    Register stuff
    """

    @cp.command(
        name = "set",
        description = "set channel for daily cp problems, or register dm for daily cp problems"
    )
    async def set(self, context:Context) -> None:
        """
            Add server channel, or dm for daily problems
        """
        channel_id = context.channel.id
        if context.guild:
            if not (context.message.author.guild_permissions.administrator or context.message.author.id == int(owner_id)):
                return
                
        await self.bot.database.add_cp_channel_row(channel_id)
        await context.reply("Registering channel completely")

    @cp.command(
        name = "unset",
        description = "unset channel for daily cp problems"
    )
    async def unset(self, context:Context) -> None:
        """
            Add server channel, or dm for daily problems
        """
        channel_id = context.channel.id
        if context.guild:
            if not (context.message.author.guild_permissions.administrator or context.message.author.id == int(owner_id)):
                return
                
        await self.bot.database.remove_cp_channel_row(channel_id)
        await context.reply("Unset channel completely")





    @cp.command(
        name = "save",
        description = "Save your cp accounts (*Currently only support cf*)"
    )
    async def save(self, context: Context, platform, handle):
        problem = await self.cp_api.random_problem()
        if (platform == "cf"):
            while problem["platform"] != "cf":
                problem = await self.cp_api.random_problem()
            problem_link = f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}"
            user_id = context.author.id

            button = SubmitButton(handle, platform, problem)
            embed = discord.Embed(
                color = 0xCCCCCC,
                description=f"Please submit a compilation error to [this problem]({problem_link})\n"
                            "When you are done, press the button below",
            )
            message = await context.send(embed=embed, view=button)
            await asyncio.sleep(0.1) 
            
            try:
                # Set a timeout of 300 seconds (5 minutes)
                await asyncio.wait_for(button.wait(), timeout=300)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    description="⏰ Verification timed out. Please try again.",
                    color=0xFF0000
                )
                await message.edit(embed=embed, view=None)
                return
            
            print(button.result)
            if button.result:
                await self.bot.database.add_cp_acc_row(user_id,handle,platform)
                embed = discord.Embed(
                    description="✅ You are now signed in uwu!!",
                    color=0x00FF00
                )
                await message.edit(embed=embed, view=None)
            else:
                embed = discord.Embed(
                    description=f"❌ Please resubmit the [problem]({problem_link}) :3",
                    color=0xFF0000
                )
            await message.edit(embed=embed, view=button)

        elif platform == "at":
            problem = {
                "index": "A",
                "contestId": f"abc{random.randrange(300,400)}"
            }

            problem_link = f"https://atcoder.jp/contests/{problem['contestId']}/tasks/{problem['contestId']}_{problem['index'].lower()}"
            problem_id = f"{problem["contestId"]}_{problem["index"].lower()}"
            embed = discord.Embed(
                color = 0xCCCCCC,
                description=f"Please submit a CE to [this problem]({problem_link}) and wait for at most five minutes"
            )
            await context.reply(embed = embed)
            for i in range(10):
                submissions = await self.cp_api.at_fetch_contest(problem["contestId"])
                if submissions == None:
                    continue
                # print(submissions)
                for sub in submissions:
                    pid = sub["task"][0]
                    if sub["status"] == "CE" and pid == problem["index"]:
                        await self.bot.database.add_cp_acc_row(context.author.id, handle, platform)
                        await context.send("✅ You are now signed in uwu!!")
                        return
                await asyncio.sleep(30)
            
            await context.send("❌ Please login again")
            

        

        
    """
    Random stuff
    """
        

    @cp.command(
        name = "random",
        description= "get random cp problem"
    )
    async def random_problem(self, context:Context):
        """
            Replying random problem to user message
        """
        problem = await self.cp_api.random_problem()
        await context.reply(embed=self.__embedding_cf(problem))



    @cp.command(
        name = "truerandom",
        description = "Random problem without weight"
    )
    async def true_random_problem(self, context: Context):
        """
            Replying true random problem to user message
        """
        problem = await self.cp_api.true_random_problem()
        await context.reply(embed=self.__embedding_cf(problem))
    



    """
    Owner stuff
    """
    

    @cp.command(
        name = "channels"
    )
    @commands.is_owner()
    async def get_all_channels(self, context: Context):
        channels = await self.bot.database.get_all_cp_channel()
        await context.reply(channels)




   
    """
    Leaderboard stuff
    """


    

    @cp.command(
        name = "lb",
        description = "Ranking user"
    )
    async def leaderboard(self, context: Context):
        users = await self.bot.database.get_all_users_cp_streak(context.channel.id)
        name = []
        for user in users:
            user_id = user[0]
            data = self.bot.get_user(user_id)
            
            if data:
                name.append(data.name)
            else:
                data = await self.bot.fetch_user(user_id)
                if data:
                    name.append(data.name)




        #This is vibecoding
        w_rank = 3   # Cột số thứ tự
        w_name = 16  # Cột tên (đủ dài để không bị cắt)
        w_solv = 8   # Cột Solved
        w_strk = 8   # Cột Streak

        # 3. Tạo Header
        # F-string format: {biến : <căn_lề> <độ_rộng>}
        # < : Trái, ^ : Giữa, > : Phải
        header = f"{'#':<{w_rank}} | {'Name':<{w_name}} | {'Solved':^{w_solv}} | {'Streak':^{w_strk}}"
        separator = "-" * len(header) # Dòng kẻ ngang

        # 4. Tạo các dòng dữ liệu (Rows)
        rows = []
        for index, user in enumerate(users):
            # Cắt tên nếu quá dài (Tránh vỡ bảng)
            name_display = (name[index][:w_name-2] + '..') if len(name[index]) > w_name else name[index]
            
            row = f"{index + 1:<{w_rank}} | {name_display:<{w_name}} | {user[4]:^{w_solv}} | {user[2]:^{w_strk}}"
            rows.append(row)

        # 5. Ghép thành chuỗi hoàn chỉnh
        # Đặt trong ```text ... ``` để Discord hiển thị font monospace
        table_content = f"```text\n{header}\n{separator}\n" + "\n".join(rows) + "\n```"

        # 6. Tạo Embed
        embed = discord.Embed(
            title="🏆 CP Local Leaderboard",
            description=table_content, # Bảng nằm ở đây
            color=0xFFD700 # Màu vàng Gold
        )
        

        await context.send(embed=embed)
            

    """
    Retrieve user info
    """


    @cp.command(
        name = "cf",
        description = "get user codeforces info"
    )
    async def cf_acc(self, context: Context):

        #By the way, Im lazy in doing UI stuff, so lol I vibecoded this



        handle = await self.bot.database.get_cp_handle(context.author.id)
        data = await self.cp_api.fetch_user_info(handle)
        user_data = data['result'][0]

        handle = user_data.get('handle')
        rank = user_data.get('rank', 'Unrated')
        max_rank = user_data.get('maxRank', 'Unrated')
        rating = user_data.get('rating', 0)
        max_rating = user_data.get('maxRating', 0)
        
        first_name = user_data.get('firstName', '')
        last_name = user_data.get('lastName', '')
        full_name = f"{first_name} {last_name}".strip()
        
        city = user_data.get('city', '')
        country = user_data.get('country', '')
        location = f"{city}, {country}".strip(', ')
        
        org = user_data.get('organization', 'N/A')
        avatar_url = user_data.get('avatar')
        title_photo = user_data.get('titlePhoto') # Banner image
        
        last_online = user_data.get('lastOnlineTimeSeconds')
        
        embed = discord.Embed(
            title=f"{rank.title()}: {handle}",
            url=f"https://codeforces.com/profile/{handle}",
            description=f"**{full_name}**\n{org}",
            color=self.__get_rating_color(rating) # Dynamic color based on rank
        )

        # Top right thumbnail (Avatar)
        embed.set_thumbnail(url=avatar_url)

        # Statistics Fields
        embed.add_field(name="Current Rating", value=f"**{rating}**", inline=True)
        embed.add_field(name="Max Rating", value=f"**{max_rating}**", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

        embed.add_field(name="Rank", value=rank.title(), inline=True)
        embed.add_field(name="Max Rank", value=max_rank.title(), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

        if location:
            embed.add_field(name="📍 Location", value=location, inline=False)


        # Footer with Last Online status
        # <t:TIMESTAMP:R> turns a timestamp into "5 minutes ago" automatically
        embed.add_field(
            name="Last Online", 
            value=f"<t:{last_online}:R>", 
            inline=False
        )
        
        embed.set_footer(text="Codeforces Profile", icon_url="https://cdn.iconscout.com/icon/free/png-256/codeforces-3628695-3029920.png")

        await context.send(embed=embed)



    """
        Daily problem stuff
    """

    @cp.command(
        name = "submit",
        description = "submit daily problem" 
    )
    async def submit(self, context: Context):
        handle = await self.bot.database.get_cp_handle(context.author.id)
        subs = await self.cp_api.fetch_user_submission(handle)
        problem_id = await self.bot.database.get_daily_problem()
        problem_id = problem_id[1]

        for sub in subs["result"]:
            sub_problem_id = f"{sub['problem']['contestId']}{sub['problem']['index']}"
            if sub_problem_id == problem_id and sub["verdict"] == "OK":
                await context.reply("Congrats, you completed the problem today uwu")
                #some logic for the submit feat here
                user_id = context.author.id
                today = int(time.time() // 86400 * 86400)
                user_streak_data = await self.bot.database.get_user_cp_streak(user_id)
                if not user_streak_data:
                    await self.bot.database.new_user_streak(user_id, context.channel.id,1,today)
                    return
                last_submit_date = user_streak_data[1]
                streak = user_streak_data[0]
                solved_problems = user_streak_data[2]
                
                

  
                if today - last_submit_date  > 86400:
                    await self.bot.database.update_user_streak(user_id, today, 1, solved_problems + 1)
                elif today == last_submit_date:
                    return
                else:
                    await self.bot.database.update_user_streak(user_id, today, streak + 1, solved_problems + 1)
                    
                return
            
        await context.reply("Lol, did you AC'ed today problem??")
        return


    def __convert_id (self, id :str, platform: str):
        for i in range (len(id)):
            if id[i].isalpha():
                return f"{platform}_{id[0:i]}_{id[i::].lower()}"


    @cp.command(
        name = "daily"
    )
    @commands.is_owner()
    async def set_daily_manually(self, context:Context, problem=None):
        problem = await self.bot.database.get_daily_problem()
        today  = int(time.time() // 86400 * 86400)
        last_day = int(problem[0])
        if (today - last_day) >= 86400:
            await self._daily_problem_task()
        else:
            id = self.__convert_id(problem[1], problem[2])
            with open("data/json/problems.json") as f:
                data = json.loads(f.read())
            problem = data[id]
            await context.reply(embed = self.__embedding_cf(problem)) 


    async def _daily_problem_task(self):
        problem = await self.cp_api.random_problem()
        channels_id = await self.bot.database.get_all_cp_channel()
        today = int(time.time() // 86400 * 86400)
        problem_id = f"{problem['contestId']}{problem['index']}"
        await self.bot.database.add_daily_problem(today,problem_id,problem["platform"])


        for channel_id in channels_id:
            channel = self.bot.get_channel(channel_id)
            await asyncio.sleep(0.5)
            if channel:
                problem_link = f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}"
                embed = self.__embedding_cf(problem)

                embed.set_author(
                    name="📅 Daily CP Challenge", 
                    icon_url="https://cdn-icons-png.flaticon.com/512/4251/4251963.png" # Ví dụ icon lịch
                )

                await channel.send(embed=embed)
            else:
                self.bot.logger.warn(f"Cannot find {channel_id} in cache")

    @tasks.loop(time=daily_problem_time)
    async def daily_problem(self) -> None:
        await self._daily_problem_task()

    @daily_problem.before_loop
    async def before_daily_problem(self) -> None:
        await self.bot.wait_until_ready()


    @tasks.loop(time=daily_recap_time)
    async def update_problems(self):
        if datetime.datetime.now().weekday() != 0:
            return
        self.cp_api.build_dynamic_weight_map()
        await self.cp_api.update_data()
    
    @update_problems.before_loop
    async def before_daily_problem(self) -> None:
        await self.bot.wait_until_ready()
                        

    """
    Recap stuff
    """

    @cp.command(
        name = "test"
    )
    @commands.is_owner()
    async def test(self, context: Context):
        await context.reply(context.guild.id)

    @tasks.loop(time=daily_recap_time)
    async def daily_recap(self):
        channels_id = await self.bot.database.get_all_cp_channel()
        today = int(time.time() // 86400 * 86400)

        for channel_id in channels_id:
            try:
                channel = self.bot.get_channel(int(channel_id))
                await asyncio.sleep(0.5)
                if not channel:
                    self.bot.logger.warning(f"Cannot find channel {channel_id} in cache, skipping")
                    continue

                completing_user = []
                self.bot.logger.info(channel_id)
                # correct method name and await it
                users = await self.bot.database.get_all_users_cp_streak(channel_id)
                self.bot.logger.info(users)
                for user in users:
                    if int(user[3]) != today:
                        await self.bot.database.reset_streak(user[0])
                    else:
                        completing_user.append(user)
                
                if len(completing_user) == 0:
                    await channel.send("Bro, the daily problem just mogged the whole server. Y'all actually have 0 aura today. Straight up NPC behavior🥀")
                    continue

                lines = ["🎉 **DAILY CHALLENGE RESULTS** 🎉"]
                for user in completing_user:
                    lines.append(f"<@{user[0]}> is on a {user[2]} days streak.")
                lines.append("Congrats ₍^ >ヮ<^₎")
                final_content = "\n".join(lines)
                await channel.send(final_content)
            except Exception as e:
                self.bot.logger.exception(f"Error while sending daily recap to channel {channel_id}: {e}")

    @daily_recap.before_loop
    async def before_daily_recap(self) -> None:
        await self.bot.wait_until_ready()

async def setup(bot) -> None:
    await bot.add_cog(CP(bot))