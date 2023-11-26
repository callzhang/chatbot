from html2text import HTML2Text
from bs4 import BeautifulSoup
import requests
from pprint import pprint
from apify_client import ApifyClient
from . import auth
from retry import retry
from newspaper import Article

apify_token = auth.get_apify_token()


# function calling
function_google_search = {
    "name": "google_search",
    "description": "Search inormation on Google",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The keywords string to search for information on the internet. Returns the search results in dictionary format. Please use the same language as the user input.",
            },
        },
        "required": ["query"],
    },
}

function_parse_web_content = {
    "name": "parse_web_content",
    "description": "Parse web content",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The url of the web page to parse. Returns the content of the website in markdown format.",
            },
            "title": {
                "type": "string",
                "description": "The title of the website wish to parse"
            }
        },
        "required": ["url"],
    },
}

@retry(tries=3)
def google_search(query):
    print(f'searching google: {query}')
    # Initialize the ApifyClient with your API token
    client = ApifyClient(apify_token)

    # Prepare the Actor input
    run_input = {
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": 10,
        "mobileResults": False,
        "languageCode": "",
        "maxConcurrency": 10,
        "saveHtml": False,
        "saveHtmlToKeyValueStore": False,
        "includeUnfilteredResults": False,
        "customDataFunction": """async ({ input, $, request, response, html }) => {
    return {
        pageTitle: $('title').text(),
    };
    };""",
    }

    # Run the Actor and wait for it to finish
    run = client.actor("nFJndFXA5zjCTuudP").call(run_input=run_input)

    # Fetch and print Actor results from the run's dataset (if there are any)
    parsed_results = []
    also_asks = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        '''{
            "title":"The 38 Essential Restaurants in New York City",
            "url":"https://ny.eater.com/maps/best-new-york-restaurants-38-map",
            "displayedUrl":"https://ny.eater.com › maps › best-new-york-restaurants-...",
            "description":"The 38 Essential Restaurants in New York City · Roberto's · Papaye · Sylvia's · Bánh Vietnamese Shop House · Gallaghers Steakhouse · Le Bernardin.",
            "date":"2023-10-10T12:00:00.000Z",
            "emphasizedKeywords":[
                "New York City"
            ],
            "siteLinks":[],
            "productInfo":{},
            "type":"organic",
            "position":2
        },'''
        organicResults = item['organicResults']
        for result in organicResults:
            parsed_results.append({k:v for k, v in result.items() if k in ['title', 'url', 'description']})
        
        
        '''{
            "question":"What food is New York City famous for?",
            "answer":"Keep ExploringNew York pizza slice. Out of all the foods associated with New York, perhaps none is more famous than pizza. ... New York cheesecake. ... New York–style hot dog. ... Nathan's Famous at Coney Island. ... Bagel with lox and cream cheese. ... Pastrami sandwich. ... Corned-beef sandwich. ... Matzo ball soup.More items...•",
            "url":"https://www.cityexperiences.com/blog/new-york-city-food/",
            "title":"21 Foods You'll Only Find in New York City",
            "date":"Jan 4, 2023"
        }'''
        peopleAlsoAsk = item['peopleAlsoAsk']
        for result in peopleAlsoAsk:
            parsed_results.append({k:v for k, v in result.items() if k in ['answer', 'question', 'url', 'title']})
            also_asks = [a['question'] for a in peopleAlsoAsk]
        
        # filter out no url
        parsed_results = [r for r in parsed_results if 'url' in r]
        return parsed_results, also_asks
    
@retry(tries=3)
def parse_web_content(url, title=None, safe=False):
    """
    This function converts HTML content to a readable format
    """
    print(f'parsing web content: {url}')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',  # Do Not Track Request Header
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    if safe:
        response = requests.get(url, timeout=30, headers=headers)
        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        main = soup.find('main')
        if main:
            soup = main
        html = soup.prettify()
    else:
        # use newspaper for better parsing
        article = Article(url, browser_user_agent=headers['User-Agent'], headers=headers, verbose=True)
        try:
            article.download()
        except:
            return parse_web_content(url, safe=True)
        html = article.html
        if len(html) < 100:
            return parse_web_content(url, safe=True)
        
    # Use html2text to convert the parsed HTML to plain text
    html2md = HTML2Text()
    html2md.ignore_links = True
    html2md.bypass_tables = False
    html2md.ignore_images = True
    html2md.ignore_emphasis = False
    readable_text = html2md.handle(html)
    
    # safe
    if not safe and len(readable_text) < 100:
        print(f'===> Unable to parse website, got content:\n {readable_text}, \n===>parse with safe method')
        return parse_web_content(url, safe=True)
    
    # synthesis
    web_content = f'[Title: {title}]\n\n{readable_text}'
    return web_content

#------------tools list-------------
tool_list = {
    'google_search': {
        'call': google_search,
        'function': function_google_search,
    },
    'parse_web_content': {
        'call': parse_web_content,
        'function': function_parse_web_content
    }
}

if __name__ == '__main__':
    res = google_search('北京的地道餐厅')
    pprint(res)
    print('-'*50)
    content = parse_web_content(res[4]['url'])
    pprint(content)
    with open('test/test.md', 'w') as f:
        f.write(content)
