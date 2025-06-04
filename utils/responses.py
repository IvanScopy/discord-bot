from random import choice, randint
# Helper function to get responses
def get_response(user_input: str) -> str:
    lowerd: str = user_input.lower()

    if lowerd == '':
        return "Well, you're awfully silent...."
    elif 'hello' in lowerd:
        return 'Hi 👋'
    elif 'bye' in lowerd:
        return 'See you'
    elif 'ngu vcl' in lowerd:
        return 'mày ngu ý'
    elif 'ping' in lowerd:
        return 'Pong! 🏓'
    elif 'roll dice' in lowerd:
        return f'You rolled: {randint(1, 6)}'
    elif 'announce' in lowerd:
        return 'Thông báo !!!!!!!!!!'
    else:
        return choice(['I do not understand....', 'What are you talking about?', 'm nói cái gì vậy?'])