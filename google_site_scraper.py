from googlesearch import search
results = search("Google BERT", stop=2)

for result in results:
    print(result)