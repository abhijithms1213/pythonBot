import random
import asyncio
import db_management


def randint(min=00000, max=99999):
    num = random.randint(min, max)
    return num


async def check_exist():
    while True:
        team_id = randint()
        status = await db_management.dbops('check_team_id_unique',
                                           team_id)
        print(f'team id is ::"":: {team_id}')
        if status:
            break


# # async def test():
# #    await check_exist()
#
#
#
if __name__ == '__main__':
    asyncio.run(check_exist())
#     await  test()
