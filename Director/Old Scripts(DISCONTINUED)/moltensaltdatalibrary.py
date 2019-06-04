#main script to hold unto all features

import os
import subprocess

print('Greetings fellow nuclear enthusiast what are you interested in?')
print('(1) API: For working with data from the library this is probably the options you want.')
print('(2) Director: Need to change what is in the library it self, this is the option for you')
choice = input('So what will it be: ')
if choice == '1':
    print('API is currently being programmed right now, check back later this month')
elif choice == '2':
    print('Transfering to Director')
    os.chdir('Director')
    os.system('python director.py')
