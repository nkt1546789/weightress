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
# extract weighted texts
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
# extract images from topn elements and its confidences.
print "content images (in top 10 elements)"
for src, score in ce.extract_images(topn=3):
	print src, score
```

## bs4 Elements
You can obtain weighted DOM elements (bs4.Elemens) list this:

```python
import weightress
ce = weightress.ContentExtractor().fit(html)
# extract bs4's elements
print "bs4 elements (top 5):"
for elem, score in ce.extract_elements(topn=5):
	print elem.name, elem.attrs, score
print
```

## Top-1 text

```python
import weightress
ce = weightress.ContentExtractor().fit(html)
# extract content text (this is not robust, please use "weighted texts")
print "top-1 text:"
print ce.extract_text(deliminator=u"\n")
```
