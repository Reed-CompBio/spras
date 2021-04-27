# Tobias Rubel | rubelato@reed.edu
# Reed CompBio
#
# This is a mockup interface for PRANCER

import os
import sys
import curses
from curses import wrapper
from getpass import getpass
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def check_installed_algorithms():
    installed_algorithms = ['alg1','alg2']
    return installed_algorithms

def clear_screen():
    if os.name == 'nt': 
        os.system('cls') 
    else: 
        os.system('clear') 

def display_list(lat):
    d = dict(zip(range(len(lat)),lat))
    nlat = ['{}.    {}'.format(k,v) for k,v in d.items()]
    print('\n'.join(nlat))
    return None

def execute(conf):
    print('this would run the conf file if it was written')

def check_coherence(actions):
    print('checking coherence of course of action...')


def prepare_input():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    print("Okay first we need to figure out where all the data lives")
    print("Select where on your computer the interactome you want to use is:")
    interactome_loc = askopenfilename(title='Pick Interactome') 
    print('You picked: {}'.format(interactome_loc))
    print("Okay, and where are you storing the pathways?")
    pathway_loc = askopenfilename(title='Show me the pathways!') 
    print('You picked: {}'.format(pathway_loc))
    print("Brilliant. That's all the info we need.")
    return interactome_loc,pathway_loc

def gen_config():
    clear_screen()
    poss_actions = ['prepare-input','reconstruct','parse-output','augment','ensemble','parameter-advise','evaluate','visualize']
    print("Okay, let's generate a config file for an experiment together. This will only take a second.\n")
    conf_name = input('Before we get underway, what do you want to name this config file? (ex: ground-breaking-research)\n')
    conf_name = conf_name+'.yaml'
    clear_screen()
    print("Placing configuration {} into the Config-Files directory.".format(conf_name)) 
    print("Which of the following do you want to do? (Select all numbers which apply)")
    display_list(poss_actions)
    response = input()
    indexed_actions = [int(x) for x in list(response)]
    print(indexed_actions)
    chosen_actions = [poss_actions[i] for i in indexed_actions]
    clear_screen()
    print('You have selected to perform the following tasks:')
    display_list(chosen_actions)
    assent = getpass('Is that correct? (y/n)')
    if assent == 'n':
        gen_config()
    if assent == 'y':
        print('Groovy!')
        chosen_actions = check_coherence(chosen_actions)
        prepare_input()

def main():
    # Clear screen
    clear_screen()
    
    print('Searching for configuration files...')
    config_files = os.listdir('Config-Files')
    if config_files != []:
        clear_screen()
        print('The following config files were found:\n')
        display_list(config_files)
        #print('\n'.join(config_files))
        conf = getpass('Select the number of the config file to use, or press enter to continue\n')
        clear_screen()
        if conf != '':
            print('Proceeding with config file {}'.format(conf),)
            edit = getpass('Do you want to edit the config file? (y/n)')
            if edit == 'y':
                os.system('editor {}'.format(os.path.join('Config-Files',conf)))
            elif edit == 'n':
                print('proceeding...')
            execute(config_files[int(conf)])
        else:
            gen_config()



if __name__ == "__main__":
    main()
