from bs4 import BeautifulSoup
import requests

def get_files():
    home_url = 'https://github.com/Murali-group/PathLinker'
    git = 'https://github.com/'
    url_file = 'files.txt'
    req = requests.get(home_url)
    soup = BeautifulSoup(req.text, 'html.parser')
    with open(url_file, 'w+') as f:
        for link in soup.find_all('a'):
            url = link.get('href')
            if '.py' in url:
                # print(f"found {url}")
                scraper_req = requests.get(git+url)
                s = BeautifulSoup(scraper_req.text, 'html.parser')
                for link in s.find_all('a'):
                    t_url = link.get('href')
                    if '/raw/' in t_url:
                        f.write(git+t_url)
                        f.write('\n')

def main():
    get_files()

if __name__ == '__main__':
    main()