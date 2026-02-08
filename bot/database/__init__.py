"""
Copyright © Krypton 2019-Present - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized Discord bot in Python

Version: 6.4.0
"""

import aiosqlite


class DatabaseManager:

    #template DB management

    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def add_warn(
        self, user_id: int, server_id: int, moderator_id: int, reason: str
    ) -> int:
        """
        This function will add a warn to the database.

        :param user_id: The ID of the user that should be warned.
        :param reason: The reason why the user should be warned.
        """
        rows = await self.connection.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await self.connection.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
                (
                    warn_id,
                    user_id,
                    server_id,
                    moderator_id,
                    reason,
                ),
            )
            await self.connection.commit()
            return warn_id

    async def remove_warn(self, warn_id: int, user_id: int, server_id: int) -> int:
        """
        This function will remove a warn from the database.

        :param warn_id: The ID of the warn.
        :param user_id: The ID of the user that was warned.
        :param server_id: The ID of the server where the user has been warned
        """
        await self.connection.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (
                warn_id,
                user_id,
                server_id,
            ),
        )
        await self.connection.commit()
        rows = await self.connection.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

    async def get_warnings(self, user_id: int, server_id: int) -> list:
        """
        This function will get all the warnings of a user.

        :param user_id: The ID of the user that should be checked.
        :param server_id: The ID of the server that should be checked.
        :return: A list of all the warnings of the user.
        """
        rows = await self.connection.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
        

    #DB management for Stock


    async def add_ticker_user(self, user_id, ticker, server_id):
        await self.connection.execute(
            "INSERT OR REPLACE INTO tickers_users(user_id, ticker, server_id) VALUES(?,?,?)",
            (
                user_id,
                ticker,
                server_id
            )
        )
        await self.connection.commit()

    async def remove_tickers_users(self, user_id, ticker):
        await self.connection.execute(
            "DELETE FROM tickers_users WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ) 
        await self.connection.commit()
    
    async def get_all_tickers(self):
        tickers = []
        rows = await self.connection.execute(
            "SELECT DISTINCT ticker from tickers_users"
        )        
        tickers = await rows.fetchall()
        tickers = [row[0] for row in tickers]
        await self.connection.commit()
        return tickers
    
    async def add_ticker_row(
            self,
            ticker,
            timestamp,
            resolution, 
            high,
            low,
            open,
            close,
            volume
        ):

        await self.connection.execute(
            "INSERT OR REPLACE INTO tickers(" \
            "   ticker," \
            "   timestamp," \
            "   resolution," \
            "   high," \
            "   low," \
            "   open," \
            "   close," \
            "   volume" \
            ") VALUES(?,?,?,?,?,?,?,?)",
            (
                ticker, timestamp, resolution,
                high, low, open, close, volume

            )
        )

        await self.connection.commit()
 

    #DB management for CP

    async def add_cp_acc_row(
            self,
            user_id,
            handle,
            platform
    ):
    
        await self.connection.execute(
            "INSERT OR REPLACE INTO cp_acc("
            "   user_id,"
            "   handle,"
            "   platform"
            ") VALUES(?,?,?)",
            (
                user_id, handle, platform
            )
        )
        
        await self.connection.commit()

    async def add_cp_channel_row(
            self,
            channel_id
    ):
        await self.connection.execute(
            "INSERT OR REPLACE INTO cp_channel(" \
            "   channel_id" \
            ") VALUES(?)",
            (
                channel_id,
            )
        )
        await self.connection.commit()

    async def get_all_cp_channel(self):
        channels = []
        rows = await self.connection.execute(
            "SELECT * FROM cp_channel"
        )        
        channels = await rows.fetchall()
        channels = [row[0] for row in channels]
        await self.connection.commit()
        return channels

    async def remove_cp_channel_row(
            self, channel_id
    ):
        await self.connection.execute(
            "DELETE FROM cp_channel WHERE channel_id = ?",
            (channel_id,),
        ) 
        await self.connection.commit()
        
    async def __get_user_channel(self,user_id):
        rows = await self.connection.execute(
            "SELECT * FROM user_cp_streak WHERE user_id =?",
            (user_id,),
        )
        
        users = await rows.fetchall()
        await self.connection.commit()
        try:
            channel_id = users[0][1]
            return channel_id
        except:
            return None

    async def add_user_cp_streak(
            self, user_id, channel_id, 
    ):  
        used_channel_id = await self.__get_user_channel(user_id)
        if (used_channel_id == channel_id):
            return
        elif (used_channel_id == None):
            await self.connection.execute(
                "INSERT INTO user_cp_streak(" \
                "   user_id, channel_id, streak, last_submit, solved_problems" \
                ") VALUES(?,?,?,?,?)",
                (user_id, channel_id,0,0,0),
            )
        else:
            await self.connection.execute(
                "UPDATE user_cp_streak" \
                "SET channel_id = ? " \
                "WHERE user_id = ?" \
                "VALUES (?,?)",
                (channel_id, user_id)
            )
        
        await self.connection.commit()

    async def add_daily_problem(
            self, date, problem_id, platform
    ):
        await self.connection.execute(
            "INSERT INTO daily_problem(" \
            "   date, problem_id, platform" \
            ") VALUES(?,?,?)",
            (date, problem_id, platform)
        )
        await self.connection.commit()

    async def get_cp_handle(
            self, user_id, platform=None
    ):
        accs = await self.connection.execute(
            "SELECT * FROM cp_acc WHERE user_id = ?", (user_id,)  ,
        )
        accs = await accs.fetchall()
        await self.connection.commit()
        
        if not accs:
            return None
        
        # If platform is specified, return handle for that platform
        if platform:
            for acc in accs:
                if acc[2] == platform:  # acc[2] is platform
                    return acc[1]  # Return handle
            return None
        
        # Otherwise return handle and platform of first account
        return {"handle": accs[0][1], "platform": accs[0][2]}
        


    async def get_daily_problem(
            self,
    ):
        problems = await self.connection.execute(
            "SELECT * FROM daily_problem " \
            "WHERE date = (SELECT MAX(date) FROM daily_problem)"
        )
        problems = await problems.fetchone()
        return problems

    async def new_user_streak(self, user_id, channel_id, streak=0, last_submit=0):
        await self.connection.execute(
            "INSERT INTO user_cp_streak (" \
            "user_id, channel_id, streak, last_submit, solved_problems)" \
            "VALUES(?,?,?,?,?)",
            (user_id, channel_id, streak, last_submit, 0) \
        )
        await self.connection.commit()
    

    async def get_user_cp_streak(self, user_id):
        rows = await self.connection.execute(
            "SELECT streak, last_submit, solved_problems FROM user_cp_streak WHERE user_id = ?",
            (user_id,),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
        return result if result is not None else None

    async def update_user_streak(self, user_id, date, streak, solved_problems):
        await self.connection.execute(
            "UPDATE user_cp_streak "  
            "SET last_submit = ?, streak = ?, solved_problems = ? " 
            "WHERE user_id = ?",
            (date, streak, solved_problems, user_id) 
        )
        await self.connection.commit()

    async def get_all_users_cp_streak(self, channel_id):
        rows = await self.connection.execute(
            "SELECT * FROM user_cp_streak where channel_id = ? ORDER BY solved_problems DESC, streak DESC",
            (channel_id,),
        )
        users = await rows.fetchall()
        return users
    
    async def reset_streak(self, user_id):
        await self.connection.execute(
            """
            UPDATE user_cp_streak
            SET streak = ? WHERE user_id = ?
            """,
            (0, user_id)
        )
        await self.connection.commit()