import sec_parser as sp
from sec_downloader import Downloader

# Initialize the downloader with your company name and email
dl = Downloader("Stock Pitcher", "eli@stockpitcher.app")

# Download the latest 10-Q filing for Apple
html = dl.get_filing_html(ticker="FISI", form="10-Q")

def print_first_n_lines(text: str, *, n: int):
    print("\n".join(text.split("\n")[:n]), "...", sep="\n")


elements: list = sp.Edgar10QParser().parse(html)
print("elements", type(elements), len(elements), elements)

for element in elements:
    print(element)
#
demo_output: str = sp.render(elements)
print_first_n_lines(demo_output, n=7)
#
#
# tree = sp.TreeBuilder().build(elements)
#
# demo_output: str = sp.render(tree)
# print_first_n_lines(demo_output, n=7)
