from storage import db
from user import User

async def mass_send(message, *args, **kwargs):
    for user_obj in db.users.find({}):
        user = User(user_obj)
        await user.send_message(
            message,
            *args,
            **kwargs
        )
        print(f'Sended to {user}')