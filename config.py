API_TOKEN = '5153157850:AAHNPS6bMA8NPP-aMgaetq-X1NLjjJAjt6E'
# bot token from @BotFather
POSTGRES = "postgresql://uzqmubvfssuina:222eec260bedccf6942975fffe06ef7d86c9e378fe17381f75a7ebf96224dca7@ec2-52-86-56-90.compute-1.amazonaws.com:5432/d6t71h97rt2evu"
DB_FILE = "/db/digitalmarket.db"  # если хотим оставить возможность переключиться обратно на sqlite
SQLITE = f'sqlite://{DB_FILE}?check_same_thread=False'

LOCAL_DB = SQLITE
