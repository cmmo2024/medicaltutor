import os
print("Content-Type: text/plain\n")
print("Environment variables:")
for k,v in sorted(os.environ.items()):
    if 'EMAIL' in k or 'DB_' in k:
        print(f"{k}={v}")
