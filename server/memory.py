from storage import db
from functions import log
from user import User # dont remove this, fix recursive import
from datetime import datetime

class Memory:
    def log(self, text):
        log(f'[Memory] {text}')

    def __init__(self):
        self.db = db
        self.users = {}

        db_res = db.memory.find_one({
            'key': 'last_update_id'
        })
        if db_res:
            self.last_update_id = db_res['value']
        else:
            self.last_update_id = 0
            db.memory.insert_one({
                'key': 'last_update_id',
                'value': 0
            })

    def set_last_update_id(self, update_id):
        self.last_update_id = update_id
        db.memory.update_one({
            'key': 'last_update_id'
        }, {
            '$set': {
                'value': update_id
            }
        })

    def get_user(self, chat):
        if chat['id'] not in self.users:
            if db.users.count_documents({
                'tid': int(chat['id'])
            }) == 0:
                user_object = {
                    'tid': int(chat['id']),
                    'balance': 0,
                    'message_id': 0,
                    'history_messages_id': [],
                    'group': None,
                    'group_id': None,
                    'settings': {
                        'lesson_notification_previously': {
                            'enabled': False,
                            'minutes': None
                        },
                        'lesson_notification_beginning': {
                            'enabled': False
                        }
                    },
                    'last_use': datetime.now()
                }
                for key in ['first_name', 'last_name', 'username', 'phone']:
                    if key in chat:
                        user_object[key] = chat[key]

                db.users.insert_one(user_object)
                user = User.from_tid(user_object['tid'])
            else:
                user = User.from_tid(chat['id'])
            self.users[chat['id']] = user
        else:
            user = self.users[chat['id']]

        if not user.first_name:
            updated_fields = {}
            for key in ['first_name', 'last_name', 'username', 'phone']:
                if key in chat:
                    updated_fields[key] = chat[key]
                    if key == 'first_name':
                        self.first_name = chat['first_name']
            db.users.update_one({
                '_id': user._id
            }, {
                '$set': updated_fields
            })

        self.log(f'<- {user}')
        return user