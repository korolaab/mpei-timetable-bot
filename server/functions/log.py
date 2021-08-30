from datetime import datetime

def log(text: str):
    timestamp = datetime.now().strftime('%d.%m %H:%M:%S')
    print(f'[{timestamp}] {text}')
    with open('logs', 'a') as file:
        file.write(
            f'[{timestamp}] {text}\n'
        )