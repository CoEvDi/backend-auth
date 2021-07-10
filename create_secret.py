import secrets


with open('config.yaml', 'r') as conf:
    lines = conf.readlines()
    for i, line in enumerate(lines):
        if line.find('token_secret_key') != -1:
            lines[i] = f'    token_secret_key: {secrets.token_hex(32)}\n'
            break

with open('config.yaml', 'w') as conf:
    conf.writelines(lines)

print('Created and writed to config.yaml')
