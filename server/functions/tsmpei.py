from storage import db
from datetime import datetime
from .log import log
import httpx

def get_group_id(name):
    try:
        res = httpx.get(
            'http://ts.mpei.ru/api/search',
            params={
                'term': name,
                'type': 'group'
            }
        ).json()
    except Exception as e:
        log(f'Error TS Mpei: {e} (caused by get_group_id)')

    if len(res) == 1:
        print(res[0]['id'], res[0]['label'])
        return res[0]['id'], res[0]['label']
    else:
        print('AAA', None, None)
        return None, None

async def get_timetable_json(user, date_obj):
    if not user.group_id:
        return None

    lastdown = db.memory.find_one({
        'key': 'last_timeout_error'
    })

    if (datetime.now() - lastdown['value']).total_seconds() < 60:
        raise Exception('timeoutError')

    datestrf = date_obj.strftime('%Y.%m.%d')

    try:
        async with httpx.AsyncClient() as client:
            res = (
                await client.get(
                    f'http://ts.mpei.ru/api/schedule/group/{user.group_id}',
                    params={
                        'start': datestrf,
                        'finish': datestrf,
                        'lng': 1
                    }
                )
            ).json()
    except Exception as e:
        db.memory.update_one({
            'key': 'last_timeout_error'
        }, {
            '$set': {
                'value': datetime.now()
            }
        })
        raise e

    lessons = [
        {
            'name': lesson['discipline'],
            'type': lesson['kindOfWork'],
            'place': f"{lesson['auditorium']} ({lesson['building'] if 'building' in lesson else 'нет информации'})",
            'lecturer': lesson['lecturer'],
            'begin_lesson': date_obj.replace(
                hour=int(lesson['beginLesson'].split(':')[0]),
                minute=int(lesson['beginLesson'].split(':')[1])
            ),
           'end_lesson': date_obj.replace(
                hour=int(lesson['endLesson'].split(':')[0]),
                minute=int(lesson['endLesson'].split(':')[1])
            ),
            'group_id': user.group_id
        } for lesson in res
    ]

    # TODO: delete lessons this day from db
    # db.lessons.insert_many(lessons)

    # print(lessons)

    return lessons

