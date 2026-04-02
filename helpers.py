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


import random

# 🎯 100 TEAM NAMES
TEAM_NAMES = [
    "Code Titans", "Bug Slayers", "Binary Beasts", "Stack Masters",
    "Dev Dominators", "Logic Legends", "Syntax Squad", "Byte Warriors",
    "Code Commanders", "Debug Ninjas", "Pixel Pioneers", "Algorithm Army",
    "Script Storm", "Compile Kings", "Tech Troopers", "Cyber Squad",
    "Quantum Coders", "Runtime Rebels", "Dev Dynasty", "Hack Heroes",
    "Infinite Loopers", "Null Pointers", "Recursive Minds", "Terminal Titans",
    "Git Guardians", "Merge Masters", "Branch Bosses", "Code Crafters",
    "Dev Dragons", "Stack Overflowers", "Cloud Crusaders", "Kernel Kings",
    "AI Avengers", "Data Dynamos", "Backend Bandits", "Frontend Force",
    "Fullstack Fighters", "Server Samurai", "Cache Crew", "Script Squad",
    "Bug Hunters", "Error Eliminators", "Logic Lords", "Syntax Samurai",
    "Binary Bosses", "Dev Knights", "Code Crushers", "Hack Hustlers",
    "Deploy Demons", "Runtime Raiders", "Compile Crew", "Script Soldiers",
    "Tech Titans", "Code Wizards", "Bug Busters", "Stack Slayers",
    "Dev Ninjas", "Cyber Knights", "Pixel Pirates", "Algorithm Aces",
    "Terminal Troops", "Merge Mavericks", "Branch Breakers", "Git Gurus",
    "Code Ninjas", "Debug Squad", "Stack Savages", "Binary Bandits",
    "Dev Storm", "Hack Squad", "Cloud Commanders", "Kernel Knights",
    "AI Squad", "Data Warriors", "Backend Bosses", "Frontend Ninjas",
    "Fullstack Squad", "Server Soldiers", "Cache Kings", "Script Ninjas",
    "Bug Squad", "Error Squad", "Logic Ninjas", "Syntax Soldiers",
    "Binary Soldiers", "Dev Legends", "Code Squad", "Hack Ninjas",
    "Deploy Squad", "Runtime Squad", "Compile Ninjas", "Script Kings",
    "Tech Squad", "Code Soldiers", "Bug Ninjas", "Stack Squad"
]

# 🎯 SOLO DEV NAMES
SOLO_NAMES = [
    "Lone Coder", "Solo Ninja", "Debug Monk", "Silent Hacker",
    "Code Wanderer", "Byte Hermit", "Logic Ranger", "Stack Samurai",
    "Bug Slayer", "Script Ghost", "Terminal Nomad", "Cyber Monk",
    "Code Sniper", "Binary Lonewolf", "Dev Phantom", "Hack Ranger",
    "AI Lonewolf", "Data Hermit", "Backend Ninja", "Frontend Solo",
    "Fullstack Lonewolf", "Server Ghost", "Cache Monk", "Script Ninja",
    "Bug Hunter", "Error Slayer", "Logic Ninja", "Syntax Monk",
    "Binary Ninja", "Dev Ranger"
]


# ✅ METHOD 1 → TEAM NAME
def get_random_team_name() -> str:
    return random.choice(TEAM_NAMES)


# ✅ METHOD 2 → SOLO NAME
def get_random_solo_name() -> str:
    return random.choice(SOLO_NAMES)


if __name__ == '__main__':
    asyncio.run(check_exist())
#     await  test()
