from typing import Optional

import requests
from bs4 import BeautifulSoup


class MSFTLearnScrapper:
    """Relou."""

    def __init__(self, function: str):
        self.function = function
        json_data = requests.get(
            f"https://docs.microsoft.com/api/search?search={function}%20function&locale=en-us&scoringprofile=semantic-captions&facet=category&facet=products&$filter=category%20eq%20%27Documentation%27&$top=1&expandScope=true"
        ).json()

        url = json_data.get("results", None)[0].get("url", None)
        if url is None:
            return

        content = requests.get(url).content
        self.soup = BeautifulSoup(content, features="html.parser")

        # this is copy-pasta code from SO
        # https://stackoverflow.com/a/73757003
        # it grabs content of <p> in h2 titles and put it in a dict
        self.h2_titles = {}
        for p in self.soup.select('p'):
            if p.find_previous('h2'):
                if self.h2_titles.get(p.find_previous('h2').text) is None:
                    self.h2_titles[p.find_previous('h2').text] = []
            else:
                continue
            self.h2_titles[p.find_previous('h2').text].append(p.text)

    def get_description(self, check: bool = False) -> str:
        if check and self.get_syntax() is None:
            return ""
        else:
            return self.soup.find("h3").findNext().text

    def get_syntax(self) -> Optional[str]:
        h2s = self.soup.find_all("h2")
        for h2 in h2s:
            if h2.text == "Syntax":
                return h2.findNext().text

    def get_parameters(self) -> Optional[list]:
        return self.h2_titles.get('Parameters', None)

    def get_return_value(self) -> Optional[list]:
        return self.h2_titles.get('Return value', None)


if __name__ == '__main__':
    function_name = "CreateFileA"
    function = MSFTLearnScrapper(function_name)
    print("==== description ====")
    print(function.get_description())
    print("==== syntax ====")
    print(function.get_syntax())
    print("==== params ====")
    print(function.get_parameters())
    print("==== return value ====")
    print(function.get_return_value())
