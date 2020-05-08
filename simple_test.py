import string
import random
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))

f = open("input.file", "w")
data = id_generator(50000)
f.write(data)
f.close()