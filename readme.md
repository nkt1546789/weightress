# Usage
Weightress assign weights to DOM elements such as texts and images.
Each weight represents the importance of the corresponding DOM element.
Since all of the DOM elements are weighted by weightress,
you can extract any elements with weights.
We shall show some examples as follows.

## Texts
You can obtain weighted text-node list like this:

```python
import weightress
ce = weightress.ContentExtractor().fit(html)
print "weighted texts (top 10):"
h = ce.get_weighted_texts()
for text, weight in sorted(h, key=lambda x:x[1], reverse=True)[:10]:
    print text, weight
```

## images
You can obtain weighted image src list like this:

```python
import weightress
ce = weightress.ContentExtractor().fit(html)
print "content images (in top 3 elements)"
for src, weight in ce.extract_images(topn=3):
	print src, weight
```

## bs4 Elements
You can obtain weighted DOM elements (bs4.Elemens) list this:

```python
import weightress
ce = weightress.ContentExtractor().fit(html)
print "bs4 elements (top 5):"
for elem, weight in ce.extract_elements(topn=5):
	print elem.name, elem.attrs, weight
print
```

## Top-1 text

```python
import weightress
ce = weightress.ContentExtractor().fit(html)
print "top-1 text:"
print ce.extract_text(deliminator=u"\n")
```
