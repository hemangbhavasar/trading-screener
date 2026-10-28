with open('C:/Users/bhava/Downloads/Trading/app.py') as f:
    for i,l in enumerate(f,1):
        if 50 < i < 75:
            print(f'{i}: {l.rstrip()}')
