import html2text
from bs4 import BeautifulSoup
import requests
from pprint import pprint
from apify_client import ApifyClient
from . import utils

apify_token = utils.get_apify_token()

def search_google(query):
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
        
        return parsed_results
    

def parse_web_content(url):
    """
    This function converts HTML content to a readable format
    """
    print(f'parsing web content: {url}')
    response = requests.get(url, timeout=30)
    html_content = response.text
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Use html2text to convert the parsed HTML to plain text
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = False
    text_maker.bypass_tables = False
    text_maker.ignore_images = True
    text_maker.ignore_emphasis = False
    readable_text = text_maker.handle(soup.prettify())
    
    return readable_text

if __name__ == '__main__':
    res = search_google('北京的地道餐厅')
    pprint(res)
    print('-'*50)
    content = parse_web_content(res[4]['url'])
    pprint(content)
    with open('test/test.md', 'w') as f:
        f.write(content)
